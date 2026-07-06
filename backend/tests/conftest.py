"""pytest fixtures: an isolated in-memory SQLite DB and a TestClient per test."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401 — register tables
from app.main import app


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
    yield


@pytest.fixture()
def db_session():
    """Fresh in-memory schema per test (StaticPool keeps one shared connection)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """TestClient whose get_db dependency is overridden to the in-memory session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
