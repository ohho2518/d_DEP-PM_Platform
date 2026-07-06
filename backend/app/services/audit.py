"""Audit-log helper. Every meaningful state change should call this (Blueprint §15)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ActorType
from app.models.audit_log import AuditLog


def record_audit(
    db: Session,
    *,
    actor_type: ActorType,
    action: str,
    entity_type: str,
    entity_id: str | None,
    actor_id: str | None = None,
    diff: dict | None = None,
) -> AuditLog:
    """Add (not commit) an AuditLog row. Caller controls the surrounding transaction."""
    entry = AuditLog(
        actor_type=actor_type.value,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        diff=diff or {},
    )
    db.add(entry)
    return entry
