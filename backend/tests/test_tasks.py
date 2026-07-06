"""Task PATCH + messages endpoints."""
from __future__ import annotations


def _project_with_task(client):
    pid = client.post("/api/projects", json={"name": "P", "type": "new"}).json()["id"]
    tid = client.post(
        f"/api/projects/{pid}/tasks", json={"title": "Do thing"}
    ).json()["id"]
    return pid, tid


def test_patch_task_status_and_assignee(client):
    _, tid = _project_with_task(client)
    resp = client.patch(
        f"/api/tasks/{tid}",
        json={"status": "planned", "assignee_type": "agent", "agent_role": "dev"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "planned"
    assert data["assignee_type"] == "agent"
    assert data["agent_role"] == "dev"


def test_patch_missing_task_404(client):
    resp = client.patch(
        "/api/tasks/00000000-0000-0000-0000-000000000009", json={"status": "done"}
    )
    assert resp.status_code == 404


def test_task_messages_empty_initially(client):
    _, tid = _project_with_task(client)
    resp = client.get(f"/api/tasks/{tid}/messages")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
