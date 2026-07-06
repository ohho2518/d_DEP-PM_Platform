"""Project request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: ProjectType = ProjectType.NEW
    repo_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _existing_requires_repo(self) -> "ProjectCreate":
        # An 'existing' (Brownfield) project needs a repo to scan (even if scan is a stub).
        if self.type == ProjectType.EXISTING and not self.repo_url:
            raise ValueError("repo_url is required when type='existing'")
        return self


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: ProjectType
    repo_url: str | None
    status: ProjectStatus
    metadata_registry_ref: str | None
    created_at: datetime
