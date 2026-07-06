"""MetadataProvider interface (ADR-02).

DEP v3.0 Metadata Engine has no real code yet (Phase 0-1). We lock the contract here so
that when the real engine ships, a ``DepEngineMetadataProvider`` can be swapped in without
touching the orchestrator or intake flow.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.scan import BaselineReport


@runtime_checkable
class MetadataProvider(Protocol):
    """Contract for producing a Baseline Report from a repo reference."""

    name: str
    is_mock: bool

    async def baseline_report(self, project_id: str, repo_ref: str | None) -> BaselineReport:
        """Scan ``repo_ref`` and return a Baseline Report convertible into initial tasks."""
        ...


def get_metadata_provider() -> MetadataProvider:
    """Return the active provider. Always the stub during MVP (ADR-02)."""
    # Imported lazily to avoid a circular import at module load.
    from app.metadata.stub import StubMetadataProvider

    return StubMetadataProvider()
