"""เส้นทาง 6 ขั้น + ชนิดงาน (code / doc / idea) — ก้อนที่ 1 ของการรื้อ UI 2026-08-15.

หัวใจที่ต้องไม่พัง: **ขั้นคำนวณจากของจริงเสมอ** ไม่มีคอลัมน์ให้ใครกดอัปเดตเอง
⇒ เทสต์ที่นี่จึงสร้าง "ของจริง" (โฟลเดอร์ · task · deployment) แล้ววัดว่าขั้นขยับตาม
"""
from __future__ import annotations

import pytest

from app.constants import DeploymentStatus, ProjectKind, ProjectStage, TaskStatus
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.task import Task
from app.services import stages


def _project(db, *, kind=ProjectKind.CODE, local_path=None, name="โปรเจกต์") -> Project:
    project = Project(name=name, type="new", kind=kind.value, local_path=local_path)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _task(db, project, status=TaskStatus.BACKLOG, title="งาน") -> Task:
    task = Task(project_id=project.id, title=title, status=status.value, depends_on=[])
    db.add(task)
    db.commit()
    return task


# --- ขั้นขยับตามของจริง -------------------------------------------------------


def test_new_project_sits_at_the_idea_stage(db_session):
    """ยังไม่มีอะไรเลย = ยังอยู่ขั้นแรก และบอกให้ไปเล่าโจทย์ก่อน."""
    result = stages.project_stages(db_session, _project(db_session))

    assert result["current"] == ProjectStage.IDEA.value
    assert result["stages"][0]["state"] == "current"
    assert "โจทย์" in result["next_action"]


def test_folder_on_disk_moves_past_structure(db_session):
    result = stages.project_stages(db_session, _project(db_session, local_path=r"D:\Dev_Proj\x"))

    by_stage = {s["stage"]: s["state"] for s in result["stages"]}
    assert by_stage[ProjectStage.IDEA.value] == "done"
    assert by_stage[ProjectStage.STRUCTURE.value] == "done"
    assert result["current"] == ProjectStage.PLAN.value


def test_backlog_only_means_scope_not_confirmed_yet(db_session):
    """มี task แต่ยังกอง backlog = แผนยังไม่ถูกยืนยัน — ต้องยังไม่ข้ามขั้นแผนงาน."""
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project)

    result = stages.project_stages(db_session, project)

    assert result["current"] == ProjectStage.PLAN.value
    assert "ยืนยัน scope" in result["next_action"]


def test_confirmed_scope_moves_to_build(db_session):
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project, TaskStatus.PLANNED)

    result = stages.project_stages(db_session, project)

    assert result["current"] == ProjectStage.BUILD.value
    assert "เหลืออีก 1 งาน" in result["next_action"]


def test_all_tasks_done_moves_to_ship(db_session):
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project, TaskStatus.DONE)

    result = stages.project_stages(db_session, project)

    assert result["current"] == ProjectStage.SHIP.value


def test_escalated_task_does_not_block_ship(db_session):
    """งานที่ยกให้คนแล้วไม่ใช่ "งานค้างของ agent" — ไม่งั้นโปรเจกต์จะติดขั้นลงมือตลอดกาล."""
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project, TaskStatus.DONE)
    _task(db_session, project, TaskStatus.ESCALATED, title="รอคนตัดสิน")

    assert stages.project_stages(db_session, project)["current"] == ProjectStage.SHIP.value


def test_successful_deployment_moves_to_marketing(db_session):
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project, TaskStatus.DONE)
    db_session.add(
        Deployment(project_id=project.id, status=DeploymentStatus.SUCCESS.value, environment="staging")
    )
    db_session.commit()

    result = stages.project_stages(db_session, project)

    assert result["current"] == ProjectStage.MARKET.value
    assert "d_MOS" in result["next_action"]  # ยังไม่เปิดใช้ ต้องบอกตรง ๆ


def test_failed_deployment_does_not_count_as_shipped(db_session):
    project = _project(db_session, local_path=r"D:\Dev_Proj\x")
    _task(db_session, project, TaskStatus.DONE)
    db_session.add(Deployment(project_id=project.id, status=DeploymentStatus.FAILED.value))
    db_session.commit()

    assert stages.project_stages(db_session, project)["current"] == ProjectStage.SHIP.value


# --- ชนิดงานเปลี่ยนเส้นทาง ------------------------------------------------------


def test_document_work_skips_the_structure_stage(db_session):
    result = stages.project_stages(db_session, _project(db_session, kind=ProjectKind.DOC))

    assert ProjectStage.STRUCTURE.value not in [s["stage"] for s in result["stages"]]


def test_document_work_renames_ship_to_delivery(db_session):
    """งานเอกสารไม่มี deploy — ขั้นที่ 5 ต้องอ่านว่า "ส่งมอบ" ไม่ใช่ "ส่งขึ้นระบบ"."""
    result = stages.project_stages(db_session, _project(db_session, kind=ProjectKind.DOC))
    ship = next(s for s in result["stages"] if s["stage"] == ProjectStage.SHIP.value)

    assert ship["label"] == "ส่งมอบ"


def test_document_work_ships_without_any_deployment(db_session):
    project = _project(db_session, kind=ProjectKind.DOC)
    _task(db_session, project, TaskStatus.DONE)

    result = stages.project_stages(db_session, project)

    # ไม่มี deployment เลย แต่ต้องข้ามขั้นส่งมอบได้ ไม่งั้นงานเอกสารจะค้างตลอดไป
    assert result["current"] == ProjectStage.MARKET.value


