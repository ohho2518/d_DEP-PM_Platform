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


class TeamExecutor:
    """Team Mode (Sprint 4, Blueprint §9): map role → provider ต่างค่าย.

    Mapping ตาม Blueprint: Codex Dev = OpenAI, Gemini SR = Google,
    PM/Reviewer = Claude (Anthropic). Provider ที่ config ไม่ครบ → fallback chain:
    provider ของ role → anthropic → deterministic text (ไม่ล้มกลางงาน)

    Orchestrator ไม่รู้จักคลาสนี้โดยตรง — เห็นแค่ PersonaExecutor protocol (DoD Sprint 4)
    """

    ROLE_PROVIDER: dict[AgentRole, str] = {
        AgentRole.PM: "anthropic",
        AgentRole.DEV: "openai",            # Codex Dev
        AgentRole.SENIOR_ARCHITECT: "google",  # Gemini SR
        AgentRole.REVIEWER: "anthropic",
    }

    def __init__(self) -> None:
        from app.agents.providers import BUILDERS

        # สร้าง client ครั้งเดียวต่อ provider ที่ config ครบ
        self._calls = {name: builder() for name, builder in BUILDERS.items()}
        self._fallback = FallbackExecutor()

    def _call_for(self, role: AgentRole):
        provider = self.ROLE_PROVIDER[role]
        return self._calls.get(provider) or self._calls.get("anthropic")

    def execute(self, task: Task, role: AgentRole, feedback: str | None = None) -> str:
        call = self._call_for(role)
        if call is None:
            return self._fallback.execute(task, role, feedback)
        prompt = (
            f"Task: {task.title}\n"
            f"Description: {task.description or '-'}\n"
            f"Spec / acceptance criteria: {task.spec or '-'}"
        )
        if feedback:
            prompt += f"\n\nReview comment รอบก่อน (ต้องแก้): {feedback}"
        return call(PERSONA_PROMPTS[role], prompt)

    def review(self, task: Task, work: str) -> ReviewResult:
        call = self._call_for(AgentRole.REVIEWER)
        if call is None:
            return self._fallback.review(task, work)
        prompt = (
            f"Task: {task.title}\n"
            f"Spec / acceptance criteria: {task.spec or '-'}\n\n"
            f"Work product ที่ต้องตรวจ:\n{work}"
        )
        text = call(REVIEWER_SYSTEM_PROMPT, prompt)
        try:
            data = json.loads(_extract_json(text))
            return ReviewResult(approved=bool(data["approved"]), comment=str(data.get("comment", "")))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return ReviewResult(approved=True, comment="(unparseable review — auto-approved)")


def get_executor() -> PersonaExecutor:
    """เลือก executor ตาม config — สลับ Solo ↔ Team ด้วย env `AGENT_MODE` เท่านั้น.

    - team               → TeamExecutor (role → provider, fallback chain ต่อ role)
    - solo + มี key      → ClaudeExecutor
    - solo + ไม่มี key   → FallbackExecutor (deterministic)
    """
    settings = get_settings()
    if settings.agent_mode == "team":
        return TeamExecutor()
    return ClaudeExecutor() if settings.agent_enabled else FallbackExecutor()
