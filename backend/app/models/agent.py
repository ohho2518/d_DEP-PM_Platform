"""Agent ORM model (Blueprint §4). Represents a human-or-AI worker identity."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import AgentMode, AgentProvider, AgentStatus
from app.db.base import Base, TimestampMixin
from app.db.types import GUID, new_uuid


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AgentProvider.ANTHROPIC.value
    )
    mode: Mapped[str] = mapped_column(String(10), nullable=False, default=AgentMode.SOLO.value)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=AgentStatus.IDLE.value)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