def test_idea_has_a_short_path_and_can_be_promoted_when_finished(db_session):
    project = _project(db_session, kind=ProjectKind.IDEA)
    _task(db_session, project, TaskStatus.DONE, title="หาคู่แข่งในตลาด")

    result = stages.project_stages(db_session, project)

    assert [s["stage"] for s in result["stages"]] == [
        ProjectStage.IDEA.value,
        ProjectStage.PLAN.value,
        ProjectStage.BUILD.value,
    ]
    assert result["ready_to_promote"] is True
    assert "ยกระดับ" in result["next_action"]


def test_idea_still_working_is_not_ready_to_promote(db_session):
    project = _project(db_session, kind=ProjectKind.IDEA)
    _task(db_session, project, TaskStatus.PLANNED)

    assert stages.project_stages(db_session, project)["ready_to_promote"] is False


# --- ผ่าน API -----------------------------------------------------------------


def test_stages_endpoint_returns_the_path(client, db_session):
    project = _project(db_session)
    body = client.get(f"/api/projects/{project.id}/stages").json()

    assert body["kind"] == ProjectKind.CODE.value
    assert len(body["stages"]) == 6
    assert body["current"] == ProjectStage.IDEA.value


def test_stages_endpoint_404_for_missing_project(client):
    assert (
        client.get("/api/projects/00000000-0000-0000-0000-000000000000/stages").status_code == 404
    )


def test_portfolio_carries_the_pipeline_of_every_project(client, db_session):
    """หน้ารวมต้องบอกได้ว่าโปรเจกต์ไหนติดตรงไหน โดยไม่ต้องเปิดเข้าไปทีละอัน."""
    _project(db_session, name="ก")
    _project(db_session, kind=ProjectKind.IDEA, name="ข")

    projects = client.get("/api/portfolio").json()["projects"]

    assert {p["kind"] for p in projects} == {ProjectKind.CODE.value, ProjectKind.IDEA.value}
    assert all(p["pipeline"]["next_action"] for p in projects)


def test_created_project_defaults_to_code_kind(client):
    """ของเดิมทั้งหมดต้องหมายความเหมือนเดิม — ไม่ส่ง kind = งานมีโค้ด."""
    body = client.post("/api/projects", json={"name": "ของเดิม", "type": "new"}).json()

    assert body["kind"] == ProjectKind.CODE.value


def test_can_create_a_document_project(client):
    body = client.post(
        "/api/projects", json={"name": "รายงานประจำไตรมาส", "type": "new", "kind": "doc"}
    ).json()

    assert body["kind"] == ProjectKind.DOC.value


# --- ยกระดับไอเดีย -------------------------------------------------------------


def test_promote_turns_an_idea_into_real_work_and_keeps_its_tasks(client, db_session):
    project = _project(db_session, kind=ProjectKind.IDEA, name="ERP งานรับสร้างบ้าน")
    _task(db_session, project, TaskStatus.DONE, title="ผลศึกษาคู่แข่ง")

    resp = client.post(f"/api/projects/{project.id}/promote", json={"kind": "doc"})

    assert resp.status_code == 200
    assert resp.json()["project"]["kind"] == ProjectKind.DOC.value
    # งานที่ศึกษาไว้ต้องอยู่ครบ — ยกระดับไม่ใช่การเริ่มใหม่
    assert client.get(f"/api/projects/{project.id}/tasks").json()["pagination"]["total"] == 1


def test_promote_writes_an_audit_trail(client, db_session):
    from app.models.audit_log import AuditLog

    project = _project(db_session, kind=ProjectKind.IDEA)
    client.post(f"/api/projects/{project.id}/promote", json={"kind": "code"})

    actions = [a.action for a in db_session.query(AuditLog).all()]
    assert "project.promoted" in actions


def test_promote_is_409_for_anything_that_is_not_an_idea(client, db_session):
    project = _project(db_session, kind=ProjectKind.CODE)

    resp = client.post(f"/api/projects/{project.id}/promote", json={"kind": "doc"})

    assert resp.status_code == 409
    assert "ไอเดีย" in resp.json()["detail"]


def test_promote_cannot_turn_something_back_into_an_idea(client, db_session):
    project = _project(db_session, kind=ProjectKind.IDEA)

    assert client.post(f"/api/projects/{project.id}/promote", json={"kind": "idea"}).status_code == 422


def test_promote_with_a_target_outside_the_allowed_root_is_rejected(client, db_session, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "scaffold_allowed_root", r"D:\Dev_Proj")
    project = _project(db_session, kind=ProjectKind.IDEA)

    resp = client.post(
        f"/api/projects/{project.id}/promote", json={"kind": "code", "target": r"C:\Windows\evil"}
    )

    assert resp.status_code == 400
    # ต้องไม่ยกระดับให้เมื่อสร้างโฟลเดอร์ไม่ได้ ไม่งั้นได้โปรเจกต์ code ที่ไม่มีบ้านอยู่
    assert client.get(f"/api/projects/{project.id}").json()["kind"] == ProjectKind.IDEA.value


@pytest.mark.parametrize("kind", ["code", "doc"])
def test_promote_without_target_only_changes_the_kind(client, db_session, kind):
    project = _project(db_session, kind=ProjectKind.IDEA)

    body = client.post(f"/api/projects/{project.id}/promote", json={"kind": kind}).json()

    assert body["target"] == ""
    assert body["created"] == []
    assert body["project"]["local_path"] is None
