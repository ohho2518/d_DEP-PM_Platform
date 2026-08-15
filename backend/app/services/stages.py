"""เส้นทาง 6 ขั้นของโปรเจกต์ — **คำนวณจากของจริง ไม่มีใครมากดอัปเดตเอง**.

ทำไมไม่เก็บขั้นเป็นคอลัมน์: สถานะที่คนต้องมากดให้ตรงจะไม่ตรงเสมอ และเราเคยโดนบทเรียนนี้มาแล้ว
(รายงานว่า "เสร็จ" ทั้งที่ไม่มีชิ้นงาน — QC จับได้ 3 ส.ค.) · ที่นี่จึงอ่านจากหลักฐานที่ปลอมไม่ได้:
มีโฟลเดอร์จริงไหม · มี task ที่ยืนยัน scope แล้วไหม · งานเหลือกี่ใบ · เคย deploy สำเร็จหรือยัง

ชนิดงานต่างกัน เส้นทางต่างกัน (AGENTS.md — ผู้ใช้เลือกเอง ระบบเดาไม่ได้):

* ``code``  ครบ 6 ขั้น
* ``doc``   ข้ามขั้น "โครงสร้าง" · ขั้น 5 ชื่อ "ส่งมอบ" (ไม่ใช่ deploy)
* ``idea``  เดินแค่ 3 ขั้นแรก แล้วจบที่ปุ่ม "ยกระดับเป็นโปรเจกต์จริง"
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import DeploymentStatus, ProjectKind, ProjectStage, TaskStatus
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.task import Task

#: ขั้นที่เปิดใช้ต่อชนิดงาน — เรียงตามลำดับที่งานเดินจริง
STAGES_BY_KIND: dict[str, tuple[ProjectStage, ...]] = {
    ProjectKind.CODE.value: (
        ProjectStage.IDEA,
        ProjectStage.STRUCTURE,
        ProjectStage.PLAN,
        ProjectStage.BUILD,
        ProjectStage.SHIP,
        ProjectStage.MARKET,
    ),
    ProjectKind.DOC.value: (
        ProjectStage.IDEA,
        ProjectStage.PLAN,
        ProjectStage.BUILD,
        ProjectStage.SHIP,
        ProjectStage.MARKET,
    ),
    ProjectKind.IDEA.value: (
        ProjectStage.IDEA,
        ProjectStage.PLAN,
        ProjectStage.BUILD,
    ),
}

#: ชื่อขั้นที่คนอ่าน — ขั้นเดียวกันเรียกไม่เหมือนกันได้ตามชนิดงาน
_LABELS: dict[ProjectStage, str] = {
    ProjectStage.IDEA: "ไอเดีย",
    ProjectStage.STRUCTURE: "โครงสร้าง",
    ProjectStage.PLAN: "แผนงาน",
    ProjectStage.BUILD: "ลงมือ",
    ProjectStage.SHIP: "ส่งขึ้นระบบ",
    ProjectStage.MARKET: "การตลาด",
}
_LABEL_OVERRIDES: dict[tuple[str, ProjectStage], str] = {
    (ProjectKind.DOC.value, ProjectStage.SHIP): "ส่งมอบ",
    (ProjectKind.IDEA.value, ProjectStage.PLAN): "ตั้งคำถามที่ต้องหาคำตอบ",
    (ProjectKind.IDEA.value, ProjectStage.BUILD): "ศึกษาต่อ",
}

#: สถานะ task ที่ถือว่า "ยังไม่จบ" — ใช้ตัดสินว่าขั้นลงมือจบหรือยัง
_OPEN_STATUSES = (
    TaskStatus.BACKLOG.value,
    TaskStatus.PLANNED.value,
    TaskStatus.ASSIGNED.value,
    TaskStatus.IN_PROGRESS.value,
    TaskStatus.REVIEW.value,
)


def label_for(kind: str, stage: ProjectStage) -> str:
    return _LABEL_OVERRIDES.get((kind, stage), _LABELS[stage])


class _Facts:
    """หลักฐานที่ใช้ตัดสินขั้น — อ่านทีเดียวแล้วใช้ซ้ำ (ไม่ยิง query ต่อขั้น)."""

    def __init__(self, db: Session, project: Project) -> None:
        rows = db.execute(
            select(Task.status, func.count()).where(Task.project_id == project.id).group_by(Task.status)
        ).all()
        self.by_status: dict[str, int] = {status: count for status, count in rows}
        self.total_tasks = sum(self.by_status.values())
        self.open_tasks = sum(self.by_status.get(s, 0) for s in _OPEN_STATUSES)
        self.backlog_only = self.open_tasks and self.open_tasks == self.by_status.get(
            TaskStatus.BACKLOG.value, 0
        )
        self.done_tasks = self.by_status.get(TaskStatus.DONE.value, 0) + self.by_status.get(
            TaskStatus.DEPLOYED.value, 0
        )
        self.has_folder = bool(project.local_path)
        self.deploy_ok = bool(
            db.execute(
                select(Deployment.id)
                .where(
                    Deployment.project_id == project.id,
                    Deployment.status == DeploymentStatus.SUCCESS.value,
                )
                .limit(1)
            ).first()
        )


def _is_done(stage: ProjectStage, kind: str, f: _Facts) -> bool:
    """ขั้นนี้ผ่านไปแล้วหรือยัง — เกณฑ์ต้องเป็นสิ่งที่ **ปลอมไม่ได้**."""
    if stage is ProjectStage.IDEA:
        # มีโจทย์แล้ว = มีอะไรให้ทำต่อจริง ๆ (มี task หรือมีโฟลเดอร์)
        return f.total_tasks > 0 or f.has_folder
    if stage is ProjectStage.STRUCTURE:
        return f.has_folder
    if stage is ProjectStage.PLAN:
        # ยืนยัน scope แล้ว = มี task ที่พ้น backlog · ยังกอง backlog ล้วน = ยังไม่ผ่านขั้นนี้
        return f.total_tasks > 0 and not f.backlog_only
    if stage is ProjectStage.BUILD:
        return f.total_tasks > 0 and f.open_tasks == 0
    if stage is ProjectStage.SHIP:
        if kind == ProjectKind.DOC.value:
            # งานเอกสารไม่มี deploy — ถือว่าส่งมอบเมื่อไม่เหลืองานค้างและมีชิ้นงานจริง
            return f.total_tasks > 0 and f.open_tasks == 0 and f.done_tasks > 0
        return f.deploy_ok
    # การตลาด: ยังไม่มีอะไรรองรับจนกว่าจะต่อ d_MOS (ก้อนที่ 4) — จึงยังไม่ผ่านเสมอ
    return False


def _next_action(stage: ProjectStage | None, kind: str, f: _Facts) -> str:
    """ประโยคเดียวที่บอกว่า **ต้องทำอะไรต่อ** — ไม่มีขั้นค้าง = บอกว่าจบแล้ว."""
    if stage is None:
        return "จบครบทุกขั้นแล้ว"
    if stage is ProjectStage.IDEA:
        return "เล่าโจทย์หรือแนบไฟล์ แล้วให้ PM แตกงาน"
    if stage is ProjectStage.STRUCTURE:
        return "สร้างโฟลเดอร์จริงของโปรเจกต์ (ยังไม่เรียก AI)"
    if stage is ProjectStage.PLAN:
        if f.total_tasks == 0:
            return "ยังไม่มีงานในแผน — ให้ PM แตกงานจากโจทย์ก่อน"
        return f"ตรวจแผน {f.by_status.get(TaskStatus.BACKLOG.value, 0)} งานแล้วกดยืนยัน scope"
    if stage is ProjectStage.BUILD:
        return f"เหลืออีก {f.open_tasks} งาน — กด Run ให้ agent ทำต่อ"
    if stage is ProjectStage.SHIP:
        if kind == ProjectKind.IDEA.value:
            return "พร้อมแล้ว — ยกระดับเป็นโปรเจกต์จริง"
        if kind == ProjectKind.DOC.value:
            return "รวมไฟล์ผลงานแล้วส่งมอบ"
        return "commit แล้วส่งขึ้น staging"
    return "ยังไม่เปิดใช้ — ขั้นการตลาดต่อกับ d_MOS ในเฟสถัดไป"


def project_stages(db: Session, project: Project) -> dict:
    """สถานะเส้นทางของโปรเจกต์นี้ — ใช้ทั้งบนบอร์ดและหน้ารวม."""
    kind = project.kind or ProjectKind.CODE.value
    stages = STAGES_BY_KIND.get(kind, STAGES_BY_KIND[ProjectKind.CODE.value])
    facts = _Facts(db, project)

    items: list[dict] = []
    current: ProjectStage | None = None
    for stage in stages:
        done = _is_done(stage, kind, facts)
        if not done and current is None:
            current = stage
        items.append(
            {
                "stage": stage.value,
                "label": label_for(kind, stage),
                "state": "done" if done else ("current" if current is stage else "todo"),
            }
        )

    # ไอเดียที่เดินครบเส้นของตัวเองแล้ว = พร้อมยกระดับ (ปุ่มบนหน้าบอร์ด)
    ready_to_promote = kind == ProjectKind.IDEA.value and current is None

    return {
        "kind": kind,
        "current": current.value if current else None,
        "stages": items,
        "next_action": (
            "พร้อมยกระดับเป็นโปรเจกต์จริง" if ready_to_promote else _next_action(current, kind, facts)
        ),
        "ready_to_promote": ready_to_promote,
        "open_tasks": facts.open_tasks,
        "total_tasks": facts.total_tasks,
    }


def project_stages_by_id(db: Session, project_id: uuid.UUID) -> dict | None:
    project = db.get(Project, project_id)
    return None if project is None else project_stages(db, project)
