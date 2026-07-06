"""Schemas for the Metadata scan / Baseline Report (Brownfield flow — ADR-02, Blueprint §7)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.constants import Priority


class BaselineFinding(BaseModel):
    """One issue discovered by a scan (mock while DEP Engine is a stub)."""

    category: str = Field(..., description="e.g. 'tech_debt', 'missing_tests', 'doc_coverage'")
    title: str
    detail: str | None = None
    suggested_priority: Priority = Priority.P2
    confidence: float = Field(..., ge=0.0, le=1.0)


class BaselineReport(BaseModel):
    project_id: str
    provider: str = Field(..., description="Which MetadataProvider produced this")
    is_mock: bool = Field(..., description="True while backed by StubMetadataProvider")
    summary: str
    findings: list[BaselineFinding]


class ScanResponse(BaseModel):
    """Response of POST /api/projects/:id/scan — the report plus the tasks it created."""

    report: BaselineReport
    created_task_ids: list[str]
