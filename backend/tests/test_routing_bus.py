"""Routing Rules + Message Bus tests."""
from __future__ import annotations

from sqlalchemy import select

from app.agents.routing import route_task
from app.bus import clear_subscribers, publish, subscribe
from app.constants import AgentRole, MessageType
from app.models.agent_message import AgentMessage
from app.models.project import Project
from app.models.task import Task


def _task(db, title, description=None, spec=None):
    project = Project(name="R", type="new")
    db.add(project)
    db.flush()
    task = Task(
        project_id=project.id, title=title, description=description, spec=spec, depends_on=[]
    )
    db.add(task)
    db.flush()
    return task


def test_design_task_routes_to_architect(db_session):
    task = _task(db_session, "ออกแบบ database schema สำหรับระบบ billing")
    assert route_task(db_session, task) == AgentRole.SENIOR_ARCHITECT


def test_english_architecture_keyword(db_session):
    task = _task(db_session, "Define service architecture", spec="draw component diagram")
    assert route_task(db_session, task) == AgentRole.SENIOR_ARCHITECT


def test_default_routes_to_dev(db_session):
    task = _task(db_session, "Implement login endpoint")
    assert route_task(db_session, task) == AgentRole.DEV


def test_publish_persists_and_dispatches(db_session):
    task = _task(db_session, "bus target")
    received = []
    subscribe(received.append)
    try:
        msg = publish(
            db_session,
            project_id=task.project_id,
            task_id=task.id,
            from_agent_id="dev",
            to_agent_id="reviewer",
            message_type=MessageType.RESULT,
            payload={"work": "done"},
        )
        db_session.commit()
    finally:
        clear_subscribers()

    assert received == [msg]  # in-process dispatch
    rows = db_session.execute(select(AgentMessage)).scalars().all()
    assert len(rows) == 1  # persist เสมอ (ADR-03)
    assert rows[0].payload == {"work": "done"}


def test_agent_messages_endpoint(client):
    pid = client.post("/api/projects", json={"name": "P", "type": "new"}).json()["id"]
    resp = client.post(
        "/api/agent-messages",
        json={
            "project_id": pid,
            "from_agent_id": "pm",
            "to_agent_id": "dev",
            "message_type": "handoff",
            "payload": {"note": "เริ่มงานได้"},
        },
    )
    assert resp.status_code == 201
    assert "id" in resp.json()


def test_agent_messages_endpoint_missing_project_404(client):
    resp = client.post(
        "/api/agent-messages",
        json={
            "project_id": "00000000-0000-0000-0000-000000000009",
            "message_type": "handoff",
        },
    )
    assert resp.status_code == 404
