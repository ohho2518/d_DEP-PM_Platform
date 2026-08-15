"""Project request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import ProjectKind, ProjectStage, ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: ProjectType = ProjectType.NEW
    #: ชนิดงาน — ไม่ส่ง = `code` (พฤติกรรมเดิมของทุกโปรเจกต์ก่อน 2026-08-15)
    kind: ProjectKind = ProjectKind.CODE
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
    #: **ประมาณการ** จากราคาประกาศใน `.env` ไม่ใช่บิลจริงของบัญชีนี้ (ดู `services/usage.py`)
    cost_usd: float = 0.0


class UsageTotals(BaseModel):
    input: int = 0
    output: int = 0
    calls: int = 0


class BudgetStatus(BaseModel):
    """เพดานค่าใช้จ่ายต่อโปรเจกต์ (§5) — ตัวเลขเป็น **ประมาณการ** ทั้งหมด."""

    #: รวมค่าใช้จ่ายโดยประมาณของทุกเจ้า (USD) — คิดเฉพาะโทเคนที่รู้ว่าเจ้าไหนใช้
    spent_usd: float = 0.0
    #: 0 = ไม่ได้ตั้งเพดาน
    limit_usd: float = 0.0
    #: warn = เตือนอย่างเดียว · stop = รอบรันไม่เริ่ม task ใหม่
    action: str = "warn"
    over: bool = False
    #: True = มีโทเคนที่ระบุเจ้าไม่ได้ ⇒ ของจริงสูงกว่าตัวเลขนี้ (อย่าอ่านว่า "ใช้น้อย")
    excludes_untracked: bool = False


class ProjectUsage(BaseModel):
    """ถังสำหรับเพดานค่าใช้จ่ายต่อเจ้า (§5 ใบสั่งงาน 2026-08-06)."""

    project_id: str
    totals: UsageTotals
    by_provider: list[ProviderUsage]
    #: โทเคนที่นับรวมไว้แต่ระบุเจ้าไม่ได้ — งานที่ทำก่อน 2026-08-14 (ไม่ใช่ศูนย์แปลว่า "ไม่ได้ใช้")
    untracked: UsageTotals
    budget: BudgetStatus


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
    #: โฟลเดอร์จริงบนดิสก์ (ตั้งตอน bootstrap — ADR-05) · null = ไม่มีโฟลเดอร์ผูกไว้
    local_path: str | None = None
    #: ชนิดงาน — ตัดสินว่าเส้นทาง 6 ขั้นเปิดขั้นไหนบ้าง (code = ค่าเดิมของทุกโปรเจกต์ก่อน 15 ส.ค.)
    kind: ProjectKind = ProjectKind.CODE
    created_at: datetime


class StageItem(BaseModel):
    stage: ProjectStage
    #: ชื่อที่คนอ่าน — ขั้นเดียวกันเรียกต่างกันได้ตามชนิดงาน (doc: "ส่งมอบ" ไม่ใช่ "ส่งขึ้นระบบ")
    label: str
    #: done | current | todo
    state: str


class ProjectStages(BaseModel):
    """เส้นทางของโปรเจกต์หนึ่ง — **คำนวณจากของจริงทุกครั้งที่อ่าน** ไม่ได้เก็บในฐานข้อมูล."""

    kind: ProjectKind
    #: ขั้นที่กำลังอยู่ · null = เดินครบเส้นแล้ว
    current: ProjectStage | None
    stages: list[StageItem]
    #: ประโยคเดียวที่บอกว่าต้องทำอะไรต่อ
    next_action: str
    #: ไอเดียที่พร้อมยกระดับเป็นโปรเจกต์จริงแล้ว (โชว์ปุ่มบนบอร์ด)
    ready_to_promote: bool = False
    open_tasks: int = 0
    total_tasks: int = 0


class PromoteRequest(BaseModel):
    """ยกระดับไอเดีย → โปรเจกต์จริง (ไอเดียเท่านั้น)."""

    #: จะกลายเป็นงานชนิดไหน — ไอเดียยกระดับเป็นไอเดียอีกไม่ได้
    kind: Literal[ProjectKind.CODE, ProjectKind.DOC] = ProjectKind.CODE
    #: โฟลเดอร์ปลายทาง — ใส่แล้ว scaffold ให้เลย · ไม่ใส่ = ยกระดับเฉย ๆ ยังไม่สร้างโฟลเดอร์
    target: str = ""
    purpose: str = ""
    stack: str = ""
    is_python: bool = True
    relation: str = "general"


class PromoteResponse(BaseModel):
    project: ProjectRead
    #: โฟลเดอร์ที่สร้างให้ (ว่าง = ยกระดับอย่างเดียว ยังไม่ได้สร้างโฟลเดอร์)
    target: str = ""
    created: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)


class IdeaSource(BaseModel):
    name: str
    source_root: str
    files: list[str]
    is_folder: bool
    #: วันที่แก้ไขล่าสุดของไฟล์ต้นทาง (ISO date) — ว่างได้ถ้าอ่านไม่ได้
    updated: str = ""


class IdeaPreview(BaseModel):
    roots: list[str]
    found: int
    already_on_board: int
    #: เฉพาะที่ยังไม่อยู่บนบอร์ด
    items: list[IdeaSource]


class IdeaImportRequest(BaseModel):
    #: เลือกเฉพาะบางเรื่อง (ไม่ส่ง = เอาทั้งหมดที่ยังไม่มี)
    names: list[str] = Field(default_factory=list)


class BootstrapRequest(BaseModel):
    """เปิดโปรเจกต์ใหม่ "ของจริง" — สร้างโฟลเดอร์ + เอกสาร + git แล้วลงบอร์ดในคราวเดียว (ADR-05)."""

    name: str = Field(..., min_length=1, max_length=200)
    #: โฟลเดอร์ปลายทาง — ต้องอยู่ใต้ `SCAFFOLD_ALLOWED_ROOT` เท่านั้น
    target: str = Field(..., min_length=3)
    purpose: str = ""
    stack: str = ""
    is_python: bool = True
    #: general | product | service | middleware | eco-team | eco-core (ดู `services/scaffold.RELATION_LABELS`)
    relation: str = "general"
    team: str = ""
    dual_ps: bool = False


class DesignUploadResponse(BaseModel):
    """ผลการอัปโหลดไฟล์ดีไซน์ (ADR-05 S3)."""

    saved: list[str]
    #: ข้อความที่ประกอบจากไฟล์ทั้งหมด — เอาไปยิงต่อที่ `/breakdown` ได้เลย
    requirement: str
    requirement_chars: int


class DeliverableRequest(BaseModel):
    task_id: uuid.UUID
    #: path สัมพัทธ์ใต้โฟลเดอร์โปรเจกต์ เช่น `docs/PROJECT_OVERVIEW.md`
    path: str = Field(..., min_length=1, max_length=300)


class DeliverableResponse(BaseModel):
    path: str
    bytes: int
    #: ที่อยู่สำเนาไฟล์เดิม (null = ยังไม่เคยมีไฟล์นี้)
    backup: str | None
    task_id: str


class BootstrapResponse(BaseModel):
    project: ProjectRead
    target: str
    #: ไฟล์/โฟลเดอร์ที่ scaffold สร้างให้
    created: list[str]
    #: ขั้นตอนที่ทำจริง — ไว้โชว์ให้คนอ่านว่าเกิดอะไรขึ้นบ้าง (รวมคำเตือนถ้าวางผิดที่)
    steps: list[str]
    #: task แรกที่ตั้งให้บนบอร์ด (sign-off เอกสารก่อนเริ่มงาน)
    first_task_id: str
