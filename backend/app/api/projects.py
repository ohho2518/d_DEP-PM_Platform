"""Project + intake routers: create, breakdown, confirm scope, scan (Blueprint §13)."""
from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.pm import breakdown_requirement
from app.constants import (
    ActorType,
    Priority,
    ProjectKind,
    ProjectType,
    RunStatus,
    TaskStatus,
)
from app.db.session import get_db, get_session_factory
from app.integrations.ceo_client import CeoClient, get_ceo_client
from app.metadata.provider import get_metadata_provider
from app.models.agent_message import AgentMessage
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.engine import planned_task_count
from app.orchestrator.state_machine import transition
from app.schemas.project import (
    BootstrapRequest,
    BootstrapResponse,
    DeliverableRequest,
    DeliverableResponse,
    DesignUploadResponse,
    IdeaImportRequest,
    IdeaPreview,
    ProjectCreate,
    ProjectRead,
    ProjectStages,
    ProjectUsage,
    PromoteRequest,
    PromoteResponse,
)
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
from app.services import deliverables, design_files, ideas, runs, scaffold, stages, usage
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
        kind=payload.kind.value,
    )
    db.add(project)
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.created",
        entity_type="project",
        entity_id=None,  # id assigned on flush below
        diff={"name": payload.name, "type": payload.type.value, "kind": payload.kind.value},
    )
    db.commit()
    db.refresh(project)
    return project


#: ⚠️ เส้นทางที่ขึ้นต้นด้วยคำตายตัว **ต้องประกาศก่อน** `/{project_id}` เสมอ
#: ไม่งั้น FastAPI จะจับ "ideas" เป็น project_id แล้วตอบ 422 (จับคู่ตามลำดับที่ประกาศ)
@router.get("/ideas/preview", response_model=IdeaPreview)
def preview_ideas(db: Session = Depends(get_db)) -> dict:
    """ไอเดียที่กองอยู่ในดิสก์ — ดูก่อนว่าจะดึงอะไรเข้ามาบ้าง (ยังไม่เขียนอะไรทั้งสิ้น)."""
    return ideas.preview(db)


@router.post("/ideas/import", response_model=list[ProjectRead], status_code=status.HTTP_201_CREATED)
def import_ideas(payload: IdeaImportRequest, db: Session = Depends(get_db)) -> list[Project]:
    """ดึงไอเดียเก่าขึ้นบอร์ดเป็นโปรเจกต์ชนิด `idea` — **ยิงซ้ำได้ ของเดิมถูกข้าม**.

    ไฟล์ต้นทางไม่ถูกย้าย/แก้/ลบ · ไอเดียที่เป็นไฟล์เดี่ยวจะไม่มี `local_path`
    (ผูกโฟลเดอร์รวมไว้ = เปิดสิทธิ์เขียนทับของคนอื่น — รั้วของ ADR-05 ต้องแคบ)
    """
    created = ideas.import_ideas(db, names=payload.names or None)
    for project in created:
        record_audit(
            db,
            actor_type=ActorType.HUMAN,
            action="project.idea_imported",
            entity_type="project",
            entity_id=str(project.id),
            diff={"name": project.name, "local_path": project.local_path},
        )
    db.commit()
    for project in created:
        db.refresh(project)
    return created


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> Project:
    """รายละเอียดโปรเจกต์ — UI ใช้รู้ว่ามาจาก d_CEO ไหม (`ceo_task_id`)."""
    return _get_project_or_404(db, project_id)


