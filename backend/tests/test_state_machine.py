"""State Machine transition matrix + PATCH enforcement (Sprint 2 DoD)."""
from __future__ import annotations

import pytest

from app.constants import ActorType, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.state_machine import (
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    can_transition,
    transition,
)

ALL = list(TaskStatus)


def test_transition_matrix_is_exact():
    """ทุกคู่ (from, to): อนุญาตเฉพาะที่อยู่ใน ALLOWED_TRANSITIONS เท่านั้น."""
    for src in ALL:
        for dst in ALL:
            expected = dst in ALLOWED_TRANSITIONS[src]
            assert can_transition(src.value, dst.value) is expected, f"{src} -> {dst}"


def test_deployed_is_terminal():
    assert ALLOWED_TRANSITIONS[TaskStatus.DEPLOYED] == set()


def _make_task(db, status=TaskStatus.BACKLOG):
    project = Project(name="SM", type="new")
    db.add(project)
    db.flush()
    task = Task(project_id=project.id, title="t", status=status.value, depends_on=[])
    db.add(task)
    db.flush()
    return task


def test_transition_writes_audit(db_session):
    from sqlalchemy import select
    from app.models.audit_log import AuditLog

    task = _make_task(db_session)
    transition(db_session, task, TaskStatus.PLANNED, actor_type=ActorType.HUMAN)
    db_session.commit()

    assert task.status == "planned"
    audits = db_session.execute(
        select(AuditLog).where(AuditLog.action == "task.transition")
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].diff["status"] == {"from": "backlog", "to": "planned"}


def test_invalid_transition_raises(db_session):
    task = _make_task(db_session)  # backlog
    with pytest.raises(InvalidTransition):
        transition(db_session, task, TaskStatus.DONE, actor_type=ActorType.HUMAN)
    assert task.status == "backlog"  # unchanged


def test_patch_invalid_transition_returns_409(client):
    pid = client.post("/api/projects", json={"name": "P", "type": "new"}).json()["id"]
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "T"}).json()["id"]

    # backlog -> done ข้ามขั้น → 409
    resp = client.patch(f"/api/tasks/{tid}", json={"status": "done"})
    assert resp.status_code == 409

    # เดินตามลำดับที่ถูกต้องได้
    for step in ["planned", "assigned", "in_progress", "review", "done", "deployed"]:
        resp = client.patch(f"/api/tasks/{tid}", json={"status": step})
        assert resp.status_code == 200, step
        assert resp.json()["status"] == step

    # deployed เป็น terminal
    resp = client.patch(f"/api/tasks/{tid}", json={"status": "backlog"})
    assert resp.status_code == 409
