"""Deployments endpoints (Sprint 4, Blueprint §13):

- POST  /api/deployments        trigger deploy (manual — production ต้องมาทางนี้เท่านั้น)
- GET   /api/deployments        รายการ deployments (ใหม่ล่าสุดก่อน, filter ด้วย project_id ได้)
- GET   /api/deployments/:id    สถานะ deploy
- PATCH /api/deployments/:id    callback จาก GitHub workflow (queued/running -> success/failed)
"""
from __future__ import annotations

import hmac
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import ActorType, DeploymentStatus, DeploymentTrigger, TaskStatus
from app.db.session import get_db
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.state_machine import InvalidTransition, transition
from app.services.audit import record_audit
from app.services.deploy import create_deployment

router = APIRouter(prefix="/api/deployments", tags=["deployments"])

VALID_ENVIRONMENTS = {"staging", "production"}

# Callback อนุญาตเฉพาะ transition ไปข้างหน้า (terminal คือ success/failed)
_CALLBACK_ALLOWED: dict[str, set[str]] = {
    DeploymentStatus.QUEUED.value: {DeploymentStatus.RUNNING.value, DeploymentStatus.SUCCESS.value, DeploymentStatus.FAILED.value},
    DeploymentStatus.RUNNING.value: {DeploymentStatus.SUCCESS.value, DeploymentStatus.FAILED.value},
    DeploymentStatus.SUCCESS.value: set(),
    DeploymentStatus.FAILED.value: set(),
}


CALLBACK_SECRET_HEADER = "X-DEP-PM-Secret"


def require_callback_secret(
    secret: str | None = Header(default=None, alias=CALLBACK_SECRET_HEADER),
) -> None:
    """ตรวจ shared secret ของ callback จาก CI (Risk #1).

    **ไม่ตั้งค่า = ไม่ตรวจ** — ยังเป็นค่าปริยายเพื่อไม่ให้ dev บน localhost และ workflow
    ที่ติดตั้งไปแล้วพังทันที · แต่ก่อนเปิดพอร์ตออกนอกเครื่อง **ต้องตั้ง `DEPLOY_CALLBACK_SECRET`**
    ไม่งั้นใครก็ตามที่ยิงถึงพอร์ตได้จะเลื่อน task เป็น `deployed` ปลอมได้ (`docs/SECURITY.md`)

    เทียบด้วย `hmac.compare_digest` — กัน timing attack ที่เดา secret ทีละตัวอักษร ·
    เทียบเป็น **bytes** เพราะเวอร์ชัน str รับเฉพาะ ASCII: secret ที่มีอักษรไทยจะทำให้ 500
    แทนที่จะเป็น 401 (ค่าใน `.env` เป็นอะไรก็ได้ เราคุมไม่ได้)
    """
    settings = get_settings()
    if not settings.callback_auth_enabled:
        return
    if secret is None or not hmac.compare_digest(
        secret.encode("utf-8"), settings.deploy_callback_secret.encode("utf-8")
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"callback ต้องแนบ header {CALLBACK_SECRET_HEADER} ให้ตรงกับ DEPLOY_CALLBACK_SECRET",
        )


class DeploymentCreate(BaseModel):
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    environment: str = Field(default="staging")


class DeploymentUpdate(BaseModel):
    status: DeploymentStatus
    commit_sha: str | None = Field(default=None, max_length=64)


