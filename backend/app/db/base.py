"""Declarative Base plus a small timestamp mixin shared by models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Timezone-aware UTC now (used as Python-side default)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Root declarative base for all ORM models."""


class TimestampMixin:
    """Adds ``created_at`` to a model. Models needing ``updated_at`` add it explicitly."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=utcnow, nullable=False
    )
