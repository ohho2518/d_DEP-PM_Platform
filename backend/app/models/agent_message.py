"""AgentMessage ORM model (Blueprint §4, §10).

Every inter-agent communication is persisted here — this table is the auditable source
of truth for the Message Bus regardless of transport (ADR-03).
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import GUID, JSONType, new_uuid


class AgentMessage(Base, TimestampMixin):
    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True
    )
    from_agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_agent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
