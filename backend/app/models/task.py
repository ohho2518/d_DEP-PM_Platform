"""Task ORM model (Blueprint §4). Central entity driven by the State Machine (Sprint 2)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import Priority, TaskStatus
from app.db.base import Base, utcnow
from app.db.types import GUID, JSONType, new_uuid
from sqlalchemy import DateTime, func

if TYPE_CHECKING:
    from app.models.project import Project


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskStatus.BACKLOG.value, index=True
    )

    # Assignment — either a human or an agent; agent_role set the routing persona.
    assignee_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    assignee_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_role: Mapped[str | None] = mapped_column(String(30), nullable=True)

    priority: Mapped[str] = mapped_column(String(4), nullable=False, default=Priority.P2.value)

    # List of task UUIDs this task depends on. JSON array (ADR-01: never PG array type).
    depends_on: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)

    spec: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimate_points: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Escalation Rule support (Max Revision = 2).
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