@router.get("/{project_id}/stages", response_model=ProjectStages)
def get_project_stages(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """เส้นทาง 6 ขั้นของโปรเจกต์นี้ — **คำนวณสด** จากโฟลเดอร์/task/deployment ที่มีอยู่จริง."""
    project = _get_project_or_404(db, project_id)
    return stages.project_stages(db, project)


@router.post("/{project_id}/promote", response_model=PromoteResponse)
def promote_project(
    project_id: uuid.UUID, payload: PromoteRequest, db: Session = Depends(get_db)
) -> dict:
    """ยกระดับไอเดีย → โปรเจกต์จริง โดย**เก็บงานที่ศึกษาไว้แล้วทั้งหมด**.

    ใส่ `target` = สร้างโฟลเดอร์จริงให้ในคราวเดียว (เหมือน `/bootstrap`) ·
    ไม่ใส่ = เปลี่ยนชนิดงานอย่างเดียว ค่อยไปสร้างโฟลเดอร์ทีหลังได้
    """
    project = _get_project_or_404(db, project_id)
    if project.kind != ProjectKind.IDEA.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"ยกระดับได้เฉพาะโปรเจกต์ชนิดไอเดีย — ตัวนี้เป็น '{project.kind}' อยู่แล้ว",
        )

    result: dict = {"target": "", "created": [], "steps": []}
    if payload.target.strip():
        try:
            manifest = scaffold.scaffold(
                payload.target,
                project.name,
                purpose=payload.purpose,
                stack=payload.stack,
                is_python=payload.is_python,
                relation=payload.relation,
            )
        except scaffold.ScaffoldError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        project.local_path = manifest["target"]
        result = {
            "target": manifest["target"],
            "created": manifest["created"],
            "steps": manifest["steps"],
        }

    was = project.kind
    project.kind = payload.kind.value
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.promoted",
        entity_type="project",
        entity_id=str(project.id),
        diff={"kind": {"from": was, "to": project.kind}, "target": result["target"]},
    )
    db.commit()
    db.refresh(project)
    return {"project": project, **result}


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_project(payload: BootstrapRequest, db: Session = Depends(get_db)) -> dict:
    """เปิดโปรเจกต์ใหม่ **ของจริง**: โฟลเดอร์ + เอกสารกำกับ + git init แล้วลงบอร์ดในคราวเดียว.

    ยกมาจาก `new-project-studio` ตาม ADR-05 — ส่วนนี้เป็น deterministic ล้วน **ไม่เรียก AI**
    (ตรงกับหลัก "AI ล่ม ระบบไม่ล่ม") · การเติมเอกสารจากไฟล์ดีไซน์เป็นงานบนบอร์ดคนละขั้น

    ลำดับตั้งใจ: **scaffold ก่อน แล้วค่อยลงบอร์ด** — ถ้าสร้างโฟลเดอร์ไม่ได้จะได้ไม่มี
    project ค้างในระบบที่ไม่มีของจริงรองรับ · ไม่ auto-commit git (คนต้องตรวจก่อนเสมอ)
    """
    try:
        manifest = scaffold.scaffold(
            payload.target,
            payload.name,
            purpose=payload.purpose,
            stack=payload.stack,
            is_python=payload.is_python,
            relation=payload.relation,
            team=payload.team,
            dual_ps=payload.dual_ps,
        )
    except scaffold.ScaffoldError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    project = Project(
        name=payload.name, type=ProjectType.NEW.value, local_path=manifest["target"]
    )
    db.add(project)
    db.flush()

    description = f"โปรเจกต์อยู่ที่: {manifest['target']}"
    if payload.purpose:
        description += f"\nPurpose: {payload.purpose}"
    description += "\nปิด checklist ใน docs/REVIEW_CHECKLIST.md ก่อนเริ่ม Sprint 1"
    task = Task(
        project_id=project.id,
        title="Sign-off เอกสารกำกับก่อนเริ่มงาน",
        description=description,
        status=TaskStatus.BACKLOG.value,
        priority=Priority.P1.value,
        depends_on=[],
    )
    db.add(task)
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.bootstrapped",
        entity_type="project",
        entity_id=None,
        diff={"name": payload.name, "target": manifest["target"], "relation": payload.relation},
    )
    db.commit()
    db.refresh(project)
    db.refresh(task)

    return {
        "project": project,
        "target": manifest["target"],
        "created": manifest["created"],
        "steps": manifest["steps"],
        "first_task_id": str(task.id),
    }


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_project(
    project_id: uuid.UUID, unlink_ceo: bool = False, db: Session = Depends(get_db)
) -> None:
    """ลบโปรเจกต์พร้อมของทั้งหมดที่ห้อยอยู่ — ใช้ล้างงานทดสอบออกจากบอร์ด.

    🔴 **ลบแล้วไม่มีทางกู้จาก API** (ผลงาน agent ทั้งหมดของโปรเจกต์นั้นหายไปด้วย) —
    สำรอง `backend/dep_pm.db` ก่อนเสมอตาม WORKING_RULES Rule 3

    ปฏิเสธ (409) โปรเจกต์ที่ผูกกับงานของ d_CEO เพราะฝั่งโน้นยังอ้าง `ceo_task_id` อยู่ ·
    ตั้งใจจะลบจริง ๆ ให้ส่ง `?unlink_ceo=true` — **เจตนาต้องเขียนออกมา** ไม่ใช่ลบผ่านไปเงียบ ๆ
    (ใช้ตอนงานฝั่งเลขาปิดแล้วและไม่ต้องเก็บของทดสอบไว้)
    """
    project = _get_project_or_404(db, project_id)
    if project.ceo_task_id and unlink_ceo:
        record_audit(
            db,
            actor_type=ActorType.HUMAN,
            action="project.ceo_link_removed",
            entity_type="project",
            entity_id=str(project.id),
            diff={"ceo_task_id": project.ceo_task_id, "reason": "ลบโปรเจกต์ทดสอบ"},
        )
        project.ceo_task_id = None
    if project.ceo_task_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"ลบไม่ได้ — โปรเจกต์นี้รับงานมาจาก d_CEO (task {project.ceo_task_id}) "
            "ให้ล้าง ceo_task_id ก่อนถ้าตั้งใจลบจริง",
        )

    tasks = db.execute(select(Task).where(Task.project_id == project_id)).scalars().all()
    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.deleted",
        entity_type="project",
        entity_id=str(project.id),
        diff={"name": project.name, "tasks": len(tasks)},
    )

    # SQLite dev ไม่ enforce FK ondelete — ทำ semantics ที่ประกาศไว้ใน models ให้ตรงเอง
    # (เหมือน delete_task): messages CASCADE, deployments SET NULL แล้วค่อยลบตัวโปรเจกต์
    for message in db.execute(
        select(AgentMessage).where(AgentMessage.project_id == project_id)
    ).scalars():
        db.delete(message)
    for deployment in db.execute(
        select(Deployment).where(Deployment.project_id == project_id)
    ).scalars():
        db.delete(deployment)
    for task in tasks:
        db.delete(task)
    db.delete(project)
    db.commit()


