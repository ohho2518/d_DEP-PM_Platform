"""Project + intake routers: create, breakdown, confirm scope, scan (Blueprint §13)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.pm import breakdown_requirement
from app.constants import ActorType, ProjectType, TaskStatus
from app.db.session import get_db
from app.metadata.provider import get_metadata_provider
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.scan import ScanResponse
from app.schemas.task import (
    BreakdownRequest,
    BreakdownResponse,
    ConfirmScopeRequest,
    PlannedTask,
    TaskCreate,
    TaskList,
    TaskPlan,
    TaskRead,
    Pagination,
)
from app.orchestrator.engine import run_project
from app.orchestrator.state_machine import transition
from app.services.audit import record_audit
from app.services.tasks import persist_task_plan

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(
        name=payload.name,
        type=payload.type.value,
        repo_url=payload.repo_url,
    )
    db.add(project)
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.created",
        entity_type="project",
        entity_id=None,  # id assigned on flush below
        diff={"name": payload.name, "type": payload.type.value},
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/tasks", response_model=TaskList)
def list_tasks(
    project_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> TaskList:
    _get_project_or_404(db, project_id)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    base = select(Task).where(Task.project_id == project_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(Task.created_at).limit(limit).offset(offset)).scalars().all()
    )
    return TaskList(
        data=[TaskRead.model_validate(t) for t in rows],
        pagination=Pagination(total=total, limit=limit, offset=offset),
    )


@router.post(
    "/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED
)
def create_task(
    project_id: uuid.UUID, payload: TaskCreate, db: Session = Depends(get_db)
) -> Task:
    _get_project_or_404(db, project_id)
    task = Task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=TaskStatus.BACKLOG.value,
        priority=payload.priority.value,
        depends_on=[str(d) for d in payload.depends_on],
        spec=payload.spec,
        estimate_points=payload.estimate_points,
    )
    db.add(task)
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="task.created",
        entity_type="task",
        entity_id=None,
        diff={"title": payload.title},
    )
    db.commit()
    db.refresh(task)
    return task


@router.post("/{project_id}/breakdown", response_model=BreakdownResponse)
def breakdown(
    project_id: uuid.UUID, payload: BreakdownRequest, db: Session = Depends(get_db)
) -> BreakdownResponse:
    """PM Agent breaks a requirement into backlog tasks (New Project Onboarding, Blueprint §6)."""
    _get_project_or_404(db, project_id)
    result = breakdown_requirement(payload.requirement)
    created = persist_task_plan(db, project_id, result.plan)
    return BreakdownResponse(
        source=result.source,
        tasks=[TaskRead.model_validate(t) for t in created],
    )


@router.post("/{project_id}/confirm", response_model=TaskList)
def confirm_scope(
    project_id: uuid.UUID, payload: ConfirmScopeRequest, db: Session = Depends(get_db)
) -> TaskList:
    """Confirm backlog tasks -> planned (STEP 4 of onboarding). Empty list = all backlog."""
    _get_project_or_404(db, project_id)
    stmt = select(Task).where(
        Task.project_id == project_id, Task.status == TaskStatus.BACKLOG.value
    )
    if payload.task_ids:
        stmt = stmt.where(Task.id.in_(payload.task_ids))
    tasks = db.execute(stmt).scalars().all()
    for task in tasks:
        # ผ่าน State Machine เสมอ (backlog -> planned) — audit ถูกเขียนใน transition()
        transition(
            db, task, TaskStatus.PLANNED, actor_type=ActorType.HUMAN, reason="scope confirmed"
        )
    db.commit()
    return TaskList(
        data=[TaskRead.model_validate(t) for t in tasks],
        pagination=Pagination(total=len(tasks), limit=len(tasks), offset=0),
    )


@router.post("/{project_id}/scan", response_model=ScanResponse)
async def scan_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ScanResponse:
    """Run a metadata scan (Brownfield). Sprint 1 answers from the Stub provider (ADR-02)."""
    project = _get_project_or_404(db, project_id)
    if project.type != ProjectType.EXISTING.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "scan is only valid for type='existing' projects"
        )

    provider = get_metadata_provider()
    report = await provider.baseline_report(str(project_id), project.repo_url)

    # Convert findings into backlog tasks so they show up on the board (Blueprint §7).
    plan = TaskPlan(
        tasks=[
            PlannedTask(
                ref=f"S{i + 1}",
                title=f.title,
                description=f.detail,
                priority=f.suggested_priority,
                depends_on=[],
                spec=f"[{f.category}] confidence={f.confidence}",
            )
            for i, f in enumerate(report.findings)
        ]
    )
    created = persist_task_plan(db, project_id, plan, actor_id="stub-metadata")
    return ScanResponse(report=report, created_task_ids=[str(t.id) for t in created])


@router.post("/{project_id}/run")
def run_orchestrator(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """รัน Solo-Mode Orchestrator กับ task ที่ planned ทั้งหมดของโปรเจกต์ (synchronous ใน MVP)."""
    _get_project_or_404(db, project_id)
    summary = run_project(db, project_id)
    return {
        "project_id": summary.project_id,
        "processed": len(summary.outcomes),
        "counts": summary.counts,
        "outcomes": [
            {
                "task_id": o.task_id,
                "title": o.title,
                "final_status": o.final_status,
                "revisions": o.revisions,
            }
            for o in summary.outcomes
        ],
    }
