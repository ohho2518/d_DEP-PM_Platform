"""LLM provider wrappers สำหรับ Team Mode (Sprint 4, Blueprint §8-9).

แต่ละ provider เป็นฟังก์ชัน `(system, prompt) -> LLMReply` — lazy import SDK เพื่อให้ระบบ
รันได้แม้ไม่ติดตั้ง/ไม่มี key ของ provider นั้น (คืน None = ใช้ไม่ได้ ให้ chain
fallback ใน runtime ตัดสินใจต่อ)
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class LLMReply:
    """ผลจาก LLM หนึ่ง call พร้อม token usage (debt #7 — คุมงบก่อนเปิด Team Mode)."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0


# Callable ที่พร้อมใช้ หรือ None ถ้า provider นั้น config ไม่ครบ
# (รับ str กลับได้ด้วย — เทสต์/custom call เก่าคืน str ล้วน; runtime._as_reply normalize ให้)
ProviderCall = Callable[[str, str], "LLMReply | str"]


def build_anthropic() -> ProviderCall | None:
    settings = get_settings()
    if not settings.anthropic_api_key.strip():
        return None
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def call(system: str, prompt: str) -> LLMReply:
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
        )

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

    client = OpenAI(api_key=settings.openai_api_key)

    def call(system: str, prompt: str) -> LLMReply:
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
        )

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

    client = genai.Client(api_key=settings.gemini_api_key)

    def call(system: str, prompt: str) -> LLMReply:
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
        )

    return call


BUILDERS: dict[str, Callable[[], ProviderCall | None]] = {
    "anthropic": build_anthropic,
    "openai": build_openai,
    "google": build_gemini,
}
