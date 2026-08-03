"""Orchestrator E2E: happy path, revision loop, escalation (Sprint 2 DoD)."""
from __future__ import annotations

from sqlalchemy import select

from app.agents.runtime import ReviewResult
from app.constants import MAX_REVISIONS
from app.models.agent_message import AgentMessage
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.task import Task
from app.orchestrator import engine
from app.orchestrator.engine import run_project


class RejectingReviewer:
    """Executor ที่ reviewer ปฏิเสธ N ครั้งแรกแล้วค่อย approve (N=None -> ปฏิเสธตลอด)."""

    def __init__(self, reject_times: int | None = None) -> None:
        self.reject_times = reject_times
        self.reviews = 0
        self.contexts: list[str | None] = []  # context ที่ orchestrator ส่งมาแต่ละครั้ง

    def execute(self, task, role, feedback=None, context=None):
        self.contexts.append(context)
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
def test_e2e_happy_path_via_api(client, wait_run):
    pid = client.post("/api/projects", json={"name": "E2E", "type": "new"}).json()["id"]
    client.post(f"/api/projects/{pid}/breakdown", json={"requirement": "Build feature X"})
    client.post(f"/api/projects/{pid}/confirm", json={})

    resp = client.post(f"/api/projects/{pid}/run")
    assert resp.status_code == 202  # งานเบื้องหลัง (Phase 2) — ตอบทันทีพร้อม run_id
    run = wait_run(resp.json()["run_id"])
    assert run.status == "succeeded"
    assert run.processed >= 1
    assert run.counts == {"done": run.processed}  # fallback reviewer approve เสมอ

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


# ---------------------------------------------------------------------------
# Upstream context — task ที่ depend อยู่ต้องได้ "ผลงานจริง" ของงานก่อนหน้าทั้งสาย
# (บั๊กจาก UAT 2026-08-03: agent เห็นแค่ title/spec ของตัวเอง งาน "รวมเล่ม" จึงทำไม่ได้)
# ---------------------------------------------------------------------------
class ContextSpy:
    """เก็บ context ที่ได้รับ + คืนผลงานที่ระบุตัวตนได้ว่ามาจาก task ไหน."""

    def __init__(self, work_by_title: dict[str, str] | None = None) -> None:
        self.work_by_title = work_by_title or {}
        self.seen: dict[str, str | None] = {}  # title -> context ครั้งแรกที่ถูกเรียก

    def execute(self, task, role, feedback=None, context=None):
        self.seen.setdefault(task.title, context)
        return self.work_by_title.get(task.title, f"ผลงานของ {task.title}")

    def review(self, task, work):
        return ReviewResult(approved=True, comment="ok")


def test_dependent_task_receives_whole_upstream_graph(db_session):
    # A → B → C : C ต้องเห็นผลงานของ **ทั้ง A และ B** ไม่ใช่แค่ B ที่เป็น dependency ตรง
    project, _ = _project_with_planned_tasks(
        db_session, ["A", "B", "C"], deps={"B": [0], "C": [1]}
    )
    spy = ContextSpy()
    run_project(db_session, project.id, executor=spy)

    assert spy.seen["A"] is None  # ไม่มีงานก่อนหน้า = ไม่ต้องมี context
    assert "ผลงานของ A" in spy.seen["B"]

    ctx_c = spy.seen["C"]
    assert "ผลงานของ A" in ctx_c and "ผลงานของ B" in ctx_c
    assert ctx_c.index("ผลงานของ A") < ctx_c.index("ผลงานของ B")  # เรียงตามลำดับแผน
    assert "ห้ามสมมติเนื้อหาเอง" in ctx_c  # สั่งชัดว่าห้ามใส่ placeholder


def test_context_uses_latest_work_after_revision(db_session):
    """งานที่ถูกแก้รอบสอง ต้องส่ง "ผลงานล่าสุด" ให้ตัวถัดไป ไม่ใช่ฉบับที่ถูกปฏิเสธ."""

    class ReviseOnce:
        def __init__(self) -> None:
            self.calls = 0
            self.seen: dict[str, str | None] = {}

        def execute(self, task, role, feedback=None, context=None):
            self.seen.setdefault(task.title, context)
            if task.title == "Base":
                self.calls += 1
                return f"ฉบับที่ {self.calls}"
            return "งานต่อยอด"

        def review(self, task, work):
            approved = not (task.title == "Base" and work == "ฉบับที่ 1")
            return ReviewResult(approved=approved, comment="แก้ก่อน")

    project, _ = _project_with_planned_tasks(
        db_session, ["Base", "Child"], deps={"Child": [0]}
    )
    executor = ReviseOnce()
    run_project(db_session, project.id, executor=executor)

    ctx = executor.seen["Child"]
    assert "ฉบับที่ 2" in ctx and "ฉบับที่ 1" not in ctx


def test_long_upstream_work_is_clipped_with_a_visible_marker(db_session):
    project, _ = _project_with_planned_tasks(db_session, ["Big", "Next"], deps={"Next": [0]})
    huge = "ก" * (engine.UPSTREAM_WORK_CHAR_LIMIT + 500)
    spy = ContextSpy({"Big": huge})
    run_project(db_session, project.id, executor=spy)

    ctx = spy.seen["Next"]
    assert len(ctx) < len(huge) + 500
    assert "ตัดเหลือ" in ctx  # ต้องบอกว่าถูกตัด ไม่ตัดเงียบ


def test_context_total_budget_drops_oldest_first(db_session, monkeypatch):
    # เพดานรวมเล็กจนใส่ได้แค่ชิ้นเดียว → ต้องเก็บตัวที่ใกล้ที่สุด (B) และทิ้ง A พร้อมบอกจำนวน
    monkeypatch.setattr(engine, "UPSTREAM_CONTEXT_CHAR_LIMIT", 60)
    project, _ = _project_with_planned_tasks(
        db_session, ["A", "B", "C"], deps={"B": [0], "C": [0, 1]}
    )
    spy = ContextSpy({"A": "ผ" * 50, "B": "ญ" * 20})
    run_project(db_session, project.id, executor=spy)

    ctx = spy.seen["C"]
    assert "ญ" * 20 in ctx  # ตัวใกล้ตัวเราถูกเก็บไว้
    assert "ตัดผลงานของงานเก่า 1 รายการ" in ctx
