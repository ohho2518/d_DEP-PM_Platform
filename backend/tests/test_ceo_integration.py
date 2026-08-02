"""Phase 1 — รับงานจาก d_CEO และรายงานผลกลับ (AGENTS.md §3.1).

กติกา mocking ตาม AI_AGENT_GUIDE: **ไม่ mock HTTP** — inject stub client ผ่าน
FastAPI dependency override (`get_ceo_client`) แบบเดียวกับที่ orchestrator ใช้
`run_project(executor=…)`
"""
from __future__ import annotations

import uuid

import pytest

from app.constants import TaskStatus
from app.integrations.ceo_client import CeoClient, CeoTask, CeoUnavailable, get_ceo_client
from app.main import app
from app.models.project import Project
from app.models.task import Task

RND_TEAM_ID = "4406dde7-64ec-44b6-9139-4abc61b58aa6"
OTHER_TEAM_ID = "0b95b1a0-0781-45ac-b17d-fc1b596b6577"


def _ceo_task(task_id: str, text: str, team_id: str | None = RND_TEAM_ID) -> CeoTask:
    return CeoTask(
        id=task_id,
        input_text=text,
        assigned_team_id=team_id,
        status="queued",
        output=None,
        created_at="2026-08-02T10:00:00Z",
    )


class StubCeoClient:
    """แทน d_CEO — บันทึกทุก PATCH ไว้ตรวจว่าเราส่งอะไรกลับไปจริง."""

    base_url = "http://stub-ceo"

    def __init__(self, tasks: list[CeoTask] | None = None, *, online: bool = True) -> None:
        self.tasks = tasks or []
        self.online = online
        self.patches: list[dict] = []

    def _guard(self) -> None:
        if not self.online:
            raise CeoUnavailable("เชื่อมต่อ d_CEO ไม่ได้ (stub offline)")

    def health(self) -> bool:
        return self.online

    def list_teams(self) -> list[dict]:
        self._guard()
        return [
            {"id": RND_TEAM_ID, "name": "Research & Development"},
            {"id": OTHER_TEAM_ID, "name": "Quality Control & Knowledge Management"},
        ]

    def resolve_team_id(self, name: str) -> str | None:
        self._guard()
        for team in self.list_teams():
            if team["name"].casefold() == name.strip().casefold():
                return team["id"]
        return None

    def list_tasks(self, *, status: str = "queued", limit: int = 50) -> list[CeoTask]:
        self._guard()
        return [t for t in self.tasks if t.status == status][:limit]

    def patch_task(self, task_id: str, *, status: str | None = None, output: str | None = None):
        self._guard()
        self.patches.append({"task_id": task_id, "status": status, "output": output})
        return _ceo_task(task_id, "patched")


@pytest.fixture()
def stub_ceo(client):
    """ติดตั้ง stub เป็น dependency ของ /api/ceo/* — คืนตัว stub ให้ test ตรวจ."""
    stub = StubCeoClient()
    app.dependency_overrides[get_ceo_client] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_ceo_client, None)


# --- guardrail: ห้ามปิดงานฝั่ง d_CEO เอง -----------------------------------


def test_client_refuses_to_send_done_or_awaiting_approval():
    """มติ Vinit 2026-08-02 (เคส d_MOS): ระบบข้างเคียงส่งได้แค่ in_progress/qc_review."""
    ceo = CeoClient("http://127.0.0.1:9")  # ไม่มีการยิงจริง — ValueError เกิดก่อน
    for forbidden in ("done", "awaiting_approval", "rejected"):
        with pytest.raises(ValueError, match="QC gate"):
            ceo.patch_task("task-1", status=forbidden)


def test_client_requires_at_least_one_field():
    with pytest.raises(ValueError):
        CeoClient("http://127.0.0.1:9").patch_task("task-1")


# --- inbox ------------------------------------------------------------------


