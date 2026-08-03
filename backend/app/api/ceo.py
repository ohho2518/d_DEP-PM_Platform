"""รับงานจากเลขา (d_CEO) และรายงานผลกลับ — Phase 1.

- GET  /api/ceo/status            สมองออนไลน์ไหม + ทีมที่ resolve ได้ + จำนวนงานที่รออยู่
- GET  /api/ceo/inbox             งาน queued ของทีม R&D ที่ยังไม่ถูกดึงมา
- POST /api/ceo/pull              รับงาน → สร้างโปรเจกต์ + แตกงาน + แจ้ง d_CEO ว่ารับแล้ว
- POST /api/ceo/report/{project}  ส่งผลงานกลับเข้า QC gate (สถานะ qc_review เท่านั้น)

ทั้งหมดเป็น **manual** โดยตั้งใจ — ผู้ใช้กดเอง เห็นพฤติกรรมจริงก่อนค่อยพิจารณา poller
อัตโนมัติ (หลัก "ยืนยันก่อนทำ" ของ ecosystem)
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.integrations.ceo_client import CeoClient, CeoUnavailable, get_ceo_client
from app.models.project import Project
from app.services import ceo_sync

router = APIRouter(prefix="/api/ceo", tags=["ceo"])


class PullRequest(BaseModel):
    """`task_ids` ว่าง/ไม่ส่ง = รับทุกงานที่รออยู่ (ความหมายเดียวกับ confirm-scope)."""

    task_ids: list[str] = Field(default_factory=list)
    breakdown: bool = True


def _require_client(client: CeoClient | None) -> CeoClient:
    if client is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "การเชื่อมต่อ d_CEO ปิดอยู่ — ตั้ง CEO_API_BASE ใน backend/.env",
        )
    return client


def _unavailable(exc: CeoUnavailable) -> HTTPException:
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))


@router.get("/status")
def ceo_status(
    db: Session = Depends(get_db), client: CeoClient | None = Depends(get_ceo_client)
) -> dict:
    """ไม่ 503 เมื่อสมองออฟไลน์ — UI ใช้ endpoint นี้ตัดสินใจว่าจะโชว์ปุ่มไหม."""
    settings = get_settings()
    if client is None:
        return {"enabled": False, "online": False, "team_name": settings.ceo_team_name}

    online = client.health()
    payload: dict = {
        "enabled": True,
        "online": online,
        "base_url": client.base_url,
        "team_name": settings.ceo_team_name,
        "team_id": None,
        "waiting": 0,
    }
    if not online:
        return payload
    try:
        payload["team_id"] = client.resolve_team_id(settings.ceo_team_name)
        payload["waiting"] = len(ceo_sync.list_inbox(db, client))
    except CeoUnavailable as exc:  # ล้มระหว่างทาง = ถือว่าออฟไลน์ ไม่ทำให้ UI พัง
        payload["online"] = False
        payload["detail"] = str(exc)
    return payload


@router.get("/inbox")
def ceo_inbox(
    db: Session = Depends(get_db), client: CeoClient | None = Depends(get_ceo_client)
) -> dict:
    ceo = _require_client(client)
    try:
        tasks = ceo_sync.list_inbox(db, ceo)
    except CeoUnavailable as exc:
        raise _unavailable(exc) from exc
    return {
        "data": [
            {
                "id": task.id,
                "input_text": task.input_text,
                "status": task.status,
                "created_at": task.created_at,  # UTC — FE แปลงเป็น Asia/Bangkok
            }
            for task in tasks
        ],
        "total": len(tasks),
    }


@router.post("/pull")
def ceo_pull(
    payload: PullRequest | None = None,
    db: Session = Depends(get_db),
    client: CeoClient | None = Depends(get_ceo_client),
) -> dict:
    ceo = _require_client(client)
    body = payload or PullRequest()
    try:
        results = ceo_sync.pull_tasks(
            db, ceo, task_ids=body.task_ids or None, breakdown=body.breakdown
        )
    except CeoUnavailable as exc:
        raise _unavailable(exc) from exc
    return {
        "pulled": [
            {
                "ceo_task_id": r.ceo_task_id,
                "project_id": r.project_id,
                "name": r.name,
                "task_count": r.task_count,
                "breakdown_source": r.breakdown_source,
                "acknowledged": r.acknowledged,
                "detail": r.detail,
            }
            for r in results
        ],
        "count": len(results),
    }


@router.post("/report/{project_id}")
def ceo_report(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    client: CeoClient | None = Depends(get_ceo_client),
) -> dict:
    ceo = _require_client(client)
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if not project.ceo_task_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "โปรเจกต์นี้ไม่ได้มาจาก d_CEO (ไม่มี ceo_task_id)"
        )

    result = ceo_sync.report_project(db, ceo, project)
    return {
        "ready": result.ready,
        "reported": result.reported,
        "status_sent": result.status_sent,
        "detail": result.detail,
        "counts": result.counts,
        "output": result.output,
    }


@router.post("/qc/{project_id}")
def ceo_request_qc(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    client: CeoClient | None = Depends(get_ceo_client),
) -> dict:
    """สั่ง QC ของ d_CEO ตรวจงานที่เรารายงานไปแล้ว — **ปุ่มฉุกเฉิน ปกติไม่ต้องใช้**.

    ตั้งแต่ contract v6 (2026-08-03) d_CEO ส่งงานเข้า QC ต่อให้เองเมื่อ PATCH เลื่อนสถานะ
    **เข้า** `qc_review` พร้อม `output` — ซึ่งเป็นสิ่งที่ `report_project` ทำอยู่แล้ว
    endpoint นี้มีไว้เผื่อ QC ฝั่งเขาล่มตอนนั้นแล้วงานค้าง

    ⚠️ **1 รอบ QC มีราคา** (~ครึ่งของค่างานหนึ่งชิ้น ตามที่เลขาวัดไว้ 2026-08-01) — อย่ายิงซ้ำเล่น
    """
    ceo = _require_client(client)
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if not project.ceo_task_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "โปรเจกต์นี้ไม่ได้มาจาก d_CEO (ไม่มี ceo_task_id)"
        )

    try:
        task = ceo.qc_task(project.ceo_task_id)
    except CeoUnavailable as exc:
        raise _unavailable(exc) from exc
    return {"ceo_task_id": project.ceo_task_id, "status": task.status, "detail": "สั่ง QC ตรวจแล้ว"}
