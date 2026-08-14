"""ผิวสัมผัสเดียวของรีโปนี้ที่คุยกับผู้ให้บริการ LLM — provider + ลำดับสำรอง + แยกชนิด error.

ใบสั่งงาน 2026-08-06 ("รองรับ AI หลายเจ้า", `d_CEO\\docs\\ORDER_TICKET_2026-08-06.md`):
เช้าวันนั้นเครดิตบัญชี Anthropic หมด แล้ว **ทั้งบ้านหยุดพร้อมกันแบบเงียบ ๆ** ⇒ ทุกระบบที่เรียก LLM
ต้องสลับเจ้าได้โดยไม่แก้โค้ดธุรกิจ · ต้องบอกว่ากำลังใช้ตัวสำรอง · และต้องแยกให้ออกว่า
"บัญชีใช้ไม่ได้" (สลับทันที) ต่างจาก "โจทย์ผิด" (ห้ามสลับ — สลับไปก็ผิดเหมือนกัน แถมจ่ายสองเจ้า)

**ห้าม import SDK ของผู้ให้บริการนอกไฟล์นี้** (AGENTS.md §9.1) — แต่ละ provider เป็นฟังก์ชัน
`(system, prompt) -> LLMReply` ที่ lazy import SDK เพื่อให้ระบบรันได้แม้ไม่ได้ติดตั้ง/ไม่มีคีย์
(builder คืน None = เจ้านั้นใช้ไม่ได้ ให้ `call_chain` ข้ามไปเจ้าถัดไป)
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from app.config import get_settings

# เพดานความยาว body ของ error ที่เก็บไว้ — ต้องเก็บ "เนื้อความ" ไม่ใช่แค่รหัสสถานะ
# (บทเรียนจริง 29 ก.ค. ในคู่มือกลาง: log เขียนแค่ `HTTP 400` 40 ครั้งติด ต้นเหตุจริงคือ
#  credit balance หมด ซึ่งไม่มีทางรู้ได้เลยจาก log — เสียเวลาไปหนึ่งวัน)
ERROR_BODY_CHAR_LIMIT = 500

# ข้อความที่แปลว่า "บัญชีเจ้านี้ใช้ไม่ได้" แม้ผู้ให้บริการจะตอบมาเป็น 400
ACCOUNT_HINTS = (
    "credit balance",
    "billing",
    "quota",
    "insufficient",
    "payment",
    "suspended",
    "deactivated",
    "expired",
)

# ขัดข้องชั่วคราว (429/5xx/เน็ตหลุด) → ลองซ้ำเจ้าเดิมกี่ครั้งก่อนจะสลับเจ้า
TEMPORARY_RETRIES = 1
RETRY_SLEEP_SECONDS = 1.0  # เทสต์ตั้งเป็น 0 เพื่อไม่ให้ suite ช้า

#: ชื่อผู้ให้บริการ -> (env ของคีย์, env ของรุ่น) — หน้า Settings ใช้เขียนกลับ `.env`
PROVIDER_ENV: dict[str, tuple[str, str]] = {
    "anthropic": ("ANTHROPIC_API_KEY", "CLAUDE_MODEL"),
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL"),
    "google": ("GEMINI_API_KEY", "GEMINI_MODEL"),
}


# --- ชนิดความผิดพลาด (ตาราง §3 ของใบสั่งงาน) --------------------------------
class LlmError(RuntimeError):
    """ฐานของความผิดพลาดจากผู้ให้บริการ — **เก็บ body ไว้เสมอ** ไม่ใช่แค่รหัสสถานะ."""

    def __init__(self, provider: str, message: str, *, status: int | None = None) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.body = message
        self.status = status


class LlmAccountError(LlmError):
    """บัญชีของเจ้านี้ใช้ไม่ได้ (เครดิตหมด/401/403) — **สลับเจ้าทันที** ลองซ้ำไม่มีประโยชน์."""


class LlmTemporaryError(LlmError):
    """ขัดข้องชั่วคราว (429/5xx/timeout) — ถอยแล้วลองใหม่เจ้าเดิมก่อน ค่อยสลับ."""


class LlmRequestError(LlmError):
    """โจทย์ผิด ไม่ใช่ผู้ให้บริการ (prompt ยาวเกิน/เนื้อหาถูกปฏิเสธ) — **ห้ามสลับ**."""


#: เหตุผลมาตรฐานเมื่อเจ้านั้นยังไม่ได้ตั้งคีย์ — ต่างจาก "ตั้งแล้วแต่พัง" ตรงที่ยังถอยไปทาง
#: deterministic ได้ (AGENTS.md §9.1.8: ห้ามลบ fallback path no-key → FallbackExecutor)
NO_KEY_REASON = "ยังไม่ได้ตั้งคีย์"


class AllProvidersUnavailable(RuntimeError):
    """ไล่ครบทุกเจ้าในลำดับแล้วยังไม่ได้ผล — ข้อความต้องบอกว่า *เจ้าไหนพังเพราะอะไร* ครบทุกตัว."""

    def __init__(self, failures: dict[str, str]) -> None:
        self.failures = dict(failures)
        detail = " · ".join(f"{name} = {reason}" for name, reason in failures.items())
        super().__init__(
            f"ผู้ให้บริการ LLM ใช้ไม่ได้ทั้งหมด ({detail or 'ยังไม่ได้ตั้งค่าผู้ให้บริการใดเลย'})"
        )

    @property
    def only_missing_keys(self) -> bool:
        """True = **ไม่มีใครตั้งคีย์เลย** (ไม่ใช่ตั้งแล้วพัง) → ยังใช้ทาง deterministic ได้ตามสัญญาเดิม."""
        return all(reason == NO_KEY_REASON for reason in self.failures.values())


@dataclass
class LLMReply:
    """ผลจาก LLM หนึ่ง call พร้อม token usage (debt #7) และ **ใครเป็นคนทำ** (ห้ามสลับเงียบ)."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = ""
    model: str = ""
    #: เหตุที่โมเดลหยุด — ใช้อธิบายเคส "ข้อความว่าง" ที่เจอจริงตอน thinking กิน max_tokens จนหมด
    stop_reason: str = ""


# Callable ที่พร้อมใช้ หรือ None ถ้า provider นั้น config ไม่ครบ
# (รับ str กลับได้ด้วย — เทสต์/custom call เก่าคืน str ล้วน; `_as_llm_reply` normalize ให้)
ProviderCall = Callable[[str, str], "LLMReply | str"]


def _status_of(exc: Exception) -> int | None:
    """ดึงรหัสสถานะจาก exception ของ SDK ไหนก็ได้ — แต่ละเจ้าตั้งชื่อ attribute ไม่เหมือนกัน."""
    for attr in ("status_code", "status", "code", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _body_of(exc: Exception) -> str:
    parts = [str(exc).strip()]
    text = getattr(getattr(exc, "response", None), "text", None)
    if isinstance(text, str) and text.strip() and text.strip() not in parts[0]:
        parts.append(text.strip())
    body = " | ".join(part for part in parts if part) or exc.__class__.__name__
    return body[:ERROR_BODY_CHAR_LIMIT]


def classify_error(provider: str, exc: Exception) -> LlmError:
    """แปลง exception ดิบของ SDK เป็น 1 ใน 3 ชนิดตามตาราง §3 ของใบสั่งงาน.

    ⚠️ **ลำดับการตรวจสำคัญ**: ต้องเช็กข้อความที่บอกว่าบัญชีมีปัญหา **ก่อน** สรุปว่า 400 = โจทย์ผิด
    เพราะเคสจริงที่ทำให้ทั้งบ้านล่ม (`credit balance is too low`) มาเป็น **400** ไม่ใช่ 402/403
    """
    status = _status_of(exc)
    body = _body_of(exc)
    low = body.lower()
    if status in (401, 403) or any(hint in low for hint in ACCOUNT_HINTS):
        return LlmAccountError(provider, body, status=status)
    if status in (400, 404, 413, 422):
        return LlmRequestError(provider, body, status=status)
    # 429 · 5xx · timeout · เน็ตหลุด · ไม่รู้จัก → ถือว่าชั่วคราว (ปลอดภัยกว่า: ยังไปต่อได้)
    return LlmTemporaryError(provider, body, status=status)


def _guard(provider: str, fn: Callable[[], LLMReply]) -> LLMReply:
    """เรียก SDK แล้วแปลงทุก exception เป็นชนิดที่ `call_chain` ตัดสินใจต่อได้."""
    try:
        return fn()
    except LlmError:
        raise
    except Exception as exc:  # noqa: BLE001 — จงใจกวาดทุกอย่างเพื่อจำแนก ไม่ได้กลืนทิ้ง
        raise classify_error(provider, exc) from exc


def _as_llm_reply(value: LLMReply | str, provider: str) -> LLMReply:
    reply = value if isinstance(value, LLMReply) else LLMReply(text=str(value))
    if not reply.provider:
        reply.provider = provider
    if not reply.model:
        reply.model = get_settings().provider_models.get(provider, "")
    return reply


# --- builders ต่อผู้ให้บริการ ------------------------------------------------
def build_anthropic() -> ProviderCall | None:
    settings = get_settings()
    if not settings.anthropic_api_key.strip():
        return None
    import anthropic

    # timeout ต้องตั้งเอง — ค่าปริยายของ SDK คือ 600 วิ ซึ่งนานเกินกว่าจะสลับเจ้าได้ทัน
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key, timeout=settings.llm_timeout_seconds
    )

    def call(system: str, prompt: str) -> LLMReply:
        def run() -> LLMReply:
            response = client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.max_tokens_per_task,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return LLMReply(
                text="".join(b.text for b in response.content if b.type == "text"),
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                provider="anthropic",
                model=settings.claude_model,
                stop_reason=response.stop_reason or "",
            )

        return _guard("anthropic", run)

    return call


def build_openai() -> ProviderCall | None:
    """Codex Dev (Blueprint §9). ต้องติดตั้ง `openai` + ตั้ง OPENAI_API_KEY."""
    settings = get_settings()
    if not settings.openai_api_key.strip():
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_seconds)

    def call(system: str, prompt: str) -> LLMReply:
        def run() -> LLMReply:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            usage = response.usage
            return LLMReply(
                text=response.choices[0].message.content or "",
                input_tokens=(usage.prompt_tokens or 0) if usage else 0,
                output_tokens=(usage.completion_tokens or 0) if usage else 0,
                provider="openai",
                model=settings.openai_model,
                stop_reason=response.choices[0].finish_reason or "",
            )

        return _guard("openai", run)

    return call


