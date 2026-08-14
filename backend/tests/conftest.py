"""pytest fixtures: an isolated DB (SQLite in-memory by default) + TestClient per test."""
from __future__ import annotations

import os

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
    # ลำดับผู้ให้บริการต้องกลับเป็นค่าปริยายทุก test — เทสต์ของหน้า Settings เขียนค่านี้จริง
    # ผ่าน API (ไม่ใช่ monkeypatch) ถ้าไม่ล็อกไว้จะรั่วข้ามไฟล์แล้วหาสาเหตุยาก
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "llm_fallbacks", "")
    # เพดานค่าใช้จ่าย (§5) ปิดเป็นค่าปริยาย — เครื่อง dev ที่ตั้งเพดานจริงไว้ต้องไม่ทำให้
    # เทสต์รอบรันหยุดกลางคัน · เทสต์ที่ต้องการเพดานตั้งเองใน test_usage_budget.py
    monkeypatch.setattr(settings, "llm_budget_usd", 0.0)
    monkeypatch.setattr(settings, "llm_budget_action", "warn")
    monkeypatch.setattr(settings, "github_token", "")
    monkeypatch.setattr(settings, "github_repo", "")
    monkeypatch.setattr(settings, "auto_deploy_enabled", False)
    monkeypatch.setattr(settings, "deploy_callback_secret", "")
    # ประตูหน้าบ้านปิดเป็นค่าปริยายในเทสต์ — พอเครื่อง dev ตั้ง API_TOKEN จริง เทสต์ทุกตัว
    # ที่ยิง /api/* จะกลายเป็น 401 ทันที (เจอจริงตอนตั้งค่าจริงครั้งแรก 2026-08-14)
    # เทสต์ที่ต้องการโหมดล็อกให้ตั้งเองใน test_api_auth.py
    monkeypatch.setattr(settings, "api_token", "")
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


#: ปริยาย = SQLite ในหน่วยความจำ (เร็ว ไม่ต้องมี service) · ตั้ง `TEST_DATABASE_URL`
#: ชี้ PostgreSQL เพื่อรันชุดเดียวกันบน engine จริง — DoD ของ ADR-01 (ดู runbook §4)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture()
def db_factory():
    """โรงงาน session ผูกกับ schema สะอาดชุดเดียวของ test นี้.

    งานเบื้องหลังเปิด session ของตัวเอง จึงต้องแยกโรงงานออกมาจาก ``db_session``
    · SQLite ใช้ StaticPool (1 connection ร่วมกันทั้ง test) · PostgreSQL ใช้ pool ปกติ
    → เธรดเบื้องหลังได้ connection ของตัวเองจริง ซึ่งใกล้เคียง production มากกว่า
    """
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL, future=True)

    # drop ตอนเริ่ม (ไม่ใช่ตอนจบ) — ตอนจบอาจมีเธรดเบื้องหลังค้าง lock อยู่แล้ว DROP ค้าง
    Base.metadata.drop_all(engine)
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
