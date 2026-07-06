"""Deployment ORM model (Blueprint §4, §12). Wired to the pipeline in Sprint 4."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import DeploymentStatus, DeploymentTrigger
from app.db.base import Base, TimestampMixin
from app.db.types import GUID, new_uuid


class Deployment(Base, TimestampMixin):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    triggered_by: Mapped[str] = mapped_column(
        String(10), nullable=False, default=DeploymentTrigger.MANUAL.value
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=DeploymentStatus.QUEUED.value
    )
    environment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