def build_gemini() -> ProviderCall | None:
    """Gemini SR (Blueprint §9). ต้องติดตั้ง `google-genai` + ตั้ง GEMINI_API_KEY."""
    settings = get_settings()
    if not settings.gemini_api_key.strip():
        return None
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        return None

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"timeout": int(settings.llm_timeout_seconds * 1000)},  # genai รับเป็น ms
    )

    def call(system: str, prompt: str) -> LLMReply:
        def run() -> LLMReply:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(system_instruction=system),
            )
            usage = getattr(response, "usage_metadata", None)
            return LLMReply(
                text=response.text or "",
                input_tokens=(getattr(usage, "prompt_token_count", 0) or 0) if usage else 0,
                output_tokens=(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0,
                provider="google",
                model=settings.gemini_model,
            )

        return _guard("google", run)

    return call


BUILDERS: dict[str, Callable[[], ProviderCall | None]] = {
    "anthropic": build_anthropic,
    "openai": build_openai,
    "google": build_gemini,
}


# --- ลำดับสำรอง --------------------------------------------------------------
def available_providers() -> list[str]:
    """เจ้าที่ตั้งคีย์ไว้แล้ว (ตรวจจากคีย์ ไม่สร้าง client) — ใช้ใน `/health` และหน้า Settings."""
    keys = get_settings().provider_keys
    return [name for name in BUILDERS if keys.get(name)]


def provider_chain(primary: str | None = None) -> list[str]:
    """ลำดับที่จะไล่เรียก: ``[primary or LLM_PROVIDER] + LLM_FALLBACKS``.

    ชื่อที่ไม่รู้จักถูก**ข้ามเงียบ ๆ ไม่พัง** (ตั้ง env ผิดตัวหนึ่งไม่ควรทำให้ระบบล่ม) ·
    เจ้าที่ยังไม่ตั้งคีย์ยังอยู่ในลำดับ เพื่อให้ `call_chain` รายงานได้ว่า "ยังไม่ได้ตั้งคีย์"
    """
    settings = get_settings()
    chain: list[str] = []
    for name in [primary or settings.llm_provider, *settings.llm_fallback_list]:
        key = (name or "").strip().lower()
        if key in BUILDERS and key not in chain:
            chain.append(key)
    return chain


def call_chain(
    system: str,
    prompt: str,
    *,
    primary: str | None = None,
    calls: dict[str, ProviderCall | None] | None = None,
) -> LLMReply:
    """เรียก LLM ตามลำดับสำรอง — **ทุกที่ในรีโปเรียกผ่านฟังก์ชันนี้เท่านั้น**.

    - บัญชีใช้ไม่ได้ → ข้ามไปเจ้าถัดไปทันที (ลองซ้ำเจ้าเดิมไม่มีประโยชน์)
    - ขัดข้องชั่วคราว → ลองซ้ำเจ้าเดิม ``TEMPORARY_RETRIES`` ครั้ง แล้วค่อยสลับ
    - **โจทย์ผิด → โยนออกทันที ไม่สลับ** (สลับไปก็ผิดเหมือนกัน แถมจ่ายสองเจ้า)
    - ครบทุกเจ้า → ``AllProvidersUnavailable`` ที่บอกว่าเจ้าไหนพังเพราะอะไร

    ``calls`` = ตารางฟังก์ชันที่สร้างไว้แล้ว (Team Mode ส่ง ``_calls`` ของตัวเองเข้ามา
    เพื่อไม่ต้องสร้าง client ใหม่ทุก call และเพื่อให้เทสต์เสียบ call ปลอมได้)
    """
    failures: dict[str, str] = {}
    for name in provider_chain(primary):
        call = calls.get(name) if calls is not None else BUILDERS[name]()
        if call is None:
            failures[name] = NO_KEY_REASON
            continue
        for attempt in range(1 + TEMPORARY_RETRIES):
            try:
                # ผ่าน `_guard` อีกชั้นเผื่อ call ที่ถูกเสียบเข้ามาโยน exception ดิบของ SDK
                # (builder ของเราจำแนกให้แล้ว แต่ที่นี่คือจุดเดียวที่ตัดสินใจ จึงต้องกันไว้)
                # `c=call` ผูกค่าตอนสร้าง lambda — `call` เป็นตัวแปรของลูป (ruff B023)
                return _as_llm_reply(_guard(name, lambda c=call: c(system, prompt)), name)
            except LlmRequestError:
                raise
            except LlmAccountError as exc:
                failures[name] = f"บัญชีใช้ไม่ได้ ({exc.body})"
                break
            except LlmTemporaryError as exc:
                failures[name] = f"ขัดข้องชั่วคราว ({exc.body})"
                if attempt + 1 < 1 + TEMPORARY_RETRIES and RETRY_SLEEP_SECONDS > 0:
                    time.sleep(RETRY_SLEEP_SECONDS)
    raise AllProvidersUnavailable(failures)


def ping(provider: str) -> LLMReply:
    """เรียกสั้นที่สุดเพื่อดูว่าเจ้านี้ใช้ได้จริงไหม — ปุ่ม "ทดสอบ" ของหน้า Settings.

    **ยิงเจ้านั้นตรง ๆ ไม่ผ่าน `call_chain`** เพราะต้องรู้ผลของเจ้านั้นจริง ไม่ใช่ผลของตัวสำรอง
    """
    builder = BUILDERS.get(provider)
    if builder is None:
        raise LlmRequestError(provider, f"ไม่รู้จักผู้ให้บริการ '{provider}'")
    call = builder()
    if call is None:
        raise LlmAccountError(provider, "ยังไม่ได้ตั้งคีย์ของผู้ให้บริการนี้")
    return _as_llm_reply(call("ตอบสั้นที่สุดเท่าที่ทำได้", "ping"), provider)
