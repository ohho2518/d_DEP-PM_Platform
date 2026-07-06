"""Task request/response schemas + the PM Agent Task-Plan contract."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.constants import AgentRole, AssigneeType, Priority, TaskStatus


class TaskCreate(BaseModel):
    """Human- or agent-created task. Defaults to backlog."""

    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    priority: Priority = Priority.P2
    depends_on: list[uuid.UUID] = Field(default_factory=list)
    spec: str | None = None
    estimate_points: int | None = Field(default=None, ge=0)


class TaskUpdate(BaseModel):
    """PATCH /api/tasks/:id — partial update (status / assignee). Validated further in Sprint 2."""

    status: TaskStatus | None = None
    assignee_type: AssigneeType | None = None
    assignee_id: str | None = None
    agent_role: AgentRole | None = None
    priority: Priority | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    spec: str | None = None
    estimate_points: int | None = Field(default=None, ge=0)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    assignee_type: AssigneeType | None
    assignee_id: str | None
    agent_role: AgentRole | None
    priority: Priority
    depends_on: list[uuid.UUID]
    spec: str | None
    estimate_points: int | None
    revision_count: int
    created_at: datetime
    updated_at: datetime


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int


class TaskList(BaseModel):
    data: list[TaskRead]
    pagination: Pagination


# ---------------------------------------------------------------------------
# PM Agent Task-Plan contract (Blueprint §6, SOW PM). The agent must return JSON
# that parses into ``TaskPlan``; ``ref`` lets the agent express dependencies by a
# local reference (e.g. "T1") before real UUIDs exist.
# ---------------------------------------------------------------------------
class PlannedTask(BaseModel):
    ref: str = Field(..., description="Local id used for depends_on within this plan, e.g. 'T1'")
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    priority: Priority = Priority.P2
    estimate_points: int | None = Field(default=None, ge=0)
    depends_on: list[str] = Field(default_factory=list, description="refs of prerequisite tasks")
    spec: str | None = None


class TaskPlan(BaseModel):
    tasks: list[PlannedTask]


class BreakdownRequest(BaseModel):
    requirement: str = Field(..., min_length=1, description="Free-text requirement to break down")


class BreakdownResponse(BaseModel):
    """Result of a breakdown: created backlog tasks + whether a live agent produced them."""

    source: str = Field(..., description="'agent' or 'fallback' (no API key / parse failure)")
    tasks: list[TaskRead]


class ConfirmScopeRequest(BaseModel):
    """Confirm a set of backlog tasks -> planned. Empty list = confirm all backlog tasks."""

    task_ids: list[uuid.UUID] = Field(default_factory=list)
