"""Task ORM model (Blueprint §4). Central entity driven by the State Machine (Sprint 2)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import Priority, TaskStatus
from app.db.base import Base, utcnow
from app.db.types import GUID, JSONType, new_uuid

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

    # Cumulative LLM token usage across every execute/review call of this task (debt #7).
    tokens_input: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    tokens_output: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # เดียวกันแต่ **แยกตามผู้ให้บริการ** — ราคาต่อโทเคนของแต่ละเจ้าไม่เท่ากัน เพดานก้อนเดียว
    # จึงคุมไม่อยู่เมื่อสลับเจ้า (§5 ของใบสั่งงาน 2026-08-06)
    #   {"anthropic": {"model": "claude-sonnet-5", "input": 1234, "output": 567, "calls": 3}}
    # 1 task มีได้หลายเจ้าจริง ๆ: Team Mode ให้ dev=openai แต่ reviewer=anthropic ในงานเดียวกัน
    # nullable เพราะ task ที่มีอยู่ก่อน 2026-08-14 แยกที่มาไม่ได้ — ต้องนับเป็น "ไม่ทราบเจ้า"
    # ไม่ใช่เดาว่าเป็นของ Anthropic (ADR-01: JSON ผ่าน JSONType เท่านั้น ห้าม JSONB เฉพาะ PG)
    token_usage: Mapped[dict | None] = mapped_column(JSONType, nullable=True, default=dict)

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

    project: Mapped[Project] = relationship(back_populates="tasks")
