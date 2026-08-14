"""อ่าน "ไฟล์ดีไซน์" ที่ผู้ใช้อัปโหลดเข้าโปรเจกต์ แล้วประกอบเป็น requirement ให้ PM แตกงาน.

ADR-05 S3 — ยกวิธีอ่านมาจาก `new-project-studio/app/ai_fill.py` (รีโปนั้นหยุดพัฒนาแล้ว)
พร้อมบทเรียนที่ฝังอยู่ในนั้น · **ต่างจากของเดิมตรงที่ไม่เรียก AI เอง** — หน้าที่ของไฟล์นี้คือ
เปลี่ยนไฟล์เป็นข้อความ แล้วส่งต่อให้ PM Agent ของบอร์ดแตกงานตามปกติ (ได้กติกาห้ามกุ + reviewer)

ไฟล์ดีไซน์อยู่ใน `<โปรเจกต์>/_design_input/` ซึ่ง `.gitignore` ของ kit กันไว้แล้ว —
เป็น **input อ่านอย่างเดียว** ไม่ใช่ของที่ต้องขึ้น repo
"""
from __future__ import annotations

from pathlib import Path

DESIGN_DIR = "_design_input"

#: เพดานข้อความต่อไฟล์ — ไฟล์ดีไซน์ใหญ่ ๆ (TOR 30 หน้า) ทำ prompt บวมจนค่าใช้จ่ายพุ่ง
PER_FILE_CHAR_LIMIT = 20_000
#: เพดานรวมทุกไฟล์ — ต่อจากนี้ตัดแล้ว **บอกว่าตัด** (เจตนาเดียวกับ `bus.clip_work`)
TOTAL_CHAR_LIMIT = 60_000

TEXT_SUFFIXES = {".md", ".txt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def strip_nulls(text: str) -> str:
    r"""ตัด NUL (``\x00``) ทิ้ง.

    `pypdf` คืน `\x00` ตรงตัวอักษรที่ font ไม่มี ToUnicode map — เจอบ่อยกับ PDF ไทย ·
    เนื้อหายังอ่านรู้เรื่อง แต่ NUL ที่ไหลต่อไปทำให้ปลายทางระเบิด (ของเดิมพังตอนส่งเข้า
    subprocess ของ Windows — ที่นี่กันไว้ที่จุดเดียวกันเพราะมันจะไหลเข้า prompt/DB แทน)
    """
    return text.replace("\x00", "") if text else text


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[อ่าน {path.name} ไม่ได้: {exc}]"


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return f"[ไม่ได้ติดตั้ง pypdf — อ่าน {path.name} ไม่ได้]"
    try:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 — ไฟล์เสียต้องไม่ล้มทั้งคำขอ
        return f"[อ่าน PDF {path.name} ไม่ได้: {exc}]"


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        return f"[ไม่ได้ติดตั้ง python-docx — อ่าน {path.name} ไม่ได้]"
    try:
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    except Exception as exc:  # noqa: BLE001
        return f"[อ่าน DOCX {path.name} ไม่ได้: {exc}]"


def _extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        text = _read_text(path)
    elif suffix == ".pdf":
        text = _read_pdf(path)
    elif suffix == ".docx":
        text = _read_docx(path)
    elif suffix in IMAGE_SUFFIXES:
        # ตั้งใจไม่เดาเนื้อหาจากชื่อไฟล์ — บอกตรง ๆ ว่าอ่านไม่ได้ ให้คนเป็นคนเล่าแทน
        return f"[{path.name} เป็นรูปภาพ — ระบบอ่านเนื้อหาไม่ได้ ต้องให้คนอธิบายเพิ่ม]"
    else:
        return f"[{path.name} เป็นไฟล์ชนิด {suffix or 'ไม่ทราบ'} ที่ยังไม่รองรับ]"

    text = strip_nulls(text).strip()
    if not text:
        return f"[{path.name} ไม่มีข้อความให้ดึง]"
    if len(text) > PER_FILE_CHAR_LIMIT:
        return f"{text[:PER_FILE_CHAR_LIMIT]}\n…(ตัดเหลือ {PER_FILE_CHAR_LIMIT:,} ตัวอักษรแรก)"
    return text


def design_dir(project_dir: Path) -> Path:
    return project_dir / DESIGN_DIR


def save_uploads(project_dir: Path, uploads: list[tuple[str, bytes]]) -> list[str]:
    """เก็บไฟล์ที่อัปโหลดลง ``_design_input/`` — คืนชื่อไฟล์ที่บันทึกจริง.

    ใช้เฉพาะชื่อไฟล์ (ตัด path ที่ติดมากับ browser ทิ้ง) เพื่อไม่ให้เขียนออกนอกโฟลเดอร์
    """
    target = design_dir(project_dir)
    target.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for filename, blob in uploads:
        safe = Path(filename).name.strip()
        if not safe:
            continue
        (target / safe).write_bytes(blob)
        saved.append(safe)
    return saved


def build_requirement(project_dir: Path, note: str = "") -> str:
    """ประกอบข้อความจากไฟล์ดีไซน์ทั้งหมด → ส่งให้ PM Agent แตกงานต่อ.

    หัวข้อของแต่ละไฟล์ระบุชื่อไฟล์ไว้เสมอ เพื่อให้ agent อ้างอิงกลับได้ว่าเอามาจากไหน
    (ตรงกับกติกาห้ามกุหลักฐาน — ต้องบอกได้ว่าข้อมูลมาจากแหล่งใด)
    """
    folder = design_dir(project_dir)
    if not folder.is_dir():
        return note.strip()

    parts: list[str] = []
    total = 0
    skipped: list[str] = []
    for path in sorted(p for p in folder.iterdir() if p.is_file()):
        chunk = f"\n=== {path.name} ===\n{_extract(path)}\n"
        if total + len(chunk) > TOTAL_CHAR_LIMIT:
            skipped.append(path.name)
            continue
        parts.append(chunk)
        total += len(chunk)

    if not parts:
        return note.strip()

    header = note.strip() + "\n\n" if note.strip() else ""
    body = "".join(parts)
    if skipped:
        body += (
            f"\n\n⚠️ ไฟล์ที่ยังไม่ได้อ่านเพราะเกินเพดาน {TOTAL_CHAR_LIMIT:,} ตัวอักษร: "
            f"{', '.join(skipped)} — ถ้าจำเป็นให้แยกทำเป็นรอบถัดไป"
        )
    return f"{header}--- เนื้อหาจากไฟล์ดีไซน์ที่แนบมา ---{body}"
