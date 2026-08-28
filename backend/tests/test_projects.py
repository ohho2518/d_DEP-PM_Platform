"""Project + task endpoint tests."""
from __future__ import annotations

from pathlib import Path

import pytest


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


# --- เปิดโปรเจกต์ใหม่ "ของจริง" (ADR-05 — ยก scaffold มาจาก new-project-studio) ---


@pytest.fixture
def scaffold_root(tmp_path, monkeypatch):
    """ให้ scaffold ลงใน tmp_path — **ห้ามแตะ D:\\Dev_Proj ของจริงตอนเทสต์**."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "scaffold_allowed_root", str(tmp_path))
    return tmp_path


def test_bootstrap_creates_the_folder_and_puts_it_on_the_board(client, scaffold_root):
    target = scaffold_root / "d_NewThing"

    resp = client.post(
        "/api/projects/bootstrap",
        json={
            "name": "d_NewThing",
            "target": str(target),
            "purpose": "ทดสอบการเปิดโปรเจกต์จริง",
            "stack": "Python + FastAPI",
            "relation": "product",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    # 1) ของจริงบนดิสก์
    assert (target / "AGENTS.md").is_file()
    assert (target / ".gitignore").is_file()
    assert (target / "requirements.txt").is_file()
    assert (target / ".git").is_dir()
    assert (target / "docs" / "API.md").is_file()  # relation=product → เอกสาร dev มาตรฐาน
    # 2) ลงบอร์ดให้ในคราวเดียว พร้อม task sign-off
    assert body["project"]["name"] == "d_NewThing"
    tasks = client.get(f"/api/projects/{body['project']['id']}/tasks").json()["data"]
    assert len(tasks) == 1 and tasks[0]["id"] == body["first_task_id"]
    assert str(target) in tasks[0]["description"]
    # 3) บอกคนอ่านว่าเกิดอะไรขึ้นบ้าง
    assert any("kit" in step for step in body["steps"])


def test_bootstrap_refuses_a_target_outside_the_allowed_root(client, scaffold_root, tmp_path):
    outside = tmp_path.parent / "ที่อื่นที่ไม่ได้อนุญาต"

    resp = client.post(
        "/api/projects/bootstrap", json={"name": "หลุดกรอบ", "target": str(outside)}
    )

    assert resp.status_code == 400
    assert not outside.exists()  # ต้องไม่แอบสร้างก่อนแล้วค่อยปฏิเสธ


def test_bootstrap_refuses_unknown_relation_before_touching_disk(client, scaffold_root):
    target = scaffold_root / "d_BadRelation"

    resp = client.post(
        "/api/projects/bootstrap",
        json={"name": "d_BadRelation", "target": str(target), "relation": "ไม่มีชั้นนี้"},
    )

    assert resp.status_code == 400
    assert not target.exists()
    assert client.get("/api/portfolio").json()["projects"] == []  # ไม่มี project ค้างบนบอร์ด


def test_bootstrap_keeps_the_kind_the_user_picked(client, scaffold_root):
    """เลือก "งานเอกสาร" แล้วต้องได้โปรเจกต์ `doc` — ไม่ใช่ `code` ตามค่าปริยาย.

    ชนิดงานเปลี่ยนเส้นทาง 6 ขั้น (`doc` ข้ามขั้นโครงสร้าง) ⇒ เดาแทนผู้ใช้ไม่ได้
    """
    resp = client.post(
        "/api/projects/bootstrap",
        json={
            "name": "d_คู่มือ",
            "target": str(scaffold_root / "d_Doc"),
            "kind": "doc",
            "relation": "general",
        },
    )

    assert resp.status_code == 201
    pid = resp.json()["project"]["id"]
    assert resp.json()["project"]["kind"] == "doc"
    assert client.get(f"/api/projects/{pid}/stages").json()["kind"] == "doc"


def test_bootstrap_defaults_to_code_like_before(client, scaffold_root):
    """ไม่ส่ง `kind` = `code` เหมือนเดิมทุกประการ (ของเก่าที่ยิงมาต้องไม่เปลี่ยนความหมาย)."""
    resp = client.post(
        "/api/projects/bootstrap",
        json={"name": "d_Default", "target": str(scaffold_root / "d_Default")},
    )

    assert resp.status_code == 201
    assert resp.json()["project"]["kind"] == "code"


def test_bootstrap_refuses_to_open_a_folder_for_an_idea(client, scaffold_root):
    """ไอเดียคือสิ่งที่ยัง**ไม่ลงมือ** — ขอโฟลเดอร์จริงให้มันไม่ได้ (ต้องไปทาง /promote)."""
    target = scaffold_root / "d_Idea"

    resp = client.post(
        "/api/projects/bootstrap",
        json={"name": "d_Idea", "target": str(target), "kind": "idea"},
    )

    assert resp.status_code == 422
    assert not target.exists()  # ปฏิเสธตั้งแต่ชั้น validate ยังไม่แตะดิสก์


def test_scaffold_options_reads_the_team_folders_off_the_disk(client, scaffold_root):
    """ฟอร์มต้องได้รายชื่อทีมจากของจริง — เพิ่มทีมใหม่แล้วเห็นเลยโดยไม่ต้องแก้โค้ด."""
    (scaffold_root / "4_RND").mkdir()
    (scaffold_root / "0_CORE").mkdir()
    (scaffold_root / "_INBOX").mkdir()
    (scaffold_root / "ไม่ใช่โฟลเดอร์ทีม").mkdir()

    body = client.get("/api/projects/scaffold-options").json()

    assert body["allowed_root"] == str(scaffold_root)
    assert [t["name"] for t in body["teams"]] == ["0_CORE", "4_RND", "_INBOX"]
    assert body["inbox"] == "_INBOX"
    assert body["teams"][1]["hint"]  # ทีมที่รู้จักต้องมีคำอธิบายให้คนเลือกถูก


def test_scaffold_options_survives_a_root_that_does_not_exist(client, monkeypatch, tmp_path):
    """รากที่ตั้งไว้หาย = ฟอร์มกลับไปพิมพ์ path เอง **ไม่ใช่หน้าเว็บพัง**."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "scaffold_allowed_root", str(tmp_path / "ไม่มีอยู่"))

    body = client.get("/api/projects/scaffold-options").json()

    assert body["teams"] == []


