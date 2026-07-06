"""In-process message dispatcher (ADR-03).

หลักการจาก Blueprint §10: ทุกข้อความระหว่าง agent **ต้องลงตาราง `agent_messages` เสมอ**
(auditable source of truth) — dispatcher ตัวนี้เป็นแค่ transport ชั้นบาง ๆ

Upgrade path: Sprint 4 เปลี่ยน transport เป็น Redis Streams โดย schema ข้อความคงเดิม
(`from_agent`, `to_agent`, `message_type`, `payload`) — ผู้เรียก ``publish`` ไม่ต้องแก้.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable

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
