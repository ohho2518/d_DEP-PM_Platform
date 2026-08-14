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


# --- โทเคนแยกตามผู้ให้บริการ (§5 ใบสั่งงาน 2026-08-06) ------------------------


def test_project_usage_splits_tokens_by_provider(client, db_session):
    """ถังสำหรับเพดานค่าใช้จ่ายต่อเจ้า — ต้องรวมข้าม task และเรียงตัวที่กินมากสุดขึ้นก่อน."""
    from app.models.task import Task

    pid = _new_project(client, name="Usage").json()["id"]
    db_session.add_all(
        [
            Task(
                project_id=pid,
                title="t1",
                depends_on=[],
                tokens_input=130,
                tokens_output=50,
                token_usage={
                    "openai": {"input": 100, "output": 40, "calls": 1, "model": "gpt-5.2"},
                    "anthropic": {"input": 30, "output": 10, "calls": 1, "model": "claude-sonnet-5"},
                },
            ),
            Task(
                project_id=pid,
                title="t2",
                depends_on=[],
                tokens_input=20,
                tokens_output=5,
                token_usage={"openai": {"input": 20, "output": 5, "calls": 2, "model": "gpt-5.2"}},
            ),
        ]
    )
    db_session.commit()

    body = client.get(f"/api/projects/{pid}/usage").json()

    assert body["totals"] == {"input": 150, "output": 55, "calls": 4}
    assert [p["provider"] for p in body["by_provider"]] == ["openai", "anthropic"]
    openai_row = body["by_provider"][0]
    assert openai_row["input"] == 120 and openai_row["output"] == 45
    assert openai_row["calls"] == 3 and openai_row["tasks"] == 2
    assert body["untracked"] == {"input": 0, "output": 0, "calls": 0}


def test_project_usage_keeps_old_tokens_visible_as_untracked(client, db_session):
    """งานที่ทำก่อนมีคอลัมน์นี้แยกที่มาไม่ได้ — ต้องโชว์แยกไว้ ไม่ใช่เดาว่าเป็นของเจ้าไหน."""
    from app.models.task import Task

    pid = _new_project(client, name="Legacy").json()["id"]
    db_session.add(
        Task(project_id=pid, title="เก่า", depends_on=[], tokens_input=900, tokens_output=300)
    )
    db_session.commit()

    body = client.get(f"/api/projects/{pid}/usage").json()

    assert body["by_provider"] == []
    assert body["untracked"]["input"] == 900 and body["untracked"]["output"] == 300


def test_project_usage_404_for_missing_project(client):
    assert client.get("/api/projects/00000000-0000-0000-0000-000000000000/usage").status_code == 404


def test_tasks_for_missing_project_404(client):
    resp = client.get("/api/projects/00000000-0000-0000-0000-000000000009/tasks")
    assert resp.status_code == 404


def test_get_project(client):
    pid = _new_project(client, name="รายละเอียด").json()["id"]
    resp = client.get(f"/api/projects/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "รายละเอียด"
    assert body["ceo_task_id"] is None  # โปรเจกต์ที่สร้างเอง ไม่ได้มาจาก d_CEO


def test_get_missing_project_404(client):
    resp = client.get("/api/projects/00000000-0000-0000-0000-000000000009")
    assert resp.status_code == 404