def test_commit_button_makes_the_first_commit(client, scaffold_root, monkeypatch):
    from app.services import scaffold as scaffold_service

    pid, folder = _bootstrap(client, scaffold_root, name="d_Commit")
    seen: list[Path] = []

    def fake_commit(target: Path) -> str:
        seen.append(target)
        return "git: commit แรกเรียบร้อย"

    # ไม่ยิง git จริง — commit ต้องมี identity ของเครื่อง เทสต์จึงจะแกว่งตามเครื่องที่รัน
    monkeypatch.setattr(scaffold_service, "git_commit_initial", fake_commit)

    resp = client.post(f"/api/projects/{pid}/commit")

    assert resp.status_code == 200
    assert resp.json()["detail"] == "git: commit แรกเรียบร้อย"
    assert seen == [folder]  # commit ในโฟลเดอร์ของโปรเจกต์นั้นเท่านั้น


def test_commit_refuses_a_project_without_a_folder(client):
    pid = _new_project(client, name="ไม่มีโฟลเดอร์").json()["id"]

    resp = client.post(f"/api/projects/{pid}/commit")

    assert resp.status_code == 400
    assert "bootstrap" in resp.json()["detail"]


# --- S3: ไฟล์ดีไซน์ + เขียนผลงานลงไฟล์จริง -----------------------------------


