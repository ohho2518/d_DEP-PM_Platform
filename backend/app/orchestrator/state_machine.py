"""Task State Machine (Blueprint §5).

Single source of truth for allowed status transitions. Every transition goes through
:func:`transition`, which validates the move and writes an audit_log row — no code path
may set ``task.status`` directly.

    Backlog → Planned → Assigned → InProgress → Review → Done → Deployed
                                       ↑           │
                                       └─ Revision ┘  (Review fail ครบ MAX_REVISIONS → Escalated)
    Escalated → InProgress  (คน/Senior Agent ลงมือทำต่อเอง)
    Escalated → Planned     (ตีกลับเข้าคิวให้ agent ลองใหม่ — ใช้เมื่อแก้ "เหตุ" แล้ว)
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ActorType, TaskStatus
from app.models.task import Task
from app.services.audit import record_audit

# Adjacency map: current status -> statuses reachable in one step.
ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.BACKLOG: {TaskStatus.PLANNED},
    TaskStatus.PLANNED: {TaskStatus.ASSIGNED},
    TaskStatus.ASSIGNED: {TaskStatus.IN_PROGRESS},
    # in_progress → escalated = เครื่องมือใช้ไม่ได้กลางคัน (ผู้ให้บริการ AI ล่มทุกเจ้า, 2026-08-14)
    # ไม่ใช่ "งานไม่ผ่าน" — แต่ปล่อยค้าง `in_progress` แล้วต้องมาแก้มือทีหลังยิ่งแย่กว่า
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.ESCALATED},
    TaskStatus.REVIEW: {TaskStatus.DONE, TaskStatus.IN_PROGRESS, TaskStatus.ESCALATED},
    TaskStatus.DONE: {TaskStatus.DEPLOYED},
    # escalated → planned = "ตีกลับเข้าคิว" ให้ orchestrator หยิบไปทำใหม่ (engine หยิบเฉพาะ
    # planned) · ใช้เมื่อแก้เหตุที่ทำให้ตันแล้ว เช่น 2026-08-03 แก้เรื่อง agent ไม่ได้รับผลงาน
    # ของงานก่อนหน้า — ไม่งั้นงานที่ escalate ไปแล้วต้องให้คนทำเองอย่างเดียวตลอดไป
    # ⚠️ `revision_count` **ไม่ถูกรีเซ็ต** โดยตั้งใจ: ตีกลับแล้วยังไม่ผ่านจะ escalate ทันที
    # รอบเดียว ไม่วนจ่ายค่า LLM ซ้ำ ๆ (ต้องรีเซ็ตเองถ้าจงใจให้ลองใหม่เต็มโควตา)
    TaskStatus.ESCALATED: {TaskStatus.IN_PROGRESS, TaskStatus.PLANNED},
    TaskStatus.DEPLOYED: set(),
}


class InvalidTransition(Exception):
    """Raised when a status move is not allowed by the State Machine (API maps to 409)."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"invalid transition: {current} -> {target}")


def can_transition(current: str, target: str) -> bool:
    try:
        return TaskStatus(target) in ALLOWED_TRANSITIONS[TaskStatus(current)]
    except (ValueError, KeyError):
        return False


def transition(
    db: Session,
    task: Task,
    target: TaskStatus,
    *,
    actor_type: ActorType,
    actor_id: str | None = None,
    reason: str | None = None,
) -> Task:
    """Move ``task`` to ``target`` if allowed; always records an audit entry.

    Does not commit — the caller owns the transaction (engine batches several
    transitions per task; the API commits per request).
    """
    if not can_transition(task.status, target.value):
        raise InvalidTransition(task.status, target.value)

    previous = task.status
    task.status = target.value
    record_audit(
        db,
        actor_type=actor_type,
        actor_id=actor_id,
        action="task.transition",
        entity_type="task",
        entity_id=str(task.id),
        diff={"status": {"from": previous, "to": target.value}, "reason": reason},
    )
    return task
