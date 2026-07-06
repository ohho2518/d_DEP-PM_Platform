"""Task-level routers: PATCH task, message history (Blueprint §13).

Full State Machine validation lands in Sprint 2; Sprint 1 does a permissive PATCH plus an
audit record so the flow is testable end-to-end.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ActorType
from app.db.session import get_db
from app.models.agent_message import AgentMessage
from app.models.task import Task
from app.schemas.task import TaskRead, TaskUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_task_or_404(db: Session, task_id: uuid.UUID) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: uuid.UUID, payload: TaskUpdate, db: Session = Depends(get_db)
) -> Task:
    task = _get_task_or_404(db, task_id)
    changes: dict = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        current = getattr(task, field)
        # Enum-typed payload values -> their string value for the ORM column.
        new_value = value.value if hasattr(value, "value") else value
        if current != new_value:
            changes[field] = {"from": current, "to": new_value}
            setattr(task, field, new_value)

    if changes:
        record_audit(
            db,
            actor_type=ActorType.HUMAN,
            action="task.updated",
            entity_type="task",
            entity_id=str(task.id),
            diff=changes,
        )
        db.commit()
        db.refresh(task)
    return task


@router.get("/{task_id}/messages")
def list_task_messages(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Inter-Agent Communication history for a task (populated by the Message Bus in Sprint 2)."""
    _get_task_or_404(db, task_id)
    rows = (
        db.execute(
            select(AgentMessage)
            .where(AgentMessage.task_id == task_id)
            .order_by(AgentMessage.created_at)
        )
        .scalars()
        .all()
    )
    return {
        "data": [
            {
                "id": str(m.id),
                "from_agent_id": m.from_agent_id,
                "to_agent_id": m.to_agent_id,
                "message_type": m.message_type,
                "payload": m.payload,
                "created_at": m.created_at.isoformat(),
            }
            for m in rows
        ]
    }
