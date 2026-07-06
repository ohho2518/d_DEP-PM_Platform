"""PM Agent breakdown + confirm-scope flow (Blueprint §6). Agent key is unset in tests,
so breakdown uses the deterministic fallback path — no network calls."""
from __future__ import annotations

from app.agents.pm import breakdown_requirement, _extract_json, _fallback_plan
from app.schemas.task import TaskPlan


def test_extract_json_from_fenced_block():
    text = 'here you go\n```json\n{"tasks": []}\n```\nthanks'
    assert _extract_json(text).strip() == '{"tasks": []}'


def test_fallback_plan_is_valid_taskplan():
    plan = _fallback_plan("Build a login page\nwith OAuth")
    assert isinstance(plan, TaskPlan)
    assert len(plan.tasks) == 1
    assert plan.tasks[0].title == "Build a login page"


def test_breakdown_without_key_uses_fallback():
    result = breakdown_requirement("Ship an MVP")
    assert result.source == "fallback"
    assert len(result.plan.tasks) == 1


def test_breakdown_endpoint_persists_backlog_tasks(client):
    pid = client.post("/api/projects", json={"name": "P", "type": "new"}).json()["id"]
    resp = client.post(f"/api/projects/{pid}/breakdown", json={"requirement": "Build X"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "fallback"
    assert len(body["tasks"]) >= 1
    assert all(t["status"] == "backlog" for t in body["tasks"])


def test_confirm_scope_moves_backlog_to_planned(client):
    pid = client.post("/api/projects", json={"name": "P", "type": "new"}).json()["id"]
    client.post(f"/api/projects/{pid}/breakdown", json={"requirement": "Build X"})

    confirm = client.post(f"/api/projects/{pid}/confirm", json={})
    assert confirm.status_code == 200
    assert all(t["status"] == "planned" for t in confirm.json()["data"])

    # All backlog tasks should now be planned.
    tasks = client.get(f"/api/projects/{pid}/tasks").json()["data"]
    assert all(t["status"] == "planned" for t in tasks)


def test_dependency_refs_resolve_to_uuids(client, db_session):
    from app.services.tasks import persist_task_plan
    from app.models.project import Project
    from app.schemas.task import PlannedTask

    project = Project(name="Dep", type="new")
    db_session.add(project)
    db_session.commit()

    plan = TaskPlan(
        tasks=[
            PlannedTask(ref="T1", title="Base"),
            PlannedTask(ref="T2", title="Depends on T1", depends_on=["T1"]),
        ]
    )
    created = persist_task_plan(db_session, project.id, plan)
    t1, t2 = created
    assert t2.depends_on == [str(t1.id)]
    assert t1.depends_on == []