def _project_dir_or_400(project: Project) -> Path:
    """โฟลเดอร์จริงของโปรเจกต์ — ทุกการเขียนไฟล์ต้องผ่านตรงนี้ (ADR-05 S3)."""
    if not project.local_path:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "โปรเจกต์นี้ไม่ได้ผูกกับโฟลเดอร์บนดิสก์ — ใช้ได้เฉพาะโปรเจกต์ที่เปิดผ่าน /bootstrap",
        )
    folder = Path(project.local_path)
    if not folder.is_dir():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"ไม่พบโฟลเดอร์ของโปรเจกต์: {folder}"
        )
    return folder


@router.post("/{project_id}/design-files", response_model=DesignUploadResponse)
async def upload_design_files(
    project_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
) -> dict:
    """อัปโหลดไฟล์ดีไซน์เข้า `_design_input/` แล้วคืน requirement ที่ประกอบจากไฟล์เหล่านั้น.

    **ไม่เรียก AI ที่นี่** — ได้ข้อความออกมาให้คนอ่านตรวจก่อน แล้วค่อยส่งต่อ `/breakdown`
    ให้ PM Agent แตกงานตามปกติ (จะได้กติกาห้ามกุหลักฐาน + reviewer + audit ครบ)
    """
    project = _get_project_or_404(db, project_id)
    folder = _project_dir_or_400(project)

    uploads = [(f.filename or "", await f.read()) for f in files]
    saved = design_files.save_uploads(folder, uploads)
    requirement = design_files.build_requirement(folder, note)

    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="project.design_files_uploaded",
        entity_type="project",
        entity_id=str(project.id),
        diff={"files": saved},
    )
    db.commit()
    return {
        "saved": saved,
        "requirement": requirement,
        "requirement_chars": len(requirement),
    }


@router.post("/{project_id}/deliverables", response_model=DeliverableResponse)
def write_deliverable(
    project_id: uuid.UUID, payload: DeliverableRequest, db: Session = Depends(get_db)
) -> dict:
    """เขียนผลงานของ task ลงไฟล์จริงในโฟลเดอร์โปรเจกต์ (ADR-05 S3).

    เป็นขั้นที่**คนสั่งเอง** — agent เขียนไฟล์เองไม่ได้ (ทุก LLM call ผ่าน providers ที่ไม่มี tool)
    · สำรองไฟล์เดิมก่อนทับเสมอ · ไม่ commit ให้
    """
    project = _get_project_or_404(db, project_id)
    folder = _project_dir_or_400(project)
    task = db.get(Task, payload.task_id)
    if task is None or task.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ไม่พบ task นี้ในโปรเจกต์")

    try:
        result = deliverables.write_task_work_product(db, task, folder, payload.path)
    except deliverables.DeliverableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    record_audit(
        db,
        actor_type=ActorType.HUMAN,
        action="task.deliverable_written",
        entity_type="task",
        entity_id=str(task.id),
        diff={"path": result["path"], "bytes": result["bytes"], "backup": result["backup"]},
    )
    db.commit()
    return result


@router.get("/{project_id}/usage", response_model=ProjectUsage)
def project_token_usage(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """โทเคนของโปรเจกต์ **แยกตามผู้ให้บริการ** + ค่าใช้จ่ายเทียบเพดาน (§5).

    ⚠️ ตัวเลขเงินเป็น **ประมาณการจากราคาประกาศ** ที่ตั้งไว้ใน `.env` ไม่ใช่บิลจริงของบัญชี
    (ส่วนลด/เครดิต/ราคาพิเศษไม่ถูกนับ) — ห้ามเอาไปอ้างเป็นค่าใช้จ่ายจริง
    """
    _get_project_or_404(db, project_id)
    return usage.project_usage(db, project_id)


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


@router.post("/{project_id}/run/cancel")
def cancel_run(
    project_id: uuid.UUID,
    run_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """ขอให้รอบรันที่กำลังเดินอยู่หยุด — **หยุดหลัง task ปัจจุบันจบ** ไม่ตัดกลางคัน.

    ตัดกลาง task ไม่ได้โดยเจตนา: จะเหลือ task ค้างสถานะกลางทางให้มาแก้มือ และจ่ายค่า token
    ไปแล้วโดยไม่ได้ผลงาน · 404 = ไม่มีรอบรันของโปรเจกต์นี้ · รอบที่จบไปแล้ว = 409
    """
    _get_project_or_404(db, project_id)
    record = runs.get_run(run_id) if run_id else runs.latest_run_for_project(project_id)
    if record is None or record.project_id != str(project_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ไม่พบรอบรันของโปรเจกต์นี้")
    if record.status != RunStatus.RUNNING.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"รอบรันนี้จบไปแล้ว (สถานะ {record.status})"
        )
    runs.cancel_run(record.run_id)
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
