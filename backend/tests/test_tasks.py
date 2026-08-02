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


# --- depends_on referential integrity (debt #5) ---


def test_create_task_rejects_dangling_depends_on(client):
    pid, _ = _project_with_task(client)
    resp = client.post(
        f"/api/projects/{pid}/tasks",
        json={"title": "B", "depends_on": ["00000000-0000-0000-0000-00000000dead"]},
    )
    assert resp.status_code == 400
    assert "depends_on" in resp.json()["detail"]


def test_create_task_rejects_cross_project_depends_on(client):
    _, tid = _project_with_task(client)
    other_pid = client.post("/api/projects", json={"name": "Q", "type": "new"}).json()["id"]
    resp = client.post(
        f"/api/projects/{other_pid}/tasks", json={"title": "B", "depends_on": [tid]}
    )
    assert resp.status_code == 400


def test_create_task_accepts_valid_depends_on(client):
    pid, tid = _project_with_task(client)
    resp = client.post(f"/api/projects/{pid}/tasks", json={"title": "B", "depends_on": [tid]})
    assert resp.status_code == 201
    assert resp.json()["depends_on"] == [tid]


def test_delete_task_blocked_when_referenced(client):
    pid, tid = _project_with_task(client)
    client.post(f"/api/projects/{pid}/tasks", json={"title": "B", "depends_on": [tid]})
    resp = client.delete(f"/api/tasks/{tid}")
    assert resp.status_code == 409
    assert "ลบไม่ได้" in resp.json()["detail"]


def test_delete_task_succeeds_when_unreferenced(client):
    _, tid = _project_with_task(client)
    assert client.delete(f"/api/tasks/{tid}").status_code == 204
    assert client.patch(f"/api/tasks/{tid}", json={"status": "planned"}).status_code == 404


def test_delete_missing_task_404(client):
    assert client.delete("/api/tasks/00000000-0000-0000-0000-000000000009").status_code == 404
