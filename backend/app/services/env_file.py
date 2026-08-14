"""อ่าน/เขียน `backend/.env` จากหน้า Settings — ที่เดียวในระบบที่แตะไฟล์นี้.

ทำไมต้องระวังเป็นพิเศษ (WORKING_RULES §6.1ข — เจอจริงบนเครื่องนี้):
`Set-Content -Encoding utf8` ของ PowerShell 5.1 ใส่ **BOM** ที่หัวไฟล์ ทำให้ key บรรทัดแรก
ของ `.env` อ่านไม่ออก แล้วแอปตกไปใช้ค่าปริยาย **เงียบ ๆ** (เคยทำให้ `STT_MODEL` เพี้ยนมาแล้ว)
⇒ ที่นี่เขียนด้วย UTF-8 ไม่มี BOM และ `\n` เสมอ · สำรองไฟล์เดิมก่อนเขียนทุกครั้ง (Rule 1)
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.config import get_settings

#: ชื่อตัวแปรใน `.env` -> ชื่อ field ใน `Settings` (มีเฉพาะตัวที่หน้า Settings แก้ได้)
ENV_TO_FIELD: dict[str, str] = {
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "CLAUDE_MODEL": "claude_model",
    "OPENAI_API_KEY": "openai_api_key",
    "OPENAI_MODEL": "openai_model",
    "GEMINI_API_KEY": "gemini_api_key",
    "GEMINI_MODEL": "gemini_model",
    "LLM_PROVIDER": "llm_provider",
    "LLM_FALLBACKS": "llm_fallbacks",
    "LLM_BUDGET_USD": "llm_budget_usd",
    "LLM_BUDGET_ACTION": "llm_budget_action",
}

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # app/services/ -> app/ -> backend/


def env_path() -> Path:
    """ที่อยู่ของ `.env` — คิดจากตำแหน่งไฟล์นี้ ไม่ใช่ CWD (uvicorn/pytest สตาร์ตคนละที่กัน)."""
    return _BACKEND_DIR / ".env"


def backup_env(path: Path) -> Path | None:
    """สำเนาไฟล์เดิมไว้ก่อนเขียนทับ — คืน path ของสำเนา (None = ยังไม่มีไฟล์เดิม)."""
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = _BACKEND_DIR.parent / "BackUp" / f"EnvSettings_{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    shutil.copy2(path, target)
    return target


def write_env(values: dict[str, str], *, path: Path | None = None) -> Path:
    """แก้เฉพาะบรรทัดของ key ที่ส่งมา — คอมเมนต์/ลำดับ/ตัวแปรอื่นต้องอยู่ครบเหมือนเดิม.

    key ที่ยังไม่มีในไฟล์จะถูกต่อท้าย · ไม่มีบรรทัดซ้ำ · ไม่มี BOM · ขึ้นบรรทัดใหม่ด้วย ``\\n``
    """
    path = path or env_path()
    backup_env(path)

    original = path.read_text(encoding="utf-8") if path.exists() else ""
    remaining = dict(values)
    lines: list[str] = []
    for line in original.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                lines.append(f"{key}={remaining.pop(key)}")
                continue
        lines.append(line)
    for key, value in remaining.items():
        lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def apply_to_settings(values: dict[str, str]) -> None:
    """อัปเดต `Settings` ที่โหลดไว้แล้วในหน่วยความจำ ให้มีผล **ทันทีโดยไม่ต้อง restart**.

    จงใจแก้ instance เดิมแทน `get_settings.cache_clear()` เพราะมีโมดูลที่จับ instance ไว้
    ตั้งแต่ import (เช่น `main.settings`) — ล้าง cache แล้วโมดูลพวกนั้นจะยังถือค่าเก่าอยู่
    """
    settings = get_settings()
    for env_name, value in values.items():
        field = ENV_TO_FIELD.get(env_name)
        if field is None:
            continue
        # ค่าใน `.env` เป็นข้อความเสมอ แต่ field ของ Settings มีชนิดจริง (เช่นเพดานเป็น float)
        # ⇒ ต้องแปลงเอง: pydantic ไม่ validate ตอน setattr ⇒ ยัด str ลง float field ได้เงียบ ๆ
        # แล้วไปพังตอนเอาไปเทียบตัวเลขทีหลัง (โผล่เป็น TypeError กลางรอบรัน)
        info = type(settings).model_fields.get(field)
        annotation = info.annotation if info is not None else str
        if annotation is float:
            setattr(settings, field, float(value or 0))
        elif annotation is int:
            setattr(settings, field, int(value or 0))
        else:
            setattr(settings, field, value)
