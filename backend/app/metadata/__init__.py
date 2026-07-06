"""Metadata subsystem: provider interface + stub implementation (ADR-02)."""
from app.metadata.provider import MetadataProvider, get_metadata_provider
from app.metadata.stub import StubMetadataProvider

__all__ = ["MetadataProvider", "StubMetadataProvider", "get_metadata_provider"]
