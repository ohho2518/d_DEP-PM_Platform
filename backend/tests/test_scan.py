"""Brownfield scan via StubMetadataProvider (ADR-02)."""
from __future__ import annotations


def test_scan_existing_project_creates_mock_baseline_tasks(client):
    pid = client.post(
        "/api/projects",
        json={"name": "Legacy", "type": "existing", "repo_url": "https://example.com/repo"},
    ).json()["id"]

    resp = client.post(f"/api/projects/{pid}/scan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report"]["is_mock"] is True
    assert len(body["report"]["findings"]) == 3
    assert len(body["created_task_ids"]) == 3

    # Findings should have become backlog tasks.
    tasks = client.get(f"/api/projects/{pid}/tasks").json()["data"]
    assert len(tasks) == 3
    assert all(t["status"] == "backlog" for t in tasks)


def test_scan_rejects_new_project(client):
    pid = client.post("/api/projects", json={"name": "Fresh", "type": "new"}).json()["id"]
    resp = client.post(f"/api/projects/{pid}/scan")
    assert resp.status_code == 400
