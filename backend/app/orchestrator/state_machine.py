"""Task State Machine (Blueprint §5).

Single source of truth for allowed status transitions. Every transition goes through
:func:`transition`, which validates the move and writes an audit_log row — no code path
may set ``task.status`` directly.

    Backlog → Planned → Assigned → InProgress → Review → Done → Deployed
                                       ↑           │
                                       └─ Revision ┘  (Review fail ครบ MAX_REVISIONS → Escalated)
    Escalated → InProgress  (คน/Senior Agent รับช่วงต่อ)
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
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW},
    TaskStatus.REVIEW: {TaskStatus.DONE, TaskStatus.IN_PROGRESS, TaskStatus.ESCALATED},
    TaskStatus.DONE: {TaskStatus.DEPLOYED},
    TaskStatus.ESCALATED: {TaskStatus.IN_PROGRESS},
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
