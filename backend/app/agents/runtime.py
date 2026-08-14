"""Agent Runtime — executes a task with a persona and reviews the work product.

สาม implementation:
- :class:`SoloExecutor`     — ตัวหลักตัวเดียวทุกบทบาท (``LLM_PROVIDER`` → ``LLM_FALLBACKS``)
- :class:`TeamExecutor`     — role → provider ตาม Blueprint §9 แล้วต่อด้วยลำดับสำรองชุดเดียวกัน
- :class:`FallbackExecutor` — deterministic ไม่มี network call (ใช้ตอนไม่มี key / ใน tests)

Orchestrator ไม่รู้จักความต่างนี้ — เห็นแค่ interface ``execute`` / ``review``
(อ่าน ``last_use`` เพิ่มได้ถ้าอยากรู้ว่าใครทำงานชิ้นล่าสุด — ใช้ติดป้าย "ทำโดยตัวสำรอง")
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from app.agents.personas import PERSONA_PROMPTS, REVIEWER_SYSTEM_PROMPT
from app.agents.pm import _extract_json
from app.agents.providers import (
    AllProvidersUnavailable,
    LLMReply,
    ProviderCall,
    available_providers,
    call_chain,
)
from app.config import get_settings
from app.constants import AgentRole
from app.models.task import Task

# Parse review ไม่ได้ → เรียก reviewer ซ้ำได้อีกกี่ครั้งก่อนตัดสิน reject (debt #3)
REVIEW_PARSE_RETRIES = 1


@dataclass
class ReviewResult:
    approved: bool
    comment: str
    #: งานติดเพราะขาดข้อมูล/สิทธิ์ที่ agent หามาเองไม่ได้ → escalate ทันที ไม่วน revision
    #: (ค่าปริยาย False = พฤติกรรมเดิมทุกประการ; provider ที่ไม่รู้จักฟิลด์นี้ไม่กระทบ)
    needs_human: bool = False


def _as_reply(value: LLMReply | str) -> LLMReply:
    """Normalize ผลจาก provider call — เทสต์/custom call อาจคืน str ล้วน (ไม่มี usage)."""
    return value if isinstance(value, LLMReply) else LLMReply(text=value)


def _add_usage(task: Task, reply: LLMReply) -> None:
    """สะสม token usage ลง task (debt #7) — ผู้เรียก orchestrator เป็นคน commit."""
    task.tokens_input = (task.tokens_input or 0) + reply.input_tokens
    task.tokens_output = (task.tokens_output or 0) + reply.output_tokens


def _execute_prompt(task: Task, feedback: str | None, context: str | None = None) -> str:
    prompt = (
        f"Task: {task.title}\n"
        f"Description: {task.description or '-'}\n"
        f"Spec / acceptance criteria: {task.spec or '-'}"
    )
    if context:
        # วางก่อน feedback: agent ต้องเห็น "ของที่มีให้ใช้" ก่อนคำสั่งแก้ไขรอบก่อน
        prompt += f"\n\n--- ผลงานของงานก่อนหน้า ---\n{context}"
    if feedback:
        prompt += f"\n\nReview comment รอบก่อน (ต้องแก้): {feedback}"
    return prompt


def _review_prompt(task: Task, work: str) -> str:
    """สิ่งที่ reviewer ได้เห็น — **ต้องมีวัตถุดิบชุดเดียวกับที่คนทำงานได้รับ**.

    ⚠️ เดิมส่งแค่ title + spec (ไม่มี description) · หลังใส่กติกาห้ามกุหลักฐาน reviewer จึง
    ปฏิเสธงานที่ถูกต้องด้วยเหตุผลว่า *"ไม่มี description ต้นฉบับแนบมา จึงยืนยันไม่ได้ว่า
    รายละเอียดที่อ้างตรงกับต้นฉบับ"* แล้วงานวนจนหมดโควตา revision → escalated
    (เจอจริง 2026-08-14 ตอนทดสอบ failover · อาการเดียวกับบั๊ก upstream context ของ Phase 3a)
    """
    return (
        f"Task: {task.title}\n"
        f"Description: {task.description or '-'}\n"
        f"Spec / acceptance criteria: {task.spec or '-'}\n\n"
        f"Work product ที่ต้องตรวจ:\n{work}"
    )


def _parse_review(text: str) -> ReviewResult | None:
    try:
        data = json.loads(_extract_json(text))
        return ReviewResult(
            approved=bool(data["approved"]),
            comment=str(data.get("comment", "")),
            needs_human=bool(data.get("needs_human", False)),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _review_with_retry(task: Task, call: ProviderCall, prompt: str) -> ReviewResult:
    """เรียก reviewer แล้ว parse ผล; parse ไม่ได้ → retry ก่อน แล้วจึง reject (fail-safe).

    เดิม parse ไม่ได้ = auto-approve (Risk #7 กัน revision loop) — เปลี่ยนเป็น reject
    เพื่อไม่ให้งานที่ไม่ถูกตรวจจริงหลุดเป็น done; loop ถูก bound ด้วย MAX_REVISIONS
    → escalate ให้คนตรวจเอง (debt #3)
    """
    for _ in range(1 + REVIEW_PARSE_RETRIES):
        reply = _as_reply(call(REVIEWER_SYSTEM_PROMPT, prompt))
        _add_usage(task, reply)
        parsed = _parse_review(reply.text)
        if parsed is not None:
            return parsed
    return ReviewResult(
        approved=False,
        comment="(unparseable review after retry — reject ไว้ก่อน; ครบ MAX_REVISIONS จะ escalate ให้คนตรวจ)",
    )


class PersonaExecutor(Protocol):
    """สัญญาที่ Orchestrator ใช้เรียก agent ทำงานและตรวจงาน.

    ``execute`` รับ ``context`` เพิ่มตั้งแต่ 2026-08-03 — ผลงานจริงของ task ที่อยู่เหนือ
    ในกราฟพึ่งพา · **provider ใหม่ต้องส่งต่อให้โมเดลด้วย** ไม่งั้นงานประเภท "ทำต่อจาก
    ของเดิม" จะผลิตได้แค่โครงเปล่า (บทเรียน UAT — ดู `orchestrator.upstream_context`)
    """

    def execute(
        self,
        task: Task,
        role: AgentRole,
        feedback: str | None = None,
        context: str | None = None,
    ) -> str:
        """ผลิต work product สำหรับ task.

        ``feedback`` = review comment รอบก่อน · ``context`` = ผลงานของงานก่อนหน้า
        """
        ...

    def review(self, task: Task, work: str) -> ReviewResult:
        """ตรวจ work product เทียบ spec."""
        ...


class FallbackExecutor:
    """Deterministic executor: ทำงานเสร็จเสมอ, reviewer approve เสมอ.

    ทำให้ E2E happy path รันได้โดยไม่มี API key — response ระบุชัดว่าเป็น (fallback).
    """

    def execute(
        self,
        task: Task,
        role: AgentRole,
        feedback: str | None = None,
        context: str | None = None,
    ) -> str:
        note = f" (แก้ตาม feedback: {feedback})" if feedback else ""
        # บอกจำนวนงานก่อนหน้าที่ได้รับมา เพื่อให้ test/ผู้ใช้เห็นว่า context ถูกส่งมาจริง
        upstream = f" [ใช้ผลงานก่อนหน้า {context.count('### ')} ชิ้น]" if context else ""
        return f"(fallback:{role.value}) ดำเนินการ '{task.title}' ตาม spec แล้ว{note}{upstream}"

    def review(self, task: Task, work: str) -> ReviewResult:
        return ReviewResult(approved=True, comment="(fallback) ตรวจตาม spec แล้ว — approve")


@dataclass
class ProviderUse:
    """ใครทำงานชิ้นล่าสุด — orchestrator เอาไปติดป้ายในผลงาน (**ห้ามสลับเงียบ**, ใบสั่งงาน 6 ส.ค. §4)."""

    provider: str = ""
    model: str = ""
    primary: str = ""  # ตัวหลักของบทบาทนั้น (ไว้เทียบว่าถอยไปใช้ตัวสำรองหรือยัง)

    @property
    def degraded(self) -> bool:
        return bool(self.provider) and bool(self.primary) and self.provider != self.primary


class _ChainExecutor:
    """ฐานร่วมของ Solo/Team — เรียก LLM ผ่าน ``providers.call_chain`` แล้วจำว่าใครทำงานล่าสุด.

    ไม่มี client ของตัวเอง: ความรู้เรื่องผู้ให้บริการทั้งหมดอยู่ใน ``providers.py`` ที่เดียว
    (AGENTS.md §9.1 — ห้าม import SDK ของเจ้าไหนนอกไฟล์นั้น)
    """

    def __init__(self) -> None:
        self.last_use = ProviderUse()
        self._fallback = FallbackExecutor()
        #: ตารางฟังก์ชันที่สร้างไว้ล่วงหน้า (Team Mode) — None = ให้ chain สร้างเองต่อ call
        self._calls: dict[str, ProviderCall | None] | None = None

    def _primary_for(self, role: AgentRole) -> str:
        raise NotImplementedError

    @staticmethod
    def _may_use_deterministic(exc: AllProvidersUnavailable) -> bool:
        """ถอยไปทาง deterministic ได้เฉพาะเมื่อ **ทั้งระบบไม่มีคีย์เลย** (สัญญาเดิม §9.1.8).

        มีคีย์อยู่แล้วแต่บทบาทนี้ไปไม่ถึงเจ้าไหนเลย (ตั้งลำดับสำรองไม่ครบ / เจ้าตาย) =
        **ต้องดัง** — ผลิตข้อความ deterministic แล้วนับว่าเสร็จคือการรายงานเกินจริง
        """
        return exc.only_missing_keys and not available_providers()

    def _call_role(self, role: AgentRole, system: str, prompt: str) -> LLMReply:
        primary = self._primary_for(role)
        reply = call_chain(system, prompt, primary=primary, calls=self._calls)
        self.last_use = ProviderUse(provider=reply.provider, model=reply.model, primary=primary)
        if not reply.text.strip():
            # พบจริงใน UAT: adaptive thinking กินโควตา max_tokens จนหมด -> text ว่าง
            # คืน marker ชัดเจนแทน string ว่าง เพื่อให้ reviewer/audit เห็นสาเหตุ
            reply.text = (
                f"(no text output จาก {reply.provider or 'provider'} — "
                f"stop_reason={reply.stop_reason or '-'}; "
                "เพิ่ม MAX_TOKENS_PER_TASK หรือแตก task ให้เล็กลง)"
            )
        return reply

    def execute(
        self,
        task: Task,
        role: AgentRole,
        feedback: str | None = None,
        context: str | None = None,
    ) -> str:
        try:
            reply = self._call_role(
                role, PERSONA_PROMPTS[role], _execute_prompt(task, feedback, context)
            )
        except AllProvidersUnavailable as exc:
            if self._may_use_deterministic(exc):
                return self._fallback.execute(task, role, feedback, context)
            raise
        _add_usage(task, reply)
        return reply.text

    def review(self, task: Task, work: str) -> ReviewResult:
        role = AgentRole.REVIEWER
        try:
            return _review_with_retry(
                task,
                lambda system, prompt: self._call_role(role, system, prompt),
                _review_prompt(task, work),
            )
        except AllProvidersUnavailable as exc:
            if self._may_use_deterministic(exc):
                return self._fallback.review(task, work)
            raise


class SoloExecutor(_ChainExecutor):
    """Solo Mode: ทุกบทบาทใช้ตัวหลักตัวเดียวกัน (``LLM_PROVIDER``) แล้วไล่ตาม ``LLM_FALLBACKS``.

    เดิมชื่อ ``ClaudeExecutor`` และสร้าง client ของ Anthropic เอง — เปลี่ยนชื่อตอนทำใบสั่งงาน
    2026-08-06 เพราะชื่อเดิมจะโกหกทันทีที่มันเรียกเจ้าอื่นได้
    """

    def _primary_for(self, role: AgentRole) -> str:
        return get_settings().llm_provider


class TeamExecutor(_ChainExecutor):
    """Team Mode (Sprint 4, Blueprint §9): map role → provider ต่างค่าย.

    Mapping ตาม Blueprint: Codex Dev = OpenAI, Gemini SR = Google, PM/Reviewer = Claude
    · ตัวหลักของบทบาทล้ม → ไล่ต่อตาม ``LLM_FALLBACKS`` (เดิม hardcode ว่าถอยไป anthropic เท่านั้น)
    · ไม่มีใครตั้งคีย์เลย → deterministic text (ไม่ล้มกลางงาน)

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

        super().__init__()
        # สร้าง client ครั้งเดียวต่อ provider ที่ config ครบ (เทสต์เสียบ call ปลอมผ่าน `_calls`)
        self._calls = {name: builder() for name, builder in BUILDERS.items()}

    def _primary_for(self, role: AgentRole) -> str:
        return self.ROLE_PROVIDER[role]


def get_executor() -> PersonaExecutor:
    """เลือก executor ตาม config — สลับ Solo ↔ Team ด้วย env `AGENT_MODE` เท่านั้น.

    - team                    → TeamExecutor (role → provider แล้วต่อด้วยลำดับสำรอง)
    - solo + มีคีย์อย่างน้อย 1 → SoloExecutor (`LLM_PROVIDER` → `LLM_FALLBACKS`)
    - solo + ไม่มีคีย์เลย      → FallbackExecutor (deterministic)
    """
    settings = get_settings()
    if settings.agent_mode == "team":
        return TeamExecutor()
    return SoloExecutor() if settings.agent_enabled else FallbackExecutor()
