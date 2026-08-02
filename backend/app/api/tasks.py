"""Task-level routers: PATCH task (State-Machine enforced), message history (Blueprint §13)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ActorType, TaskStatus
from app.db.session import get_db
from app.models.agent_message import AgentMessage
from app.models.deployment import Deployment
from app.models.task import Task
from app.orchestrator.state_machine import InvalidTransition, transition
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
    fields = payload.model_dump(exclude_unset=True)

    # Status change ต้องผ่าน State Machine เท่านั้น — ผิด transition → 409 (Sprint 2 DoD)
    new_status: TaskStatus | None = fields.pop("status", None)
    if new_status is not None and new_status.value != task.status:
        try:
            transition(db, task, new_status, actor_type=ActorType.HUMAN)
        except InvalidTransition as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    changes: dict = {}
    for field, value in fields.items():
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
    if changes or new_status is not None:
        db.commit()
        db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """ลบ task — ปฏิเสธ (409) ถ้ามี task อื่นใน depends_on อ้างถึง (debt #5: กัน dangling id)."""
    task = _get_task_or_404(db, task_id)

    # depends_on เป็น JSON array (portable — ADR-01) จึงเช็คฝั่ง Python ในสโคปโปรเจกต์เดียวกัน
    siblings = (
        db.execute(select(Task).where(Task.project_id == task.project_id, Task.id != task_id))
        .scalars()
        .all()
    )
    dependents = [t for t in siblings if str(task_id) in (t.depends_on or [])]
    if dependents:
        titles = ", ".join(f"'{t.title}'" for t in dependents[:5])
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"ลบไม่ได้ — มี {len(dependents)} task อ้างถึงใน depends_on: {titles}",
        )

    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="task.deleted",
        entity_type="task",
        entity_id=str(task.id),
        diff={"title": task.title, "status": task.status},
    )

    # SQLite dev ไม่ enforce FK ondelete — ทำ semantics ที่ประกาศไว้ใน models ให้ตรงเอง:
    # agent_messages.task_id = CASCADE, deployments.task_id = SET NULL
    for m in db.execute(
        select(AgentMessage).where(AgentMessage.task_id == task_id)
    ).scalars():
        db.delete(m)
    for d in db.execute(
        select(Deployment).where(Deployment.task_id == task_id)
    ).scalars():
        d.task_id = None

    db.delete(task)
    db.commit()


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
