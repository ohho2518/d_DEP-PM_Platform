"""POST /api/agent-messages — ส่งข้อความ/handoff เข้า Message Bus (Blueprint §13)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.bus import publish
from app.constants import MessageType
from app.db.session import get_db
from app.models.project import Project

router = APIRouter(prefix="/api/agent-messages", tags=["agent-messages"])


class AgentMessageCreate(BaseModel):
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    from_agent_id: str | None = Field(default=None, max_length=100)
    to_agent_id: str | None = Field(default=None, max_length=100)
    message_type: MessageType
    payload: dict = Field(default_factory=dict)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_agent_message(
    body: AgentMessageCreate, db: Session = Depends(get_db)
) -> dict:
    if db.get(Project, body.project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    message = publish(
        db,
        project_id=body.project_id,
        task_id=body.task_id,
        from_agent_id=body.from_agent_id,
        to_agent_id=body.to_agent_id,
        message_type=body.message_type,
        payload=body.payload,
    )
    db.commit()
    return {"id": str(message.id), "created_at": message.created_at.isoformat()}