def test_inbox_returns_only_rnd_team_tasks(client, stub_ceo):
    stub_ceo.tasks = [
        _ceo_task("t-rnd", "แก้บั๊ก login"),
        _ceo_task("t-other", "ตรวจเอกสาร", team_id=OTHER_TEAM_ID),
        _ceo_task("t-none", "งานไม่ระบุทีม", team_id=None),
    ]
    body = client.get("/api/ceo/inbox").json()
    assert body["total"] == 1
    assert body["data"][0]["id"] == "t-rnd"


def test_inbox_skips_tasks_already_pulled(client, stub_ceo, db_session):
    db_session.add(Project(name="รับไปแล้ว", type="new", ceo_task_id="t-1"))
    db_session.commit()
    stub_ceo.tasks = [_ceo_task("t-1", "งานเก่า"), _ceo_task("t-2", "งานใหม่")]

    body = client.get("/api/ceo/inbox").json()
    assert [row["id"] for row in body["data"]] == ["t-2"]


def test_inbox_503_when_ceo_offline(client, stub_ceo):
    stub_ceo.online = False
    assert client.get("/api/ceo/inbox").status_code == 503


def test_endpoints_503_when_integration_disabled(client):
    """ไม่ override dependency = ceo_api_base ว่างตาม conftest → ปิดอยู่."""
    assert client.get("/api/ceo/inbox").status_code == 503
    assert client.post("/api/ceo/pull").status_code == 503

    status = client.get("/api/ceo/status").json()  # status ต้องไม่ 503 — UI ใช้ตัดสินใจ
    assert status == {
        "enabled": False,
        "online": False,
        "team_name": "Research & Development",
    }


def test_status_reports_online_and_waiting_count(client, stub_ceo):
    stub_ceo.tasks = [_ceo_task("t-1", "งานหนึ่ง"), _ceo_task("t-2", "งานสอง")]
    body = client.get("/api/ceo/status").json()
    assert body["enabled"] is True
    assert body["online"] is True
    assert body["team_id"] == RND_TEAM_ID
    assert body["waiting"] == 2


# --- pull -------------------------------------------------------------------


def test_pull_creates_project_breaks_down_and_acks(client, stub_ceo, db_session):
    stub_ceo.tasks = [_ceo_task("t-1", "ทำระบบจองคิว\nรายละเอียดเพิ่มเติม")]

    body = client.post("/api/ceo/pull").json()
    assert body["count"] == 1
    pulled = body["pulled"][0]
    assert pulled["ceo_task_id"] == "t-1"
    assert pulled["name"] == "ทำระบบจองคิว"  # ชื่อจากบรรทัดแรก
    assert pulled["task_count"] == 1  # ไม่มี key → fallback plan 1 task
    assert pulled["breakdown_source"] == "fallback"
    assert pulled["acknowledged"] is True

    project = db_session.get(Project, uuid.UUID(pulled["project_id"]))
    assert project.ceo_task_id == "t-1"
    # แจ้ง d_CEO ว่ารับงานแล้ว — ต้องเป็น in_progress เท่านั้น
    assert stub_ceo.patches == [{"task_id": "t-1", "status": "in_progress", "output": None}]


def test_pull_same_task_twice_does_not_duplicate(client, stub_ceo, db_session):
    stub_ceo.tasks = [_ceo_task("t-1", "งานเดียว")]
    assert client.post("/api/ceo/pull").json()["count"] == 1
    assert client.post("/api/ceo/pull").json()["count"] == 0

    projects = db_session.query(Project).filter(Project.ceo_task_id == "t-1").all()
    assert len(projects) == 1


def test_pull_can_select_specific_tasks(client, stub_ceo):
    stub_ceo.tasks = [_ceo_task("t-1", "งานหนึ่ง"), _ceo_task("t-2", "งานสอง")]
    body = client.post("/api/ceo/pull", json={"task_ids": ["t-2"]}).json()
    assert [p["ceo_task_id"] for p in body["pulled"]] == ["t-2"]


