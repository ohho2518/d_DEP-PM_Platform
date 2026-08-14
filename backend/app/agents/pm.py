"""PM Agent Task Breakdown — requirement text -> validated TaskPlan (Blueprint §6).

เรียกโมเดลผ่าน ``providers.call_chain`` (persona: PM) เมื่อมีคีย์ของผู้ให้บริการอย่างน้อยหนึ่งเจ้า,
validate JSON เป็น :class:`TaskPlan`, และ retry หนึ่งครั้งเมื่อ parse ไม่ผ่าน (Risk #7) ·
ไม่มีคีย์/เรียกไม่สำเร็จ → คืนแผน task เดียวพร้อม**บอกเหตุ** เพื่อให้ flow ไม่ตันและผู้ใช้รู้ว่าทำไม
"""
from __future__ import annotations

import json
import logging
import re

from app.agents.personas import PM_SYSTEM_PROMPT
from app.agents.providers import AllProvidersUnavailable, LlmError, call_chain
from app.config import get_settings
from app.constants import Priority
from app.schemas.task import PlannedTask, TaskPlan

logger = logging.getLogger(__name__)

# Number of times to ask the model to fix invalid JSON before giving up (Risk #7).
_MAX_PARSE_RETRIES = 1


class BreakdownResult:
    """Small container: the plan plus how it was produced ('agent' | 'fallback').

    ``provider``/``model`` = ใครเป็นคนแตกงานจริง (ว่าง = ไม่ได้เรียกโมเดล) — เก็บไว้ให้ log
    และผู้เรียกเอาไปแสดงต่อได้ ตามกติกา "ห้ามสลับเงียบ" ของใบสั่งงาน 2026-08-06
    """

    def __init__(self, plan: TaskPlan, source: str, *, provider: str = "", model: str = "") -> None:
        self.plan = plan
        self.source = source
        self.provider = provider
        self.model = model


def _extract_json(text: str) -> str:
    """Pull the first {...} block out of a model reply that may wrap it in prose/fences."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    return brace.group(0) if brace else text


def _fallback_plan(requirement: str, reason: str | None = None) -> TaskPlan:
    """Deterministic single-task plan used when the agent is unavailable or unparseable.

    ``reason`` ไปอยู่ใน ``spec`` เพื่อให้ผู้ใช้เห็นบนบอร์ดว่าทำไมได้ task เดียว —
    degrade เงียบ ๆ คืออาการที่ใบสั่งงาน 2026-08-06 สั่งให้กำจัด
    """
    title = requirement.strip().splitlines()[0][:120] if requirement.strip() else "Untitled task"
    spec = "(fallback) PM Agent ไม่พร้อม — สร้าง task เดียวจาก requirement ให้ผู้ใช้แตกเอง"
    if reason:
        spec = f"{spec}\nเหตุ: {reason}"
    return TaskPlan(
        tasks=[
            PlannedTask(
                ref="T1",
                title=title,
                description=requirement.strip() or None,
                priority=Priority.P2,
                depends_on=[],
                spec=spec,
            )
        ]
    )


def breakdown_requirement(requirement: str) -> BreakdownResult:
    """Break ``requirement`` into a validated :class:`TaskPlan`.

    Never raises for model/parse issues — returns a fallback plan instead so the API endpoint
    can always persist something and report the source to the caller.
    """
    if not get_settings().agent_enabled:
        return BreakdownResult(
            _fallback_plan(requirement, "ยังไม่ได้ตั้งคีย์ของผู้ให้บริการ AI เลย"), source="fallback"
        )

    prompt = f"Requirement:\n{requirement}"
    for attempt in range(_MAX_PARSE_RETRIES + 1):
        try:
            reply = call_chain(PM_SYSTEM_PROMPT, prompt)
        except (AllProvidersUnavailable, LlmError) as exc:
            # ทุกเจ้าใช้ไม่ได้ / โจทย์ผิด — degrade อย่างมีศักดิ์ศรีแทนการ 500 ทั้ง request
            # แต่ต้อง **บอกเหตุ** ไม่ใช่คืนแผนเปล่า ๆ ให้ผู้ใช้เดาเอง
            logger.warning("PM Agent แตกงานไม่สำเร็จ: %s", exc)
            return BreakdownResult(_fallback_plan(requirement, str(exc)), source="fallback")

        try:
            data = json.loads(_extract_json(reply.text))
            return BreakdownResult(
                TaskPlan.model_validate(data),
                source="agent",
                provider=reply.provider,
                model=reply.model,
            )
        except (json.JSONDecodeError, ValueError):
            if attempt < _MAX_PARSE_RETRIES:
                # Ask the model to repair its own output (structured-retry, Risk #7).
                # ส่งของเดิมกลับไปในพรอมป์ตเดียว — `call_chain` เป็น single-turn เพื่อให้ทุกเจ้า
                # ใช้ผิวสัมผัสเดียวกันได้ (รูปแบบ message history ต่างกันในแต่ละค่าย)
                prompt = (
                    f"Requirement:\n{requirement}\n\n"
                    f"ผลลัพธ์ก่อนหน้าไม่ใช่ JSON ที่ parse ได้ตามโครงสร้าง:\n{reply.text}\n\n"
                    "กรุณาตอบใหม่เป็น JSON ที่ถูกต้องเท่านั้น ไม่มีข้อความอื่น"
                )
            continue

    return BreakdownResult(
        _fallback_plan(requirement, "โมเดลตอบกลับเป็น JSON ที่อ่านไม่ได้หลังลองซ้ำแล้ว"),
        source="fallback",
    )
