"""pytest fixtures: an isolated in-memory SQLite DB and a TestClient per test."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register tables
from app.db.base import Base
from app.db.session import get_db, get_session_factory
from app.main import app
from app.services import runs


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch):
    """บังคับ settings สะอาดทุก test — ห้ามให้ .env ของเครื่อง dev (ที่มี key จริง)
    ทำให้ suite ยิง API จริง/dispatch จริงโดยไม่ตั้งใจ.

    หมายเหตุ: ตั้ง env var เป็น "" ใช้ไม่ได้บน Windows (empty env var = ถูกลบ
    ตอน spawn process) — จึง monkeypatch ที่ Settings instance ตรง ๆ (พบจาก UAT จริง)
    """
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "agent_mode", "solo")
    monkeypatch.setattr(settings, "github_token", "")
    monkeypatch.setattr(settings, "github_repo", "")
    monkeypatch.setattr(settings, "auto_deploy_enabled", False)
    monkeypatch.setattr(settings, "deploy_callback_secret", "")
    # ปิดการเชื่อม d_CEO เป็นค่าเริ่มต้น — test ที่ต้องใช้ override dependency ด้วย stub เอง
    # (กันไม่ให้ suite เผลอยิงไปที่ Solo_CEO API ที่รันอยู่จริงบนเครื่อง dev)
    monkeypatch.setattr(settings, "ceo_api_base", "")
    yield


@pytest.fixture(autouse=True)
def _clean_run_registry():
    """ทะเบียนรอบรัน (Phase 2) เป็น singleton ต่อโปรเซส — ล้างทุก test ไม่ให้ค้างข้ามกัน."""
    runs.reset_runs()
    yield
    runs.reset_runs()


@pytest.fixture()
def db_factory():
    """โรงงาน session ผูกกับ schema ในหน่วยความจำชุดเดียวของ test นี้ (StaticPool = 1 connection).

    งานเบื้องหลังเปิด session ของตัวเอง จึงต้องแยกโรงงานออกมาจาก ``db_session``
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield TestingSession
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(db_factory):
    """Fresh in-memory schema per test (StaticPool keeps one shared connection)."""
    session = db_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session, db_factory):
    """TestClient whose get_db dependency is overridden to the in-memory session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    # งานเบื้องหลังต้องได้ session ใหม่ (ห้ามใช้ตัวเดียวกับ request) แต่ต้องเป็น schema เดียวกัน
    app.dependency_overrides[get_session_factory] = lambda: db_factory
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def wait_run(db_session):
    """รอรอบรันเบื้องหลังให้จบ แล้วล้าง cache ของ session ทดสอบให้เห็นสิ่งที่ thread เขียนจริง."""

    def _wait(run_id: str, timeout: float = 30.0):
        record = runs.wait_for_run(run_id, timeout=timeout)
        assert record is not None, f"ไม่พบรอบรัน {run_id}"
        assert record.finished_at is not None, f"รอบรัน {run_id} ไม่จบใน {timeout} วินาที"
        db_session.expire_all()
        return record

    return _wait
