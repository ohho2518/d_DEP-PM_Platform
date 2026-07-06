"""Deploy pipeline tests (Sprint 4) — stub mode (ไม่มี GITHUB_TOKEN ใน tests)."""
from __future__ import annotations

import uuid

from app.agents.runtime import ReviewResult
from app.models.task import Task
from app.orchestrator.engine import run_project


def _project(client, name="Dep"):
    return client.post("/api/projects", json={"name": name, "type": "new"}).json()["id"]


def _done_task(client, pid):
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "ship"}).json()["id"]
    for step in ["planned", "assigned", "in_progress", "review", "done"]:
        client.patch(f"/api/tasks/{tid}", json={"status": step})
    return tid


def test_trigger_deployment_stub_mode(client):
    pid = _project(client)
    resp = client.post("/api/deployments", json={"project_id": pid, "environment": "staging"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "queued"        # stub: ไม่ dispatch จริง
    assert body["dispatched"] is False
    assert "stub" in body["detail"]
    assert body["triggered_by"] == "manual"


def test_deployment_invalid_environment(client):
    pid = _project(client)
    resp = client.post("/api/deployments", json={"project_id": pid, "environment": "prod"})
    assert resp.status_code == 400


def test_deployment_missing_project_404(client):
    resp = client.post(
        "/api/deployments",
        json={"project_id": str(uuid.uuid4()), "environment": "staging"},
    )
    assert resp.status_code == 404


def test_get_deployment_status(client):
    pid = _project(client)
    did = client.post(
        "/api/deployments", json={"project_id": pid, "environment": "staging"}
    ).json()["id"]
    resp = client.get(f"/api/deployments/{did}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


def test_callback_success_moves_task_to_deployed(client):
    pid = _project(client)
    tid = _done_task(client, pid)
    did = client.post(
        "/api/deployments",
        json={"project_id": pid, "task_id": tid, "environment": "staging"},
    ).json()["id"]

    resp = client.patch(
        f"/api/deployments/{did}", json={"status": "success", "commit_sha": "abc123"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert resp.json()["commit_sha"] == "abc123"

    # deploy สำเร็จ → task done -> deployed (สะท้อนบน dashboard)
    tasks = client.get(f"/api/projects/{pid}/tasks").json()["data"]
    assert tasks[0]["status"] == "deployed"


def test_callback_terminal_status_is_immutable(client):
    pid = _project(client)
    did = client.post(
        "/api/deployments", json={"project_id": pid, "environment": "staging"}
    ).json()["id"]
    client.patch(f"/api/deployments/{did}", json={"status": "failed"})
    resp = client.patch(f"/api/deployments/{did}", json={"status": "success"})
    assert resp.status_code == 409


def test_portfolio_shows_last_deployment(client):
    pid = _project(client)
    client.post("/api/deployments", json={"project_id": pid, "environment": "staging"})
    proj = next(
        p for p in client.get("/api/portfolio").json()["projects"] if p["id"] == pid
    )
    assert proj["last_deployment"] is not None
    assert proj["last_deployment"]["environment"] == "staging"


# ---------------------------------------------------------------------------
# Auto-deploy hook (orchestrator done -> staging deployment เมื่อเปิด flag)
# ---------------------------------------------------------------------------
class _ApproveAll:
    def execute(self, task, role, feedback=None):
        return "work"

    def review(self, task, work):
        return ReviewResult(approved=True, comment="ok")


def test_auto_deploy_disabled_by_default(client, db_session):
    from app.models.project import Project
    from app.models.deployment import Deployment
    from sqlalchemy import select

    project = Project(name="AutoOff", type="new")
    db_session.add(project)
    db_session.flush()
    db_session.add(Task(project_id=project.id, title="t", status="planned", depends_on=[]))
    db_session.commit()

    run_project(db_session, project.id, executor=_ApproveAll())
    deployments = db_session.execute(select(Deployment)).scalars().all()
    assert deployments == []  # default: ปิด


def test_auto_deploy_creates_staging_deployment(client, db_session, monkeypatch):
    from app.config import get_settings
    from app.models.project import Project
    from app.models.deployment import Deployment
    from sqlalchemy import select

    monkeypatch.setattr(get_settings(), "auto_deploy_enabled", True)

    project = Project(name="AutoOn", type="new")
    db_session.add(project)
    db_session.flush()
    task = Task(project_id=project.id, title="t", status="planned", depends_on=[])
    db_session.add(task)
    db_session.commit()

    run_project(db_session, project.id, executor=_ApproveAll())

    deployments = db_session.execute(select(Deployment)).scalars().all()
    assert len(deployments) == 1
    d = deployments[0]
    assert d.environment == "staging"          # auto ยิงได้เฉพาะ staging
    assert d.triggered_by == "auto"
    assert d.task_id == task.id
    assert d.status == "queued"                # stub mode
