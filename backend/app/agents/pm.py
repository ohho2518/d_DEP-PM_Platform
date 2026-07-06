"""PM Agent Task Breakdown — requirement text -> validated TaskPlan (Blueprint §6).

Calls the Claude API (persona: PM) when an API key is configured, validates the JSON into
:class:`TaskPlan`, and retries once on a parse failure (Risk #7). When no key is present, or
after repeated parse failures, falls back to a single manual task so the flow never dead-ends.
"""
from __future__ import annotations

import json
import re

from app.agents.personas import PM_SYSTEM_PROMPT
from app.config import get_settings
from app.constants import Priority
from app.schemas.task import PlannedTask, TaskPlan

# Number of times to ask the model to fix invalid JSON before giving up (Risk #7).
_MAX_PARSE_RETRIES = 1


class BreakdownResult:
    """Small container: the plan plus how it was produced ('agent' | 'fallback')."""

    def __init__(self, plan: TaskPlan, source: str) -> None:
        self.plan = plan
        self.source = source


def _extract_json(text: str) -> str:
    """Pull the first {...} block out of a model reply that may wrap it in prose/fences."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    return brace.group(0) if brace else text


def _fallback_plan(requirement: str) -> TaskPlan:
    """Deterministic single-task plan used when the agent is unavailable or unparseable."""
    title = requirement.strip().splitlines()[0][:120] if requirement.strip() else "Untitled task"
    return TaskPlan(
        tasks=[
            PlannedTask(
                ref="T1",
                title=title,
                description=requirement.strip() or None,
                priority=Priority.P2,
                depends_on=[],
                spec="(fallback) PM Agent ไม่พร้อม — สร้าง task เดียวจาก requirement ให้ผู้ใช้แตกเอง",
            )
        ]
    )


def breakdown_requirement(requirement: str) -> BreakdownResult:
    """Break ``requirement`` into a validated :class:`TaskPlan`.

    Never raises for model/parse issues — returns a fallback plan instead so the API endpoint
    can always persist something and report the source to the caller.
    """
    settings = get_settings()
    if not settings.agent_enabled:
        return BreakdownResult(_fallback_plan(requirement), source="fallback")

    # Imported lazily so the package imports even if `anthropic` isn't installed yet.
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": f"Requirement:\n{requirement}"}]

    last_text = ""
    for attempt in range(_MAX_PARSE_RETRIES + 1):
        try:
            response = client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.max_tokens_per_task,
                system=PM_SYSTEM_PROMPT,
                messages=messages,
            )
        except Exception:
            # Network / auth / rate-limit — degrade gracefully rather than 500 the request.
            return BreakdownResult(_fallback_plan(requirement), source="fallback")

        last_text = "".join(block.text for block in response.content if block.type == "text")
        try:
            data = json.loads(_extract_json(last_text))
            return BreakdownResult(TaskPlan.model_validate(data), source="agent")
        except (json.JSONDecodeError, ValueError):
            if attempt < _MAX_PARSE_RETRIES:
                # Ask the model to repair its own output (structured-retry, Risk #7).
                messages.append({"role": "assistant", "content": last_text})
                messages.append(
                    {
                        "role": "user",
                        "content": "ผลลัพธ์ก่อนหน้าไม่ใช่ JSON ที่ parse ได้ตามโครงสร้าง "
                        "กรุณาตอบใหม่เป็น JSON ที่ถูกต้องเท่านั้น ไม่มีข้อความอื่น",
                    }
                )
            continue

    return BreakdownResult(_fallback_plan(requirement), source="fallback")
