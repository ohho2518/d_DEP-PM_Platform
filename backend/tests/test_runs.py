"""รอบรัน orchestrator แบบเบื้องหลัง (Phase 2): 202 + run_id, progress, lock 409, failed path.

`run_project` ของจริงถูกทดสอบไว้แล้วใน `test_orchestrator.py` — ที่นี่สนใจ **การจัดการรอบรัน**
จึงสลับตัว engine ด้วย fake ที่คุมจังหวะได้ (monkeypatch ที่ `runs.run_project` ตรง ๆ
ไม่ mock HTTP/ไม่แตะ orchestrator — ตรงกติกา AI_AGENT_GUIDE)
"""
from __future__ import annotations

import threading

import pytest

from app.constants import RunStatus, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.engine import TaskOutcome
from app.services import runs


def _project_with_planned(db, count: int = 2) -> Project:
    project = Project(name="รอบรัน", type="new")
    db.add(project)
    db.flush()
    for i in range(count):
        db.add(
            Task(project_id=project.id, title=f"งาน {i + 1}", status=TaskStatus.PLANNED.value)
        )
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture()
def gated_engine(monkeypatch):
    """แทน engine ด้วย fake ที่หยุดรอสัญญาณ — ทำให้ทดสอบสถานะ "กำลังรัน" ได้แน่นอน."""

    class Gate:
        def __init__(self) -> None:
            self.started = threading.Event()
            self.release = threading.Event()
            self.outcomes: list[TaskOutcome] = []

        def _fake_run(self, db, project_id, *, on_outcome=None, **kwargs):
            for outcome in self.outcomes:
                if on_outcome is not None:
                    on_outcome(outcome)
            self.started.set()
            self.release.wait(10)

    gate = Gate()
    monkeypatch.setattr(runs, "run_project", gate._fake_run)
    try:
        yield gate
    finally:
        gate.release.set()  # ปล่อย thread เสมอ แม้ assertion จะพังกลางทาง


# --- 202 + run_id ------------------------------------------------------------


def test_run_returns_202_with_run_id_and_target_total(client, db_session, wait_run):
    project = _project_with_planned(db_session, count=2)

    resp = client.post(f"/api/projects/{project.id}/run")
    assert resp.status_code == 202
    body = resp.json()
    assert body["run_id"]
    assert body["project_id"] == str(project.id)
    assert body["total"] == 2  # นับ task ที่ planned ตอนเริ่มรอบ
    assert body["status"] in {RunStatus.RUNNING.value, RunStatus.SUCCEEDED.value}

    run = wait_run(body["run_id"])
    assert run.status == RunStatus.SUCCEEDED.value
    assert run.processed == 2
    assert run.counts == {TaskStatus.DONE.value: 2}


def test_run_on_missing_project_is_404(client):
    resp = client.post("/api/projects/11111111-1111-1111-1111-111111111111/run")
    assert resp.status_code == 404


# --- progress ----------------------------------------------------------------


def test_progress_visible_while_running(client, db_session, gated_engine, wait_run):
    project = _project_with_planned(db_session, count=2)
    gated_engine.outcomes = [
        TaskOutcome(task_id="t-1", title="งาน 1", final_status=TaskStatus.DONE.value, revisions=0)
    ]

    run_id = client.post(f"/api/projects/{project.id}/run").json()["run_id"]
    assert gated_engine.started.wait(10)

    body = client.get(f"/api/projects/{project.id}/run").json()
    assert body["run_id"] == run_id
    assert body["status"] == RunStatus.RUNNING.value
    assert body["processed"] == 1 and body["total"] == 2
    assert body["counts"] == {TaskStatus.DONE.value: 1}
    assert body["outcomes"][0]["title"] == "งาน 1"
    assert body["finished_at"] is None

    gated_engine.release.set()
    assert wait_run(run_id).status == RunStatus.SUCCEEDED.value

    done = client.get(f"/api/projects/{project.id}/run?run_id={run_id}").json()
    assert done["status"] == RunStatus.SUCCEEDED.value
    assert done["finished_at"] is not None


def test_progress_404_when_project_never_ran(client, db_session):
    project = _project_with_planned(db_session, count=1)
    assert client.get(f"/api/projects/{project.id}/run").status_code == 404


def test_progress_404_when_run_id_belongs_to_another_project(client, db_session, wait_run):
    mine = _project_with_planned(db_session, count=1)
    other = _project_with_planned(db_session, count=1)
    other_run = client.post(f"/api/projects/{other.id}/run").json()["run_id"]
    wait_run(other_run)

    resp = client.get(f"/api/projects/{mine.id}/run?run_id={other_run}")
    assert resp.status_code == 404


# --- lock ต่อโปรเจกต์ (Risk #3) ------------------------------------------------


def test_second_run_on_same_project_is_409(client, db_session, gated_engine, wait_run):
    project = _project_with_planned(db_session, count=1)

    first = client.post(f"/api/projects/{project.id}/run").json()
    assert gated_engine.started.wait(10)

    conflict = client.post(f"/api/projects/{project.id}/run")
    assert conflict.status_code == 409
    assert first["run_id"] in conflict.json()["detail"]  # บอกด้วยว่าไปดูรอบไหน

    gated_engine.release.set()
    wait_run(first["run_id"])
    # จบแล้วต้องรันใหม่ได้ (lock ถูกปลด)
    assert client.post(f"/api/projects/{project.id}/run").status_code == 202


def test_lock_is_per_project_not_global(client, db_session, gated_engine, wait_run):
    first = _project_with_planned(db_session, count=1)
    second = _project_with_planned(db_session, count=1)

    first_run = client.post(f"/api/projects/{first.id}/run").json()["run_id"]
    assert gated_engine.started.wait(10)
    assert client.post(f"/api/projects/{second.id}/run").status_code == 202

    gated_engine.release.set()
    wait_run(first_run)


# --- failed path -------------------------------------------------------------


def test_failed_run_keeps_error_and_releases_lock(client, db_session, monkeypatch, wait_run):
    project = _project_with_planned(db_session, count=1)

    def _boom(db, project_id, *, on_outcome=None, **kwargs):
        raise RuntimeError("จำลอง engine พังกลางทาง")

    monkeypatch.setattr(runs, "run_project", _boom)

    run_id = client.post(f"/api/projects/{project.id}/run").json()["run_id"]
    run = wait_run(run_id)
    assert run.status == RunStatus.FAILED.value
    assert "จำลอง engine พังกลางทาง" in run.error

    body = client.get(f"/api/projects/{project.id}/run").json()
    assert body["status"] == RunStatus.FAILED.value
    assert body["error"]
    # ล้มแล้วต้องไม่ค้าง lock ไว้ ไม่งั้นโปรเจกต์นั้นรันไม่ได้อีกเลยจนกว่าจะ restart
    assert client.post(f"/api/projects/{project.id}/run").status_code == 202
