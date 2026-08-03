"""In-process message dispatcher (ADR-03).

หลักการจาก Blueprint §10: ทุกข้อความระหว่าง agent **ต้องลงตาราง `agent_messages` เสมอ**
(auditable source of truth) — dispatcher ตัวนี้เป็นแค่ transport ชั้นบาง ๆ

Upgrade path: Sprint 4 เปลี่ยน transport เป็น Redis Streams โดย schema ข้อความคงเดิม
(`from_agent`, `to_agent`, `message_type`, `payload`) — ผู้เรียก ``publish`` ไม่ต้องแก้.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import MessageType
from app.models.agent_message import AgentMessage

# Subscribers รับ AgentMessage ที่ persist แล้ว (in-process เท่านั้นใน MVP).
Subscriber = Callable[[AgentMessage], None]
_subscribers: list[Subscriber] = []


def subscribe(handler: Subscriber) -> None:
    _subscribers.append(handler)


def clear_subscribers() -> None:
    _subscribers.clear()


def publish(
    db: Session,
    *,
    project_id: uuid.UUID,
    task_id: uuid.UUID | None,
    from_agent_id: str | None,
    to_agent_id: str | None,
    message_type: MessageType,
    payload: dict,
) -> AgentMessage:
    """Persist the message (always), then fan out to in-process subscribers.

    Does not commit — caller owns the transaction, same convention as the state machine.
    """
    message = AgentMessage(
        project_id=project_id,
        task_id=task_id,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        message_type=message_type.value,
        payload=payload,
    )
    db.add(message)
    db.flush()

    for handler in list(_subscribers):
        handler(message)
    return message


def clip_work(text: str, limit: int) -> str:
    """ตัดผลงานให้พอดีเพดาน พร้อม**บอกตรง ๆ ว่าถูกตัด**.

    สำคัญกว่าที่คิด: ถ้าตัดเงียบ ๆ agent ที่อ่านต่อจะเข้าใจว่านี่คือของครบแล้วทำงานผิด
    และ QC ที่อ่านรายงานจะตัดสินจากของไม่ครบโดยไม่รู้ตัว
    """
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n…(ตัดเหลือ {limit:,} ตัวอักษรแรก จากทั้งหมด {len(text):,})"


def latest_work_by_task(db: Session, task_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    """ผลงาน (work product) **ล่าสุด** ของแต่ละ task — จากข้อความ ``result`` บน bus.

    ตาราง ``agent_messages`` เป็นที่เดียวที่เก็บตัวชิ้นงานจริง (task เก็บแค่ metadata)
    ทั้ง orchestrator (ส่งเป็น context ให้ task ที่ depend อยู่) และ ceo_sync
    (แนบในรายงานถึง d_CEO) ต้องใช้ข้อมูลชุดเดียวกัน จึงอ่านผ่านฟังก์ชันนี้ที่เดียว

    "ล่าสุด" = หลัง revision ครั้งสุดท้าย — งานรอบก่อนถูกทับ แต่ยังอยู่ในตารางให้ตรวจย้อนหลังได้
    """
    if not task_ids:
        return {}
    rows = (
        db.execute(
            select(AgentMessage)
            .where(
                AgentMessage.task_id.in_(task_ids),
                AgentMessage.message_type == MessageType.RESULT.value,
            )
            .order_by(AgentMessage.created_at)
        )
        .scalars()
        .all()
    )
    works: dict[uuid.UUID, str] = {}
    for message in rows:  # ตัวหลังทับตัวหน้า = ได้ผลงานล่าสุด
        work = (message.payload or {}).get("work")
        if message.task_id is not None and work:
            works[message.task_id] = str(work)
    return works
