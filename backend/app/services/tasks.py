"""Task persistence helpers, including materialising a PM Agent TaskPlan into rows."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.constants import ActorType, TaskStatus
from app.models.task import Task
from app.schemas.task import TaskPlan
from app.services.audit import record_audit


def persist_task_plan(
    db: Session, project_id: uuid.UUID, plan: TaskPlan, *, actor_id: str = "pm-agent"
) -> list[Task]:
    """Create backlog tasks from ``plan``, resolving ``ref`` dependencies to real UUIDs.

    Two passes: create every row first (so each ref has a UUID), then translate each task's
    ``depends_on`` refs into the corresponding UUIDs. Refs that don't resolve are dropped.
    """
    ref_to_id: dict[str, uuid.UUID] = {}
    created: list[Task] = []

    # Pass 1 — create rows without dependencies.
    for planned in plan.tasks:
        task = Task(
            project_id=project_id,
            title=planned.title,
            description=planned.description,
            status=TaskStatus.BACKLOG.value,
            priority=planned.priority.value,
            spec=planned.spec,
            estimate_points=planned.estimate_points,
            depends_on=[],
        )
        db.add(task)
        db.flush()  # assign PK without committing
        ref_to_id[planned.ref] = task.id
        created.append(task)

    # Pass 2 — resolve dependency refs to UUID strings (JSON array, ADR-01).
    for planned, task in zip(plan.tasks, created):
        resolved = [str(ref_to_id[ref]) for ref in planned.depends_on if ref in ref_to_id]
        task.depends_on = resolved

    record_audit(
        db,
        actor_type=ActorType.AGENT,
        actor_id=actor_id,
        action="task_plan.created",
        entity_type="project",
        entity_id=str(project_id),
        diff={"task_count": len(created)},
    )
    db.commit()
    for task in created:
        db.refresh(task)
    return created
