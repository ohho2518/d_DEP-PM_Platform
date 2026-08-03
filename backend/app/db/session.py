"""SQLAlchemy engine + session factory + FastAPI dependency."""
from __future__ import annotations

from collections.abc import Callable, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

# check_same_thread=False is required for SQLite under FastAPI's threadpool.
_connect_args = (
    {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped DB session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory() -> Callable[[], Session]:
    """FastAPI dependency: โรงงาน session สำหรับ **งานเบื้องหลัง** (Phase 2).

    งานที่รันหลังตอบ response แล้ว (orchestrator run) ใช้ session ของ request ไม่ได้
    เพราะ ``get_db`` ปิดมันไปพร้อม response — ต้องเปิดของตัวเอง 1 ตัวต่อ 1 รอบรัน
    เป็น dependency (ไม่ใช่ import ตรง) เพื่อให้ test override เป็น session ใน memory ได้
    """
    return SessionLocal
