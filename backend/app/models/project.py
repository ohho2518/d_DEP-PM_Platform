"""Project ORM model (Blueprint §4)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import ProjectStatus, ProjectType
from app.db.base import Base, TimestampMixin
from app.db.types import GUID, new_uuid

if TYPE_CHECKING:
    from app.models.task import Task


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default=ProjectType.NEW.value)
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProjectStatus.PLANNING.value
    )
    # Reference into the DEP Engine metadata registry — null until a real scan exists (ADR-02).
    metadata_registry_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # task ใน d_CEO ที่ถูก delegate ลงมาเป็นโปรเจกต์นี้ (Phase 1 — AGENTS.md §3.1).
    # null = โปรเจกต์ที่สร้างเองในระบบ | unique: 1 task ธุรกิจ = 1 project (ห้ามรับซ้ำ)
    ceo_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)
    # โฟลเดอร์จริงบนดิสก์ของโปรเจกต์นี้ (ADR-05) — ตั้งตอน bootstrap · null = ไม่มีโฟลเดอร์ผูกไว้
    # ใช้เป็น "รั้ว" ของทุกการเขียนไฟล์: ไฟล์ดีไซน์เข้า `_design_input/` และผลงานเขียนได้เฉพาะใต้นี้
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tasks: Mapped[list[Task]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