def _serialize(d: Deployment) -> dict:
    return {
        "id": str(d.id),
        "project_id": str(d.project_id),
        "task_id": str(d.task_id) if d.task_id else None,
        "triggered_by": d.triggered_by,
        "status": d.status,
        "environment": d.environment,
        "commit_sha": d.commit_sha,
        "created_at": d.created_at.isoformat(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def trigger_deployment(body: DeploymentCreate, db: Session = Depends(get_db)) -> dict:
    if body.environment not in VALID_ENVIRONMENTS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"environment ต้องเป็นหนึ่งใน {sorted(VALID_ENVIRONMENTS)}",
        )
    if db.get(Project, body.project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if body.task_id is not None and db.get(Task, body.task_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    # Manual Approval Gate (Blueprint §12): production trigger ได้จาก endpoint นี้
    # (มนุษย์สั่ง) เท่านั้น — เส้นทาง auto ของ orchestrator ยิงได้แค่ staging
    deployment, result = create_deployment(
        db,
        project_id=body.project_id,
        task_id=body.task_id,
        environment=body.environment,
        triggered_by=DeploymentTrigger.MANUAL,
        actor_id="human",
    )
    db.commit()
    db.refresh(deployment)
    return {**_serialize(deployment), "dispatched": result.dispatched, "detail": result.detail}


@router.get("")
def list_deployments(
    project_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict:
    """รายการ deployments ใหม่ล่าสุดก่อน — ใช้กับหน้า Deployments ใน UI."""
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    base = select(Deployment)
    if project_id is not None:
        base = base.where(Deployment.project_id == project_id)

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    rows = (
        # tie-break ด้วย id เพราะ `created_at` ชนกันได้จริง: นาฬิกาของ Windows ก้าวทีละ ~15.6 ms
        # (วัดแล้ว utcnow() 400 ครั้งติดกันได้ค่าเดียว) แถวที่สร้างในคำขอเดียวกันจึงเวลาเท่ากันเป๊ะ
        # ⚠️ id เป็น UUID สุ่ม = ลำดับใน tie ไม่ใช่ลำดับที่สร้างจริง แต่ **คงที่ทุกครั้งที่เรียก**
        # ซึ่งคือสิ่งที่ UI ต้องการ (รายการไม่สลับตำแหน่งเองตอนรีเฟรช)
        db.execute(
            base.order_by(Deployment.created_at.desc(), Deployment.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    # เติมชื่อ project/task ให้ UI ไม่ต้องยิงเพิ่มรายแถว
    project_names = {
        p.id: p.name
        for p in db.execute(
            select(Project).where(Project.id.in_({d.project_id for d in rows}))
        ).scalars()
    }
    task_ids = {d.task_id for d in rows if d.task_id}
    task_titles = {
        t.id: t.title
        for t in db.execute(select(Task).where(Task.id.in_(task_ids))).scalars()
    } if task_ids else {}

    return {
        "data": [
            {
                **_serialize(d),
                "project_name": project_names.get(d.project_id),
                "task_title": task_titles.get(d.task_id) if d.task_id else None,
            }
            for d in rows
        ],
        "pagination": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/{deployment_id}")
def get_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    deployment = db.get(Deployment, deployment_id)
    if deployment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deployment not found")
    return _serialize(deployment)


@router.patch("/{deployment_id}", dependencies=[Depends(require_callback_secret)])
def update_deployment(
    deployment_id: uuid.UUID, body: DeploymentUpdate, db: Session = Depends(get_db)
) -> dict:
    """Callback จาก CI workflow — อัปเดตผล + ถ้า success ให้เลื่อน task done -> deployed.

    endpoint เดียวในระบบที่ "ผู้เรียกอยู่นอกเครื่อง" จึงเป็นจุดเดียวที่มี auth (shared secret)
    """
    deployment = db.get(Deployment, deployment_id)
    if deployment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deployment not found")

    if body.status.value not in _CALLBACK_ALLOWED[deployment.status]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"invalid deployment status change: {deployment.status} -> {body.status.value}",
        )

    previous = deployment.status
    deployment.status = body.status.value
    if body.commit_sha:
        deployment.commit_sha = body.commit_sha

    record_audit(
        db,
        actor_type=ActorType.AGENT,
        actor_id="ci-workflow",
        action="deployment.status_changed",
        entity_type="deployment",
        entity_id=str(deployment.id),
        diff={"status": {"from": previous, "to": deployment.status}},
    )

    # Deploy สำเร็จ => สะท้อนกลับบอร์ด: task done -> deployed (State Machine ปกติ)
    if deployment.status == DeploymentStatus.SUCCESS.value and deployment.task_id:
        task = db.get(Task, deployment.task_id)
        if task is not None and task.status == TaskStatus.DONE.value:
            try:
                transition(
                    db, task, TaskStatus.DEPLOYED,
                    actor_type=ActorType.AGENT, actor_id="ci-workflow",
                    reason=f"deployment {deployment.id} succeeded",
                )
            except InvalidTransition:  # task ถูกย้ายไปแล้วระหว่างรอ CI — ไม่ถือเป็น error
                pass

    db.commit()
    db.refresh(deployment)
    return _serialize(deployment)