def test_pull_without_breakdown_creates_empty_project(client, stub_ceo):
    stub_ceo.tasks = [_ceo_task("t-1", "งานหนึ่ง")]
    pulled = client.post("/api/ceo/pull", json={"breakdown": False}).json()["pulled"][0]
    assert pulled["task_count"] == 0
    assert pulled["breakdown_source"] is None


# --- report -----------------------------------------------------------------


def _project_from_ceo(db_session, ceo_task_id: str = "t-1") -> Project:
    project = Project(name="งานจากเลขา", type="new", ceo_task_id=ceo_task_id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_report_400_when_project_not_from_ceo(client, stub_ceo, db_session):
    project = Project(name="โปรเจกต์ที่สร้างเอง", type="new")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    response = client.post(f"/api/ceo/report/{project.id}")
    assert response.status_code == 400
    assert stub_ceo.patches == []


def test_report_not_ready_while_tasks_still_running(client, stub_ceo, db_session):
    project = _project_from_ceo(db_session)
    db_session.add(Task(project_id=project.id, title="ยังทำอยู่", status=TaskStatus.PLANNED.value))
    db_session.commit()

    body = client.post(f"/api/ceo/report/{project.id}").json()
    assert body["ready"] is False
    assert body["reported"] is False
    assert stub_ceo.patches == []  # ห้ามรบกวน d_CEO ก่อนงานจบ


def test_report_sends_qc_review_with_summary(client, stub_ceo, db_session):
    project = _project_from_ceo(db_session)
    db_session.add_all(
        [
            Task(
                project_id=project.id,
                title="ออกแบบ schema",
                status=TaskStatus.DONE.value,
                tokens_input=100,
                tokens_output=50,
            ),
            Task(
                project_id=project.id,
                title="ต่อ CI",
                status=TaskStatus.ESCALATED.value,
                revision_count=2,
            ),
        ]
    )
    db_session.commit()

    body = client.post(f"/api/ceo/report/{project.id}").json()
    assert body["ready"] is True
    assert body["reported"] is True
    assert body["status_sent"] == "qc_review"

    assert len(stub_ceo.patches) == 1
    patch = stub_ceo.patches[0]
    assert patch["task_id"] == "t-1"
    assert patch["status"] == "qc_review"  # **ไม่ใช่ done** — ต้องผ่าน QC gate
    assert "ออกแบบ schema" in patch["output"]
    assert "ต่อ CI" in patch["output"]
    assert "escalated" in patch["output"]


def test_report_survives_ceo_going_offline(client, stub_ceo, db_session):
    project = _project_from_ceo(db_session)
    db_session.add(Task(project_id=project.id, title="เสร็จแล้ว", status=TaskStatus.DONE.value))
    db_session.commit()
    stub_ceo.online = False

    body = client.post(f"/api/ceo/report/{project.id}").json()
    assert body["ready"] is True
    assert body["reported"] is False  # บอกตรง ๆ ว่าส่งไม่ได้ แต่ไม่ 500
    assert "ส่งไม่สำเร็จ" in body["detail"]


# --- auto-report หลัง /run ---------------------------------------------------


def test_run_auto_reports_project_that_came_from_ceo(client, stub_ceo, db_session):
    project = _project_from_ceo(db_session)
    db_session.add(Task(project_id=project.id, title="งานเดียว", status=TaskStatus.PLANNED.value))
    db_session.commit()

    body = client.post(f"/api/projects/{project.id}/run").json()
    assert body["counts"] == {"done": 1}  # FallbackExecutor approve เสมอ
    assert body["ceo_report"]["reported"] is True
    assert stub_ceo.patches[-1]["status"] == "qc_review"


def test_run_on_normal_project_does_not_touch_ceo(client, stub_ceo, db_session):
    project = Project(name="โปรเจกต์ปกติ", type="new")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    db_session.add(Task(project_id=project.id, title="งาน", status=TaskStatus.PLANNED.value))
    db_session.commit()

    body = client.post(f"/api/projects/{project.id}/run").json()
    assert body["ceo_report"] is None
    assert stub_ceo.patches == []
