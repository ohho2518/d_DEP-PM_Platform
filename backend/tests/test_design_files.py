"""ตัวอ่านไฟล์ดีไซน์ (ADR-05 S3) — บทเรียนที่ยกมาจาก new-project-studio ต้องไม่หายไปกับการย้าย."""
from __future__ import annotations

from app.services import design_files


def _design(tmp_path):
    folder = design_files.design_dir(tmp_path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def test_nulls_never_reach_the_requirement(tmp_path):
    r"""`\x00` ที่ติดมากับไฟล์ต้องถูกตัดก่อนไหลต่อ.

    pypdf คืน NUL ตรงตัวอักษรที่ font ไม่มี ToUnicode map (เจอบ่อยกับ PDF ไทย) ·
    ของเดิมพังตอนส่งเข้า subprocess ของ Windows · ที่นี่มันจะไหลเข้า prompt แล้วลง DB แทน
    ⇒ ตัดที่จุดเดียวกันคือตอน extract · **ตรวจกับไฟล์จริงแล้ว** (`autopost-studio-mockup.pdf`
    มี NUL 18 ตัว → requirement ออกมา 0 ตัว, 2026-08-14)
    """
    folder = _design(tmp_path)
    (folder / "โจทย์.txt").write_text("ก่อน\x00หลัง", encoding="utf-8")

    requirement = design_files.build_requirement(tmp_path)

    assert "\x00" not in requirement
    assert "ก่อนหลัง" in requirement


def test_image_says_it_cannot_be_read_instead_of_guessing(tmp_path):
    """ห้ามเดาเนื้อหาจากชื่อไฟล์ — เป็นกติกาห้ามกุหลักฐานเวอร์ชันของชั้นนี้."""
    folder = _design(tmp_path)
    (folder / "mockup-หน้าจอ-login.png").write_bytes(b"\x89PNG")

    requirement = design_files.build_requirement(tmp_path)

    assert "ระบบอ่านเนื้อหาไม่ได้" in requirement
    assert "ต้องให้คนอธิบายเพิ่ม" in requirement


def test_oversized_file_is_clipped_with_a_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(design_files, "PER_FILE_CHAR_LIMIT", 50)
    folder = _design(tmp_path)
    (folder / "ยาว.md").write_text("ก" * 500, encoding="utf-8")

    requirement = design_files.build_requirement(tmp_path)

    assert "(ตัดเหลือ 50 ตัวอักษรแรก)" in requirement  # ตัดแล้วต้องบอก ไม่ใช่ตัดเงียบ


def test_files_beyond_the_total_budget_are_named_not_dropped_silently(tmp_path, monkeypatch):
    monkeypatch.setattr(design_files, "TOTAL_CHAR_LIMIT", 120)
    folder = _design(tmp_path)
    (folder / "a.md").write_text("ก" * 100, encoding="utf-8")
    (folder / "b.md").write_text("ข" * 100, encoding="utf-8")

    requirement = design_files.build_requirement(tmp_path)

    assert "b.md" in requirement  # บอกชื่อไฟล์ที่ยังไม่ได้อ่าน
    assert "เกินเพดาน" in requirement


def test_uploads_cannot_escape_the_design_folder(tmp_path):
    """ชื่อไฟล์ที่ browser ส่งมาอาจมี path ติดมา — ต้องเหลือแค่ชื่อไฟล์."""
    saved = design_files.save_uploads(tmp_path, [("../../หนีออกไป.md", b"x")])

    assert saved == ["หนีออกไป.md"]
    assert (design_files.design_dir(tmp_path) / "หนีออกไป.md").is_file()
    assert not (tmp_path.parent.parent / "หนีออกไป.md").exists()


def test_no_design_files_means_just_the_note(tmp_path):
    assert design_files.build_requirement(tmp_path, note="เล่าปากเปล่า") == "เล่าปากเปล่า"
