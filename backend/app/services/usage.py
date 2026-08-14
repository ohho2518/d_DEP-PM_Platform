"""รวมโทเคนของโปรเจกต์ **แยกตามผู้ให้บริการ** — ถังสำหรับเพดานค่าใช้จ่ายต่อเจ้า.

§5 ของใบสั่งงาน 2026-08-06: ราคาต่อโทเคนแต่ละเจ้าไม่เท่ากัน เพดานก้อนเดียวจึงคุมไม่อยู่
เมื่อระบบสลับเจ้าเอง · ที่นี่ยัง**ไม่คำนวณเป็นเงิน** — ตารางราคาเป็นข้อมูลที่เปลี่ยนบ่อยและ
ต้องมาจากเจ้าของ (ห้ามฝังตัวเลขที่เดาเอง) จึงหยุดที่ "จำนวนโทเคนต่อเจ้า" ซึ่งเป็นของที่วัดได้จริง
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.task import Task

#: ราคาต่อ 1 ล้านโทเคน — หารตัวนี้เพื่อได้ราคาต่อโทเคน
_PER_MILLION = 1_000_000


def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    """ค่าใช้จ่าย **โดยประมาณ** ของเจ้านั้น (USD) — เจ้าที่ไม่มีราคาตั้งไว้คืน 0.

    ตั้งใจเรียกว่า "ประมาณการ": ราคามาจากหน้าประกาศของผู้ให้บริการ ไม่ใช่บิลจริงของบัญชีนี้
    (ส่วนลด/เครดิต/ราคาพิเศษไม่ถูกนับ) — ห้ามเอาไปอ้างเป็นตัวเลขค่าใช้จ่ายจริง
    """
    price_in, price_out = get_settings().provider_prices.get(provider, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / _PER_MILLION


def project_usage(db: Session, project_id: uuid.UUID) -> dict:
    """โทเคนของทุก task ในโปรเจกต์ แยกตามผู้ให้บริการ + ส่วนที่ระบุเจ้าไม่ได้.

    ``untracked`` คืองานที่ทำก่อน 2026-08-14 ซึ่งนับรวมไว้แต่ไม่รู้ว่าเจ้าไหน —
    **จงใจแยกออกมาให้เห็น** แทนที่จะเดาย้อนหลังว่าเป็นของ Anthropic
    """
    tasks = (
        db.execute(select(Task).where(Task.project_id == project_id)).scalars().all()
    )

    by_provider: dict[str, dict] = {}
    tracked_input = tracked_output = 0
    for task in tasks:
        for name, entry in (task.token_usage or {}).items():
            slot = by_provider.setdefault(
                name,
                {"provider": name, "model": "", "input": 0, "output": 0, "calls": 0, "tasks": 0},
            )
            slot["input"] += int(entry.get("input", 0))
            slot["output"] += int(entry.get("output", 0))
            slot["calls"] += int(entry.get("calls", 0))
            slot["tasks"] += 1
            if entry.get("model"):
                slot["model"] = str(entry["model"])
            tracked_input += int(entry.get("input", 0))
            tracked_output += int(entry.get("output", 0))

    total_input = sum(task.tokens_input or 0 for task in tasks)
    total_output = sum(task.tokens_output or 0 for task in tasks)

    for slot in by_provider.values():
        slot["cost_usd"] = round(estimate_cost(slot["provider"], slot["input"], slot["output"]), 4)
    spent = round(sum(slot["cost_usd"] for slot in by_provider.values()), 4)

    settings = get_settings()
    budget = settings.llm_budget_usd
    return {
        "project_id": str(project_id),
        "totals": {
            "input": total_input,
            "output": total_output,
            "calls": sum(slot["calls"] for slot in by_provider.values()),
        },
        # เรียงจากตัวที่กินมากสุด — คนอ่านสนใจว่า "ใครกินงบ" เป็นอันดับแรก
        "by_provider": sorted(by_provider.values(), key=lambda s: -(s["input"] + s["output"])),
        "untracked": {
            "input": max(0, total_input - tracked_input),
            "output": max(0, total_output - tracked_output),
        },
        "budget": {
            #: **ประมาณการ** จากราคาประกาศ ไม่ใช่บิลจริง — คิดเฉพาะโทเคนที่รู้ว่าเจ้าไหนใช้
            "spent_usd": spent,
            "limit_usd": budget,
            "action": settings.llm_budget_action,
            "over": bool(budget) and spent >= budget,
            #: โทเคนของงานเก่าที่ระบุเจ้าไม่ได้ **ไม่ถูกคิดเงิน** — บอกไว้ไม่ให้เข้าใจผิดว่าใช้น้อย
            "excludes_untracked": bool(max(0, total_input - tracked_input)),
        },
    }


def over_budget(db: Session, project_id: uuid.UUID) -> str | None:
    """คืนข้อความอธิบายเมื่อโปรเจกต์นี้ใช้เกินเพดานแล้ว — None = ยังไม่เกิน/ไม่ได้ตั้งเพดาน."""
    settings = get_settings()
    if not settings.llm_budget_usd:
        return None
    budget = project_usage(db, project_id)["budget"]
    if not budget["over"]:
        return None
    return (
        f"ใช้ไปประมาณ ${budget['spent_usd']:.4f} จากเพดาน ${budget['limit_usd']:.2f} "
        "(ประมาณการจากราคาประกาศ ไม่ใช่บิลจริง)"
    )
