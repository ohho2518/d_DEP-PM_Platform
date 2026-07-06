"""Routing Rules (Blueprint §9, Solo Mode column): task -> persona ที่รับผิดชอบ.

MVP ใช้ keyword heuristic ง่าย ๆ — งานเชิงออกแบบ/สถาปัตยกรรม → Senior Architect,
ที่เหลือ → Developer. ทุกการตัดสินใจถูก log ลง audit (Risk #5: ปรับ rules จากข้อมูลจริง).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ActorType, AgentRole
from app.models.task import Task
from app.services.audit import record_audit

# Keywords (ไทย + อังกฤษ) ที่บ่งชี้งานเชิงออกแบบ/สถาปัตยกรรม.
_ARCHITECT_KEYWORDS = (
    "architecture",
    "architect",
    "design",
    "schema",
    "data model",
    "adr",
    "infra",
    "ออกแบบ",
    "สถาปัตย",
    "โครงสร้างระบบ",
)


def route_task(db: Session, task: Task) -> AgentRole:
    """เลือก persona สำหรับ task และบันทึกเหตุผลการ route ลง audit_log."""
    haystack = " ".join(
        part.lower() for part in (task.title, task.description or "", task.spec or "")
    )
    matched = next((kw for kw in _ARCHITECT_KEYWORDS if kw in haystack), None)
    role = AgentRole.SENIOR_ARCHITECT if matched else AgentRole.DEV

    record_audit(
        db,
        actor_type=ActorType.AGENT,
        actor_id="orchestrator",
        action="task.routed",
        entity_type="task",
        entity_id=str(task.id),
        diff={"role": role.value, "matched_keyword": matched},
    )
    return role
