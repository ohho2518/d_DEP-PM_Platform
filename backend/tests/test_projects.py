"""Project + task endpoint tests."""
from __future__ import annotations


def _new_project(client, name="Demo", type="new", repo_url=None):
    body = {"name": name, "type": type}
    if repo_url:
        body["repo_url"] = repo_url
    return client.post("/api/projects", json=body)


def test_create_project(client):
    resp = _new_project(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Demo"
    assert data["type"] == "new"
    assert data["status"] == "planning"


def test_existing_project_requires_repo_url(client):
    resp = _new_project(client, type="existing")
    assert resp.status_code == 422  # model validator rejects missing repo_url


def test_create_and_list_tasks(client):
    pid = _new_project(client).json()["id"]
    created = client.post(
        f"/api/projects/{pid}/tasks",
        json={"title": "Set up CI", "priority": "P1", "estimate_points": 3},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "backlog"

    listing = client.get(f"/api/projects/{pid}/tasks")
    assert listing.status_code == 200
    body = listing.json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["title"] == "Set up CI"


def test_tasks_for_missing_project_404(client):
    resp = client.get("/api/projects/00000000-0000-0000-0000-000000000009/tasks")
    assert resp.status_code == 404
