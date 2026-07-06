"""Portable column types that work on both SQLite (dev) and PostgreSQL (prod) — ADR-01.

- ``GUID``  : store UUIDs as native ``UUID`` on PostgreSQL, as ``CHAR(36)`` on SQLite.
- ``JSONType``: SQLAlchemy generic ``JSON`` (maps to JSONB-compatible usage later).

Keeping these in one place means models never touch a dialect-specific type directly.
"""
from __future__ import annotations

import uuid

from sqlalchemy import CHAR, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator

# Generic JSON — SQLAlchemy renders JSONB on PostgreSQL and TEXT-backed JSON on SQLite.
JSONType = JSON


class GUID(TypeDecorator):
    """Platform-independent UUID.

    Uses PostgreSQL's UUID type when available, otherwise stores the 36-char string.
    Always hands Python ``uuid.UUID`` (or None) back to the caller.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def new_uuid() -> uuid.UUID:
    """Default factory for primary keys."""
    return uuid.uuid4()
