"""Project request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: ProjectType = ProjectType.NEW
    repo_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _existing_requires_repo(self) -> ProjectCreate:
        # An 'existing' (Brownfield) project needs a repo to scan (even if scan is a stub).
        if self.type == ProjectType.EXISTING and not self.repo_url:
            raise ValueError("repo_url is required when type='existing'")
        return self


class ProviderUsage(BaseModel):
    """โทเคนที่ผู้ให้บริการเจ้าหนึ่งใช้ไปในโปรเจกต์นี้."""

    provider: str
    model: str = ""
    input: int = 0
    output: int = 0
    calls: int = 0
    tasks: int = 0


class UsageTotals(BaseModel):
    input: int = 0
    output: int = 0
    calls: int = 0


class ProjectUsage(BaseModel):
    """ถังสำหรับเพดานค่าใช้จ่ายต่อเจ้า (§5 ใบสั่งงาน 2026-08-06) — ยังไม่แปลงเป็นเงิน."""

    project_id: str
    totals: UsageTotals
    by_provider: list[ProviderUsage]
    #: โทเคนที่นับรวมไว้แต่ระบุเจ้าไม่ได้ — งานที่ทำก่อน 2026-08-14 (ไม่ใช่ศูนย์แปลว่า "ไม่ได้ใช้")
    untracked: UsageTotals


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: ProjectType
    repo_url: str | None
    status: ProjectStatus
    metadata_registry_ref: str | None
    # task ใน d_CEO ที่ถูก delegate ลงมาเป็นโปรเจกต์นี้ (null = สร้างเองในระบบ)
    ceo_task_id: str | None = None
    created_at: datetime