def _bootstrap(client, scaffold_root, name="d_S3"):
    resp = client.post(
        "/api/projects/bootstrap",
        json={"name": name, "target": str(scaffold_root / name), "relation": "product"},
    )
    return resp.json()["project"]["id"], scaffold_root / name


def test_design_files_land_in_the_project_and_become_a_requirement(client, scaffold_root):
    pid, folder = _bootstrap(client, scaffold_root)

    resp = client.post(
        f"/api/projects/{pid}/design-files",
        files=[
            ("files", ("โจทย์.md", "ต้องการระบบจองคิว 3 หน้าจอ".encode(), "text/markdown")),
            ("files", ("mockup.png", b"\x89PNG fake", "image/png")),
        ],
        data={"note": "ดีไซน์รอบแรกจากลูกค้า"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["saved"] == ["mockup.png", "โจทย์.md"] or set(body["saved"]) == {
        "mockup.png",
        "โจทย์.md",
    }
    assert (folder / "_design_input" / "โจทย์.md").is_file()
    # เนื้อความจากไฟล์ข้อความถูกดึงมา · รูปบอกตรง ๆ ว่าอ่านไม่ได้ (ไม่เดาเนื้อหาจากชื่อไฟล์)
    assert "ระบบจองคิว 3 หน้าจอ" in body["requirement"]
    assert "เป็นรูปภาพ — ระบบอ่านเนื้อหาไม่ได้" in body["requirement"]
    assert "ดีไซน์รอบแรกจากลูกค้า" in body["requirement"]


def test_design_upload_rejected_when_project_has_no_folder(client):
    pid = _new_project(client, name="ไม่มีโฟลเดอร์").json()["id"]

    resp = client.post(
        f"/api/projects/{pid}/design-files",
        files=[("files", ("a.md", b"x", "text/markdown"))],
    )

    assert resp.status_code == 400
    assert "bootstrap" in resp.json()["detail"]


def test_deliverable_writes_the_work_product_and_backs_up_what_it_replaces(
    client, db_session, scaffold_root
):
    from app.bus import publish
    from app.constants import MessageType
    from app.models.task import Task

    pid, folder = _bootstrap(client, scaffold_root, name="d_Deliverable")
    task = Task(project_id=pid, title="เขียน overview", depends_on=[])
    db_session.add(task)
    db_session.flush()
    publish(
        db_session,
        project_id=task.project_id,
        task_id=task.id,
        from_agent_id="dev",
        to_agent_id="reviewer",
        message_type=MessageType.RESULT,
        payload={"work": "# ภาพรวมโปรเจกต์\n\nเนื้อหาที่ agent เขียน"},
    )
    db_session.commit()

    resp = client.post(
        f"/api/projects/{pid}/deliverables",
        json={"task_id": str(task.id), "path": "docs/PROJECT_OVERVIEW.md"},
    )

    assert resp.status_code == 200
    written = folder / "docs" / "PROJECT_OVERVIEW.md"
    assert "เนื้อหาที่ agent เขียน" in written.read_text(encoding="utf-8")
    # ไฟล์เดิมจาก kit ต้องถูกสำรองไว้ก่อนทับ (WORKING_RULES Rule 1)
    backup = resp.json()["backup"]
    assert backup and Path(backup).is_file()
    assert written.read_bytes()[:3] != b"\xef\xbb\xbf"  # ไม่มี BOM


def test_deliverable_refuses_to_write_outside_the_project_folder(
    client, db_session, scaffold_root
):
    from app.bus import publish
    from app.constants import MessageType
    from app.models.task import Task

    pid, _ = _bootstrap(client, scaffold_root, name="d_Escape")
    task = Task(project_id=pid, title="งาน", depends_on=[])
    db_session.add(task)
    db_session.flush()
    publish(
        db_session,
        project_id=task.project_id,
        task_id=task.id,
        from_agent_id="dev",
        to_agent_id="reviewer",
        message_type=MessageType.RESULT,
        payload={"work": "ข้อความ"},
    )
    db_session.commit()

    resp = client.post(
        f"/api/projects/{pid}/deliverables",
        json={"task_id": str(task.id), "path": "../../หนีออกไปข้างนอก.md"},
    )

    assert resp.status_code == 400
    assert "เฉพาะใต้โฟลเดอร์ของโปรเจกต์" in resp.json()["detail"]


def test_deliverable_refuses_when_the_task_has_no_work_yet(client, db_session, scaffold_root):
    from app.models.task import Task

    pid, _ = _bootstrap(client, scaffold_root, name="d_NoWork")
    task = Task(project_id=pid, title="ยังไม่ได้ทำ", depends_on=[])
    db_session.add(task)
    db_session.commit()

    resp = client.post(
        f"/api/projects/{pid}/deliverables",
        json={"task_id": str(task.id), "path": "docs/x.md"},
    )

    assert resp.status_code == 400
    assert "ยังไม่มีผลงาน" in resp.json()["detail"]


# --- ลบโปรเจกต์ (ล้างงานทดสอบออกจากบอร์ด) -------------------------------------


def test_delete_project_removes_its_tasks_and_messages(client, db_session):
    from app.models.agent_message import AgentMessage
    from app.models.task import Task

    pid = _new_project(client, name="ทิ้งได้").json()["id"]
    client.post(f"/api/projects/{pid}/tasks", json={"title": "งานในโปรเจกต์ที่จะลบ"})
    client.post(
        "/api/agent-messages",
        json={
            "project_id": pid,
            "from_agent_id": "pm",
            "to_agent_id": "dev",
            "message_type": "handoff",
            "payload": {"note": "hi"},
        },
    )

    assert client.delete(f"/api/projects/{pid}").status_code == 204

    assert client.get(f"/api/projects/{pid}").status_code == 404
    assert db_session.query(Task).filter_by(project_id=pid).count() == 0
    assert db_session.query(AgentMessage).filter_by(project_id=pid).count() == 0


def test_delete_project_refuses_when_it_came_from_ceo(client, db_session):
    """งานที่รับมาจากเลขายังถูกอ้างจากฝั่งโน้น — ลบเงียบ ๆ = เลขาชี้ไปที่ของที่ไม่มีอยู่."""
    from app.models.project import Project

    pid = _new_project(client, name="งานจากเลขา").json()["id"]
    db_session.get(Project, pid).ceo_task_id = "4eb918bd-1675-4130-bed3-623392b6ed36"
    db_session.commit()

    resp = client.delete(f"/api/projects/{pid}")

    assert resp.status_code == 409
    assert "d_CEO" in resp.json()["detail"]
    assert client.get(f"/api/projects/{pid}").status_code == 200  # ยังอยู่ครบ


def test_delete_ceo_project_only_when_the_intent_is_written_out(client, db_session):
    """`?unlink_ceo=true` = พูดออกมาว่าตั้งใจตัดสาย — ใช้ตอนงานฝั่งเลขาปิดแล้ว."""
    from app.models.audit_log import AuditLog
    from app.models.project import Project

    pid = _new_project(client, name="งานเลขาที่ปิดแล้ว").json()["id"]
    db_session.get(Project, pid).ceo_task_id = "d89c03a8-0000-0000-0000-000000000000"
    db_session.commit()

    assert client.delete(f"/api/projects/{pid}").status_code == 409  # ไม่บอกเจตนา = ไม่ลบ
    assert client.delete(f"/api/projects/{pid}?unlink_ceo=true").status_code == 204

    # การตัดสายต้องมีร่องรอย ไม่ใช่หายไปเฉย ๆ
    actions = [a.action for a in db_session.query(AuditLog).all()]
    assert "project.ceo_link_removed" in actions


def test_delete_missing_project_404(client):
    assert client.delete("/api/projects/00000000-0000-0000-0000-000000000000").status_code == 404


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
