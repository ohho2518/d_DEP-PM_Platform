"""Deploy pipeline service (Sprint 4, Blueprint §12).

สร้าง deployment record + ยิง GitHub `repository_dispatch` เมื่อ config ครบ
(`GITHUB_TOKEN` + `GITHUB_REPO`) — ไม่ครบ = stub mode: record ถูกสร้างสถานะ `queued`
พร้อม environment ใน payload ระบุว่า dispatch ไม่ได้ยิงจริง (graceful degradation
แบบเดียวกับ PM Agent)

กติกาจาก Blueprint §12:
- staging: trigger อัตโนมัติได้ (จาก orchestrator เมื่อ task done + AUTO_DEPLOY_ENABLED)
- production: ต้องสั่งมือเสมอ (Manual Approval Gate) — enforce ที่ endpoint

Callback: workflow ฝั่ง GitHub รายงานผลกลับผ่าน PATCH /api/deployments/:id
(ตัวอย่าง workflow ใน docs/github-workflow-example.yml)
"""
from __future__ import annotations

import uuid

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import ActorType, DeploymentStatus, DeploymentTrigger
from app.models.deployment import Deployment
from app.services.audit import record_audit

# ชื่อ event ที่ workflow ฝั่ง repo ต้อง subscribe (types ใน on.repository_dispatch)
DISPATCH_EVENT_TYPE = "dep-pm-deploy"


class DispatchResult:
    def __init__(self, dispatched: bool, detail: str) -> None:
        self.dispatched = dispatched
        self.detail = detail


def _fire_repository_dispatch(deployment: Deployment) -> DispatchResult:
    """ยิง POST /repos/{repo}/dispatches — คืนผลโดยไม่ raise (caller ตัดสินใจต่อ)."""
    settings = get_settings()
    if not settings.deploy_dispatch_enabled:
        return DispatchResult(False, "stub: GITHUB_TOKEN/GITHUB_REPO not configured")

    try:
        response = httpx.post(
            f"https://api.github.com/repos/{settings.github_repo}/dispatches",
            headers={
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "event_type": DISPATCH_EVENT_TYPE,
                "client_payload": {
                    "deployment_id": str(deployment.id),
                    "project_id": str(deployment.project_id),
                    "task_id": str(deployment.task_id) if deployment.task_id else None,
                    "environment": deployment.environment,
                },
            },
            timeout=15.0,
        )
        if response.status_code == 204:  # GitHub ตอบ 204 No Content เมื่อสำเร็จ
            return DispatchResult(True, "repository_dispatch sent")
        return DispatchResult(False, f"github responded {response.status_code}: {response.text[:200]}")
    except httpx.HTTPError as exc:
        return DispatchResult(False, f"network error: {exc}")


def create_deployment(
    db: Session,
    *,
    project_id: uuid.UUID,
    task_id: uuid.UUID | None,
    environment: str,
    triggered_by: DeploymentTrigger,
    actor_id: str,
) -> tuple[Deployment, DispatchResult]:
    """สร้าง record + พยายาม dispatch. ไม่ commit — caller เป็นเจ้าของ transaction.

    สถานะเริ่มต้น: dispatch สำเร็จ -> `running` (workflow กำลังทำ), ไม่สำเร็จ/stub -> `queued`.
    """
    deployment = Deployment(
        project_id=project_id,
        task_id=task_id,
        triggered_by=triggered_by.value,
        environment=environment,
        status=DeploymentStatus.QUEUED.value,
    )
    db.add(deployment)
    db.flush()

    result = _fire_repository_dispatch(deployment)
    if result.dispatched:
        deployment.status = DeploymentStatus.RUNNING.value

    record_audit(
        db,
        actor_type=ActorType.AGENT if triggered_by == DeploymentTrigger.AUTO else ActorType.HUMAN,
        actor_id=actor_id,
        action="deployment.created",
        entity_type="deployment",
        entity_id=str(deployment.id),
        diff={
            "environment": environment,
            "triggered_by": triggered_by.value,
            "dispatched": result.dispatched,
            "detail": result.detail,
        },
    )
    return deployment, result
