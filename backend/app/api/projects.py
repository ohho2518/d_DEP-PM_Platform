"""Project + intake routers: create, breakdown, confirm scope, scan (Blueprint §13)."""
from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.pm import breakdown_requirement
from app.constants import ActorType, ProjectType, TaskStatus
from app.db.session import get_db, get_session_factory
from app.integrations.ceo_client import CeoClient, get_ceo_client
from app.metadata.provider import get_metadata_provider
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.engine import planned_task_count
from app.orchestrator.state_machine import transition
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.scan import ScanResponse
from app.schemas.task import (
    BreakdownRequest,
    BreakdownResponse,
    ConfirmScopeRequest,
    Pagination,
    PlannedTask,
    TaskCreate,
    TaskList,
    TaskPlan,
    TaskRead,
)
from app.services import runs
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


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> Project:
    """รายละเอียดโปรเจกต์ — UI ใช้รู้ว่ามาจาก d_CEO ไหม (`ceo_task_id`)."""
    return _get_project_or_404(db, project_id)


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

    # Referential check (debt #5): ทุก id ใน depends_on ต้องเป็น task จริงในโปรเจกต์เดียวกัน
    # ไม่งั้น dangling id ทำให้ task ไม่มีวัน runnable (_deps_met fail-closed) แบบเงียบ ๆ
    if payload.depends_on:
        found = (
            db.execute(
                select(Task.id).where(
                    Task.project_id == project_id, Task.id.in_(payload.depends_on)
                )
            )
            .scalars()
            .all()
        )
        missing = set(payload.depends_on) - set(found)
        if missing:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"depends_on อ้าง task ที่ไม่มีในโปรเจกต์นี้: {sorted(str(m) for m in missing)}",
            )

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


@router.post("/{project_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_orchestrator(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    ceo_client: CeoClient | None = Depends(get_ceo_client),
) -> dict:
    """สั่งรัน Solo-Mode Orchestrator **เบื้องหลัง** แล้วตอบ 202 + `run_id` ทันที (Phase 2).

    ของจริงกินเวลาระดับหลายนาที (UAT: 6 tasks = 297 วิ) — ถามความคืบหน้าต่อที่
    ``GET /api/projects/{id}/run`` · ยิงซ้อนโปรเจกต์เดิมที่ยังรันอยู่ = **409**
    """
    _get_project_or_404(db, project_id)
    try:
        record = runs.start_run(
            project_id,
            session_factory=session_factory,
            ceo_client=ceo_client,
            total=planned_task_count(db, project_id),
        )
    except runs.RunAlreadyActive as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return record.snapshot()


@router.get("/{project_id}/run")
def get_run_progress(
    project_id: uuid.UUID,
    run_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """ความคืบหน้าของรอบรัน — ไม่ส่ง `run_id` = รอบล่าสุดของโปรเจกต์นี้.

    404 = โปรเจกต์นี้ยังไม่เคยรันในโปรเซสนี้ (ทะเบียนอยู่ในหน่วยความจำ — restart แล้วหาย
    แต่ผลงานจริงยังอยู่ในตาราง tasks)
    """
    _get_project_or_404(db, project_id)
    record = runs.get_run(run_id) if run_id else runs.latest_run_for_project(project_id)
    if record is None or record.project_id != str(project_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ไม่พบรอบรันของโปรเจกต์นี้")
    return record.snapshot()
