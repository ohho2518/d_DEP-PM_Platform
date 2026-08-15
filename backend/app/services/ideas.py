"""ดึง "ไอเดีย" ที่กองอยู่ในดิสก์เข้ามาอยู่บนบอร์ด (ชนิดงาน ``idea``).

ที่มา: ก่อนมีระบบนี้ ไอเดียถูกเก็บเป็นไฟล์กระจายอยู่หลายโฟลเดอร์ ไม่มีใครรู้ว่ามีกี่อัน
อันไหนถูกหยิบไปทำแล้ว — พอบอร์ดรับรู้ไอเดียเป็นชนิดงานหนึ่ง ของเก่าจึงต้องตามเข้ามาด้วย
(มติผู้ใช้ 2026-08-15) ไม่งั้นบอร์ดจะเล่าความจริงได้แค่ครึ่งเดียว

กติกาที่ยึด:

* **อ่านอย่างเดียว** — ไม่ย้าย ไม่แก้ ไม่ลบไฟล์ต้นทางแม้แต่ไบต์เดียว
* **ยิงซ้ำได้** — ของที่ดึงเข้ามาแล้วจะถูกข้าม (เทียบด้วยชื่อในกลุ่มโปรเจกต์ชนิด idea)
* **ไฟล์ชื่อเดียวกันหลายนามสกุลนับเป็นไอเดียเดียว** — `เรื่องเดียวกัน.md` + `เรื่องเดียวกัน.html`
  คือฉบับ markdown กับฉบับเปิดในเบราว์เซอร์ของสิ่งเดียวกัน (เจอจริงทั้งสองโฟลเดอร์)
* **ไอเดียที่เป็นไฟล์เดี่ยวไม่ผูก `local_path`** — โฟลเดอร์ต้นทางเป็นของรวม ถ้าผูกไว้จะกลายเป็น
  ใบอนุญาตให้เขียนไฟล์ทับของคนอื่นในโฟลเดอร์เดียวกัน (รั้วของ ADR-05 ต้องแคบเสมอ)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import ProjectKind, ProjectStatus, ProjectType
from app.models.project import Project

#: นามสกุลที่ถือว่าเป็น "ไอเดียที่เขียนไว้แล้ว"
IDEA_SUFFIXES = {".md", ".html", ".txt", ".docx", ".pdf"}

#: ไฟล์/โฟลเดอร์ที่ไม่ใช่ไอเดีย — ข้ามเงียบ ๆ
_SKIP_NAMES = {"readme.md", "readme.html", "index.md", "icon", "desktop.ini", "thumbs.db"}
_SKIP_PREFIXES = (".", "_")


@dataclass(frozen=True)
class IdeaCandidate:
    """ไอเดียหนึ่งเรื่องที่เจอในดิสก์ (ยังไม่ได้ดึงเข้าบอร์ด)."""

    name: str
    #: โฟลเดอร์ต้นทางที่เจอ — บอกให้คนรู้ว่ามาจากไหน
    source_root: str
    #: path ของไฟล์/โฟลเดอร์จริง (ไฟล์หลายนามสกุลของเรื่องเดียวกันจะอยู่ใน `files`)
    files: tuple[str, ...]
    is_folder: bool
    updated: str

    @property
    def local_path(self) -> str | None:
        """ผูกโฟลเดอร์ให้เฉพาะไอเดียที่ *เป็นโฟลเดอร์ของตัวเอง* — ไฟล์เดี่ยวคืน None."""
        return self.files[0] if self.is_folder else None


def idea_roots() -> list[Path]:
    """โฟลเดอร์ที่ไปตามหาไอเดีย — ตั้งได้ที่ `IDEA_ROOTS` (คั่นด้วย ;)."""
    raw = get_settings().idea_roots
    return [Path(p.strip()) for p in raw.split(";") if p.strip()]


def _mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).date().isoformat()
    except OSError:
        return ""


def _skip(name: str) -> bool:
    return name.lower() in _SKIP_NAMES or name.startswith(_SKIP_PREFIXES)


def scan(roots: list[Path] | None = None) -> list[IdeaCandidate]:
    """หาไอเดียทั้งหมดในโฟลเดอร์ต้นทาง — **อ่านอย่างเดียว** · โฟลเดอร์ที่ไม่มีอยู่ถูกข้าม."""
    found: list[IdeaCandidate] = []
    for root in roots if roots is not None else idea_roots():
        if not root.is_dir():
            continue
        # ไฟล์เดี่ยว: รวมนามสกุลต่าง ๆ ของชื่อเดียวกันเป็นเรื่องเดียว
        by_stem: dict[str, list[Path]] = {}
        for entry in sorted(root.iterdir()):
            if _skip(entry.name):
                continue
            if entry.is_dir():
                found.append(
                    IdeaCandidate(
                        name=entry.name,
                        source_root=str(root),
                        files=(str(entry),),
                        is_folder=True,
                        updated=_mtime(entry),
                    )
                )
            elif entry.suffix.lower() in IDEA_SUFFIXES:
                by_stem.setdefault(entry.stem, []).append(entry)

        for stem, paths in by_stem.items():
            found.append(
                IdeaCandidate(
                    name=stem,
                    source_root=str(root),
                    files=tuple(str(p) for p in sorted(paths)),
                    is_folder=False,
                    updated=max((_mtime(p) for p in paths), default=""),
                )
            )
    return found


def _existing_idea_names(db: Session) -> set[str]:
    rows = db.execute(
        select(Project.name).where(Project.kind == ProjectKind.IDEA.value)
    ).scalars().all()
    return {name.strip().casefold() for name in rows}


def preview(db: Session, roots: list[Path] | None = None) -> dict:
    """ดูก่อนดึง — บอกว่าจะได้อะไรใหม่บ้าง และอะไรมีอยู่แล้ว (ไม่เขียนอะไรทั้งสิ้น)."""
    existing = _existing_idea_names(db)
    candidates = scan(roots)
    new = [c for c in candidates if c.name.strip().casefold() not in existing]
    return {
        "roots": [str(r) for r in (roots if roots is not None else idea_roots())],
        "found": len(candidates),
        "already_on_board": len(candidates) - len(new),
        "items": [
            {
                "name": c.name,
                "source_root": c.source_root,
                "files": list(c.files),
                "is_folder": c.is_folder,
                "updated": c.updated,
            }
            for c in new
        ],
    }


def import_ideas(
    db: Session, roots: list[Path] | None = None, names: list[str] | None = None
) -> list[Project]:
    """สร้างโปรเจกต์ชนิด ``idea`` จากไอเดียที่ยังไม่อยู่บนบอร์ด — **ไม่ commit** (router จัดการ).

    ``names`` = เลือกเฉพาะบางเรื่อง (ไม่ส่ง = เอาทั้งหมดที่ยังไม่มี)
    """
    existing = _existing_idea_names(db)
    wanted = {n.strip().casefold() for n in names} if names else None
    created: list[Project] = []

    for candidate in scan(roots):
        key = candidate.name.strip().casefold()
        if key in existing:
            continue
        if wanted is not None and key not in wanted:
            continue
        project = Project(
            name=candidate.name[:200],
            type=ProjectType.NEW.value,
            kind=ProjectKind.IDEA.value,
            status=ProjectStatus.PLANNING.value,
            local_path=candidate.local_path,
        )
        db.add(project)
        created.append(project)
        existing.add(key)  # กันชื่อซ้ำภายในรอบเดียวกัน (2 รากมีชื่อเดียวกันได้)
    db.flush()
    return created
