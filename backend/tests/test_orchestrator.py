"""Orchestrator E2E: happy path, revision loop, escalation (Sprint 2 DoD)."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.agents.runtime import ReviewResult
from app.constants import MAX_REVISIONS, AgentRole
from app.models.agent_message import AgentMessage
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.engine import run_project


class RejectingReviewer:
    """Executor ที่ reviewer ปฏิเสธ N ครั้งแรกแล้วค่อย approve (N=None -> ปฏิเสธตลอด)."""

    def __init__(self, reject_times: int | None = None) -> None:
        self.reject_times = reject_times
        self.reviews = 0

    def execute(self, task, role, feedback=None):
        return f"work v{self.reviews + 1}" + (f" (fixed: {feedback})" if feedback else "")

    def review(self, task, work):
        self.reviews += 1
        if self.reject_times is None or self.reviews <= self.reject_times:
            return ReviewResult(approved=False, comment=f"ยังไม่ผ่านรอบ {self.reviews}")
        return ReviewResult(approved=True, comment="ผ่านแล้ว")


def _project_with_planned_tasks(db, titles: list[str], deps: dict[str, list[int]] | None = None):
    project = Project(name="Run", type="new")
    db.add(project)
    db.flush()
    tasks = []
    for title in titles:
        t = Task(project_id=project.id, title=title, status="planned", depends_on=[])
        db.add(t)
        db.flush()
        tasks.append(t)
    # deps: {"title": [index ของ task ที่ต้องรอ]}
    for t in tasks:
        idxs = (deps or {}).get(t.title, [])
        t.depends_on = [str(tasks[i].id) for i in idxs]
    db.commit()
    return project, tasks


# ---------------------------------------------------------------------------
# Happy path — E2E ผ่าน API: breakdown -> confirm -> run -> ทุก task done
# ---------------------------------------------------------------------------
def test_e2e_happy_path_via_api(client):
    pid = client.post("/api/projects", json={"name": "E2E", "type": "new"}).json()["id"]
    client.post(f"/api/projects/{pid}/breakdown", json={"requirement": "Build feature X"})
    client.post(f"/api/projects/{pid}/confirm", json={})

    resp = client.post(f"/api/projects/{pid}/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["processed"] >= 1
    assert body["counts"] == {"done": body["processed"]}  # fallback reviewer approve เสมอ

    tasks = client.get(f"/api/projects/{pid}/tasks").json()["data"]
    assert all(t["status"] == "done" for t in tasks)
    assert all(t["assignee_type"] == "agent" for t in tasks)

    # ทุก task มีบทสนทนา agent อย่างน้อย handoff + result + review_comment
    for t in tasks:
        msgs = client.get(f"/api/tasks/{t['id']}/messages").json()["data"]
        types = [m["message_type"] for m in msgs]
        assert "handoff" in types and "result" in types and "review_comment" in types


def test_happy_path_audit_and_messages(db_session):
    project, tasks = _project_with_planned_tasks(db_session, ["Do A"])
    summary = run_project(db_session, project.id)

    assert summary.counts == {"done": 1}
    # ทุก state change มี audit record: planned->assigned->in_progress->review->done = 4
    audits = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "task.transition", AuditLog.entity_id == str(tasks[0].id)
        )
    ).scalars().all()
    assert len(audits) == 4
    # routing decision ถูก log (Risk #5)
    routed = db_session.execute(
        select(AuditLog).where(AuditLog.action == "task.routed")
    ).scalars().all()
    assert len(routed) == 1


# ---------------------------------------------------------------------------
# Revision loop — reject 1 ครั้งแล้วผ่าน → done, revision_count = 1
# ---------------------------------------------------------------------------
def test_revision_then_done(db_session):
    project, tasks = _project_with_planned_tasks(db_session, ["Do B"])
    executor = RejectingReviewer(reject_times=1)
    summary = run_project(db_session, project.id, executor=executor)

    task = db_session.get(Task, tasks[0].id)
    assert task.status == "done"
    assert task.revision_count == 1
    assert summary.outcomes[0].revisions == 1
    # review เกิด 2 รอบ → มี review_comment 2 ข้อความ
    comments = db_session.execute(
        select(AgentMessage).where(AgentMessage.message_type == "review_comment")
    ).scalars().all()
    assert len(comments) == 2


# ---------------------------------------------------------------------------
# Escalation — reject ตลอด → escalated ที่ revision_count = MAX_REVISIONS + แจ้งผู้ใช้
# ---------------------------------------------------------------------------
def test_escalation_after_max_revisions(db_session):
    project, tasks = _project_with_planned_tasks(db_session, ["Do C"])
    executor = RejectingReviewer(reject_times=None)  # ไม่ผ่านตลอด
    summary = run_project(db_session, project.id, executor=executor)

    task = db_session.get(Task, tasks[0].id)
    assert task.status == "escalated"
    assert task.revision_count == MAX_REVISIONS
    assert summary.counts == {"escalated": 1}

    # มีข้อความแจ้งผู้ใช้ (question broadcast)
    questions = db_session.execute(
        select(AgentMessage).where(AgentMessage.message_type == "question")
    ).scalars().all()
    assert len(questions) == 1
    assert questions[0].payload["escalated"] is True


# ---------------------------------------------------------------------------
# Dependencies — task ที่รอ dependency จะรันหลัง dependency เสร็จ
# ---------------------------------------------------------------------------
def test_dependency_ordering(db_session):
    project, tasks = _project_with_planned_tasks(
        db_session, ["Base", "Child"], deps={"Child": [0]}
    )
    summary = run_project(db_session, project.id)
    assert [o.title for o in summary.outcomes] == ["Base", "Child"]
    assert summary.counts == {"done": 2}


def test_dependent_of_escalated_task_stays_planned(db_session):
    project, tasks = _project_with_planned_tasks(
        db_session, ["Base", "Child"], deps={"Child": [0]}
    )
    executor = RejectingReviewer(reject_times=None)
    summary = run_project(db_session, project.id, executor=executor)

    # Base escalated → Child ยังไม่ถูกแตะ (deps ไม่ครบ)
    assert summary.counts == {"escalated": 1}
    child = db_session.get(Task, tasks[1].id)
    assert child.status == "planned"
