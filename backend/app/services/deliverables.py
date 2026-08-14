"""เขียน "ผลงานของ task" ลงไฟล์จริงในโฟลเดอร์โปรเจกต์ (ADR-05 S3).

**ทำไมต้องมีขั้นนี้:** agent ของเราคืน *ข้อความ* เท่านั้น (ทุก LLM call ผ่าน `providers.py`
ซึ่งไม่มี tool เขียนไฟล์ — AGENTS.md §9.1.13) · การเอาผลงานไปเป็นไฟล์จึงเป็นขั้น
deterministic ที่คนสั่งเอง ไม่ใช่สิ่งที่ agent ทำเองเงียบ ๆ

กติกาบังคับของไฟล์นี้:
1. เขียนได้เฉพาะ**ใต้โฟลเดอร์ของโปรเจกต์นั้น** — path ที่หลุดออกไปถูกปฏิเสธ
2. **สำรองไฟล์เดิมก่อนทับเสมอ** (WORKING_RULES Rule 1) ลงที่ `BackUp/` ของโปรเจกต์ปลายทาง
3. เขียน UTF-8 **ไม่มี BOM** และขึ้นบรรทัดด้วย ``\\n`` (WORKING_RULES §6.1ข)
4. **ไม่ commit ให้** — คนตรวจแล้ว commit เอง (เจตนาเดียวกับ new-project-studio)
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.bus import latest_work_by_task
from app.models.task import Task


class DeliverableError(RuntimeError):
    """เขียนไฟล์ไม่ได้ด้วยเหตุที่ผู้ใช้แก้ได้ — router แปลงเป็น 400."""


def _resolve_inside(project_dir: Path, relative_path: str) -> Path:
    """คืน path เต็มที่ยืนยันแล้วว่าอยู่ใต้ ``project_dir`` จริง (กัน ``..`` และ path เต็ม)."""
    candidate = (project_dir / relative_path).resolve()
    root = project_dir.resolve()
    if root != candidate and root not in candidate.parents:
        raise DeliverableError(
            f"เขียนได้เฉพาะใต้โฟลเดอร์ของโปรเจกต์ ({root}) — ได้ {candidate}"
        )
    if candidate.is_dir():
        raise DeliverableError(f"{relative_path} เป็นโฟลเดอร์ ไม่ใช่ไฟล์")
    return candidate


def backup_existing(project_dir: Path, path: Path) -> str | None:
    """สำเนาไฟล์เดิมไว้ก่อนเขียนทับ — คืน path ของสำเนา (None = ยังไม่มีไฟล์เดิม)."""
    if not path.is_file():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_dir / "BackUp" / f"Deliverable_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / path.name
    shutil.copy2(path, target)
    return str(target)


def write_task_work_product(db: Session, task: Task, project_dir: Path, relative_path: str) -> dict:
    """เอาผลงาน**ฉบับล่าสุด**ของ task ไปเขียนที่ ``relative_path`` ใต้โฟลเดอร์โปรเจกต์.

    ผลงานอ่านจาก Message Bus (ที่เดียวที่เก็บตัวชิ้นงานจริง — ADR-03) ไม่ใช่จากช่องอื่น
    """
    works = latest_work_by_task(db, [task.id])
    work = works.get(task.id, "").strip()
    if not work:
        raise DeliverableError(
            f"task '{task.title}' ยังไม่มีผลงานให้เขียน — ต้องรันจนมีข้อความจาก agent ก่อน"
        )

    path = _resolve_inside(project_dir, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_existing(project_dir, path)
    path.write_text(work if work.endswith("\n") else work + "\n", encoding="utf-8", newline="\n")

    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "backup": backup,
        "task_id": str(task.id),
    }
