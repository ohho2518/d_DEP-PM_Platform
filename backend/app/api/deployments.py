"""Deployments endpoints (Sprint 4, Blueprint §13):

- POST  /api/deployments        trigger deploy (manual — production ต้องมาทางนี้เท่านั้น)
- GET   /api/deployments/:id    สถานะ deploy
- PATCH /api/deployments/:id    callback จาก GitHub workflow (queued/running -> success/failed)
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

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


@router.get("/{deployment_id}")
def get_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    deployment = db.get(Deployment, deployment_id)
    if deployment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deployment not found")
    return _serialize(deployment)


@router.patch("/{deployment_id}")
def update_deployment(
    deployment_id: uuid.UUID, body: DeploymentUpdate, db: Session = Depends(get_db)
) -> dict:
    """Callback จาก CI workflow — อัปเดตผล + ถ้า success ให้เลื่อน task done -> deployed."""
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
