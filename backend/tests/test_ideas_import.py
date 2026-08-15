"""ดึงไอเดียเก่าจากดิสก์ขึ้นบอร์ด (มติผู้ใช้ 2026-08-15: "ของเก่าจะดึงเข้าบอร์ด").

สิ่งที่ต้องจริงเสมอ — ทั้งสามข้อนี้พังแล้วผู้ใช้เสียของจริง:

1. **ไม่แตะไฟล์ต้นทาง** (ไม่ย้าย ไม่แก้ ไม่ลบ)
2. **ยิงซ้ำแล้วไม่งอก** — กดปุ่มสองครั้งต้องไม่ได้ไอเดียซ้ำเต็มบอร์ด
3. **ไฟล์เดี่ยวไม่ผูก `local_path`** — โฟลเดอร์รวมเป็นของหลายคน ผูกไว้ = เปิดสิทธิ์เขียนทับกัน
"""
from __future__ import annotations

from app.constants import ProjectKind
from app.services import ideas


def _make_idea_folder(tmp_path):
    """จำลองของจริงบนเครื่อง: ไฟล์เดี่ยว · ไฟล์ชื่อซ้ำสองนามสกุล · โฟลเดอร์ · ของที่ต้องข้าม."""
    root = tmp_path / "IDEAs"
    root.mkdir()
    (root / "ระบบ ERP งานรับสร้างบ้าน.md").write_text("โจทย์", encoding="utf-8")
    (root / "Storytelling Master.md").write_text("a", encoding="utf-8")
    (root / "Storytelling Master.html").write_text("<p>a</p>", encoding="utf-8")
    (root / "README.md").write_text("อธิบายโฟลเดอร์", encoding="utf-8")
    (root / "Icon").write_text("", encoding="utf-8")
    (root / "_archive").mkdir()
    (root / "3D Cartoon Workflow").mkdir()
    return root


def test_scan_groups_same_name_different_suffix_as_one_idea(tmp_path):
    """`เรื่องเดียวกัน.md` + `.html` คือฉบับ markdown กับฉบับเปิดเบราว์เซอร์ของสิ่งเดียวกัน."""
    found = {c.name: c for c in ideas.scan([_make_idea_folder(tmp_path)])}

    assert "Storytelling Master" in found
    assert len(found["Storytelling Master"].files) == 2


def test_scan_skips_readme_icon_and_underscore_folders(tmp_path):
    names = {c.name for c in ideas.scan([_make_idea_folder(tmp_path)])}

    assert "README" not in names and "Icon" not in names and "_archive" not in names
    assert names == {"ระบบ ERP งานรับสร้างบ้าน", "Storytelling Master", "3D Cartoon Workflow"}


def test_scan_ignores_roots_that_do_not_exist(tmp_path):
    assert ideas.scan([tmp_path / "ไม่มีอยู่จริง"]) == []


def test_import_creates_idea_projects(client, db_session, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    created = client.post("/api/projects/ideas/import", json={}).json()

    assert len(created) == 3
    assert {p["kind"] for p in created} == {ProjectKind.IDEA.value}


def test_import_twice_does_not_duplicate(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    client.post("/api/projects/ideas/import", json={})
    second = client.post("/api/projects/ideas/import", json={}).json()

    assert second == []
    assert len(client.get("/api/portfolio").json()["projects"]) == 3


def test_folder_idea_gets_a_local_path_but_a_loose_file_does_not(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    by_name = {p["name"]: p for p in client.post("/api/projects/ideas/import", json={}).json()}

    assert by_name["3D Cartoon Workflow"]["local_path"] == str(root / "3D Cartoon Workflow")
    assert by_name["ระบบ ERP งานรับสร้างบ้าน"]["local_path"] is None


def test_import_leaves_the_source_files_untouched(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    client.post("/api/projects/ideas/import", json={})

    after = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    assert after == before


def test_import_can_take_only_the_names_you_picked(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    created = client.post(
        "/api/projects/ideas/import", json={"names": ["3D Cartoon Workflow"]}
    ).json()

    assert [p["name"] for p in created] == ["3D Cartoon Workflow"]


def test_preview_shows_what_is_new_without_writing_anything(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])

    body = client.get("/api/projects/ideas/preview").json()

    assert body["found"] == 3 and body["already_on_board"] == 0
    assert len(body["items"]) == 3
    assert client.get("/api/portfolio").json()["projects"] == []  # ยังไม่มีอะไรถูกสร้าง


def test_preview_marks_ideas_already_on_the_board(client, tmp_path, monkeypatch):
    root = _make_idea_folder(tmp_path)
    monkeypatch.setattr(ideas, "idea_roots", lambda: [root])
    client.post("/api/projects/ideas/import", json={"names": ["3D Cartoon Workflow"]})

    body = client.get("/api/projects/ideas/preview").json()

    assert body["already_on_board"] == 1
    assert "3D Cartoon Workflow" not in [i["name"] for i in body["items"]]


def test_two_roots_with_the_same_idea_name_import_once(client, tmp_path, monkeypatch):
    """ของจริงมี 2 โฟลเดอร์ — ชื่อชนกันได้ ต้องไม่ได้โปรเจกต์ซ้ำสองใบ."""
    a, b = tmp_path / "IDEAs", tmp_path / "KM_Ideas"
    a.mkdir(), b.mkdir()
    (a / "เรื่องเดียวกัน.md").write_text("x", encoding="utf-8")
    (b / "เรื่องเดียวกัน.md").write_text("y", encoding="utf-8")
    monkeypatch.setattr(ideas, "idea_roots", lambda: [a, b])

    created = client.post("/api/projects/ideas/import", json={}).json()

    assert len(created) == 1
