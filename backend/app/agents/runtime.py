"""Agent Runtime — executes a task with a persona and reviews the work product.

สอง implementation:
- :class:`ClaudeExecutor`  — เรียก Claude API ด้วย persona system prompt (เมื่อมี API key)
- :class:`FallbackExecutor` — deterministic ไม่มี network call (ใช้ตอนไม่มี key / ใน tests)

Orchestrator ไม่รู้จักความต่างนี้ — เห็นแค่ interface ``execute`` / ``review``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from app.agents.personas import PERSONA_PROMPTS, REVIEWER_SYSTEM_PROMPT
from app.agents.pm import _extract_json
from app.config import get_settings
from app.constants import AgentRole
from app.models.task import Task


@dataclass
class ReviewResult:
    approved: bool
    comment: str


class PersonaExecutor(Protocol):
    """สัญญาที่ Orchestrator ใช้เรียก agent ทำงานและตรวจงาน."""

    def execute(self, task: Task, role: AgentRole, feedback: str | None = None) -> str:
        """ผลิต work product สำหรับ task (feedback = review comment รอบก่อน ถ้ามี)."""
        ...

    def review(self, task: Task, work: str) -> ReviewResult:
        """ตรวจ work product เทียบ spec."""
        ...


class FallbackExecutor:
    """Deterministic executor: ทำงานเสร็จเสมอ, reviewer approve เสมอ.

    ทำให้ E2E happy path รันได้โดยไม่มี API key — response ระบุชัดว่าเป็น (fallback).
    """

    def execute(self, task: Task, role: AgentRole, feedback: str | None = None) -> str:
        note = f" (แก้ตาม feedback: {feedback})" if feedback else ""
        return f"(fallback:{role.value}) ดำเนินการ '{task.title}' ตาม spec แล้ว{note}"

    def review(self, task: Task, work: str) -> ReviewResult:
        return ReviewResult(approved=True, comment="(fallback) ตรวจตาม spec แล้ว — approve")


class ClaudeExecutor:
    """เรียก Claude API ด้วย persona prompt ตาม role (Solo Mode — key เดียวทุกบทบาท)."""

    def __init__(self) -> None:
        import anthropic

        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model
        self._max_tokens = settings.max_tokens_per_task

    def _call(self, system: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in response.content if b.type == "text")

    def execute(self, task: Task, role: AgentRole, feedback: str | None = None) -> str:
        prompt = (
            f"Task: {task.title}\n"
            f"Description: {task.description or '-'}\n"
            f"Spec / acceptance criteria: {task.spec or '-'}"
        )
        if feedback:
            prompt += f"\n\nReview comment รอบก่อน (ต้องแก้): {feedback}"
        return self._call(PERSONA_PROMPTS[role], prompt)

    def review(self, task: Task, work: str) -> ReviewResult:
        prompt = (
            f"Task: {task.title}\n"
            f"Spec / acceptance criteria: {task.spec or '-'}\n\n"
            f"Work product ที่ต้องตรวจ:\n{work}"
        )
        text = self._call(REVIEWER_SYSTEM_PROMPT, prompt)
        try:
            data = json.loads(_extract_json(text))
            return ReviewResult(approved=bool(data["approved"]), comment=str(data.get("comment", "")))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            # Parse ไม่ได้ → auto-approve พร้อม note (กัน revision loop จาก output เพี้ยน — Risk #7)
            return ReviewResult(approved=True, comment="(unparseable review — auto-approved)")


def get_executor() -> PersonaExecutor:
    """เลือก executor ตาม config: มี key จริง → Claude, ไม่มี → fallback."""
    return ClaudeExecutor() if get_settings().agent_enabled else FallbackExecutor()
