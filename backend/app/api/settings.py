"""`/api/settings/llm` — ตั้งคีย์/ลำดับสำรองของผู้ให้บริการ AI จากหน้าเว็บ + ปุ่มทดสอบ.

เกิดจากใบสั่งงาน 2026-08-06: วันที่เครดิตหมด การสลับไปเจ้าสำรองต้องทำได้**ทันที**
ไม่ใช่ต้องเปิดไฟล์ `.env` แล้ว restart backend กลางวิกฤต

🔒 **อ่อนไหวที่สุดในระบบ** — endpoint กลุ่มนี้อ่าน/เขียนคีย์จริง และระบบนี้ **ยังไม่มี
authentication** ⇒ ต้อง bind `127.0.0.1` เท่านั้น (docs/SECURITY.md) ·
ขาออก **ไม่มีคีย์เต็มเด็ดขาด** (mask อย่างเดียว) และห้าม log ค่าคีย์
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, status

from app.agents.providers import (
    BUILDERS,
    PROVIDER_ENV,
    LlmAccountError,
    LlmError,
    LlmRequestError,
    LlmTemporaryError,
    ping,
)
from app.config import get_settings
from app.schemas.settings import (
    LlmSettingsRead,
    LlmSettingsUpdate,
    ProviderStatus,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderTestResult,
)
from app.services.env_file import apply_to_settings, write_env

router = APIRouter(prefix="/api/settings", tags=["settings"])

#: ตัวอักษรท้ายคีย์ที่ยอมให้เห็น — พอให้คนยืนยันว่า "ใช่คีย์ตัวที่ตั้งใจ" โดยไม่เผยของจริง
MASK_VISIBLE_CHARS = 4

#: สิ่งที่ทำได้เมื่อถึงเพดานค่าใช้จ่าย (§5) — ตรงกับ `config.llm_budget_action`
BUDGET_ACTIONS = ("warn", "stop")


def _mask(key: str) -> str:
    if not key:
        return ""
    tail = key[-MASK_VISIBLE_CHARS:] if len(key) > MASK_VISIBLE_CHARS else key
    return f"{key[:3]}…{tail}" if len(key) > MASK_VISIBLE_CHARS + 3 else f"…{tail}"


def _current() -> LlmSettingsRead:
    settings = get_settings()
    keys = settings.provider_keys
    models = settings.provider_models
    prices = settings.provider_prices
    return LlmSettingsRead(
        provider=settings.llm_provider,
        fallbacks=settings.llm_fallback_list,
        budget_usd=settings.llm_budget_usd,
        budget_action=settings.llm_budget_action,
        providers=[
            ProviderStatus(
                name=name,
                model=models.get(name, ""),
                key_set=bool(keys.get(name)),
                key_masked=_mask(keys.get(name, "")),
                price_in=prices.get(name, (0.0, 0.0))[0],
                price_out=prices.get(name, (0.0, 0.0))[1],
            )
            for name in BUILDERS
        ],
    )


def _known_provider(name: str) -> str:
    key = name.strip().lower()
    if key not in BUILDERS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ไม่รู้จักผู้ให้บริการ '{name}' — ที่รองรับ: {', '.join(BUILDERS)}",
        )
    return key


@router.get("/llm", response_model=LlmSettingsRead)
def read_llm_settings() -> LlmSettingsRead:
    """ค่าปัจจุบัน — คีย์เป็นแบบ mask เท่านั้น."""
    return _current()


@router.put("/llm", response_model=LlmSettingsRead)
def update_llm_settings(payload: LlmSettingsUpdate) -> LlmSettingsRead:
    """บันทึกลง `backend/.env` แล้วมีผลทันที (ไม่ต้อง restart).

    ตัวที่ไม่ได้ส่งมาจะไม่ถูกแตะ — ดูเหตุผลใน `LlmSettingsUpdate`
    """
    values: dict[str, str] = {}
    for name, key in payload.keys.items():
        values[PROVIDER_ENV[_known_provider(name)][0]] = key.strip()
    for name, model in payload.models.items():
        model = model.strip()
        if model:  # ชื่อรุ่นว่าง = ไม่ตั้งใจลบ (ระบบไม่มีค่าปริยายให้ถอยไป)
            values[PROVIDER_ENV[_known_provider(name)][1]] = model
    if payload.provider is not None:
        values["LLM_PROVIDER"] = _known_provider(payload.provider)
    if payload.fallbacks is not None:
        values["LLM_FALLBACKS"] = ",".join(_known_provider(name) for name in payload.fallbacks)
    if payload.budget_usd is not None:
        values["LLM_BUDGET_USD"] = f"{payload.budget_usd:g}"
    if payload.budget_action is not None:
        action = payload.budget_action.strip().lower()
        if action not in BUDGET_ACTIONS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"budget_action ต้องเป็น {' หรือ '.join(BUDGET_ACTIONS)} เท่านั้น",
            )
        values["LLM_BUDGET_ACTION"] = action

    if values:
        write_env(values)
        apply_to_settings(values)
    return _current()


def _kind_of(exc: LlmError) -> str:
    if isinstance(exc, LlmAccountError):
        return "account"
    if isinstance(exc, LlmTemporaryError):
        return "temporary"
    if isinstance(exc, LlmRequestError):
        return "request"
    return "unknown"


def _test_one(name: str) -> ProviderTestResult:
    """ยิงจริงหนึ่งครั้งแบบสั้นที่สุด — ใช้ `classify_error` ชุดเดียวกับตอนทำงานจริง."""
    started = time.perf_counter()
    try:
        reply = ping(name)
    except LlmError as exc:
        return ProviderTestResult(
            provider=name,
            ok=False,
            kind=_kind_of(exc),
            detail=exc.body,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    return ProviderTestResult(
        provider=name,
        ok=True,
        model=reply.model,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


@router.post("/llm/test", response_model=ProviderTestResponse)
def test_llm_providers(payload: ProviderTestRequest) -> ProviderTestResponse:
    """ทดสอบว่าคีย์ใช้ได้จริงไหม — ไม่ระบุเจ้า = ทดสอบทุกเจ้าที่รองรับ.

    ยิงเจ้านั้น **ตรง ๆ ไม่ผ่านลำดับสำรอง** เพราะต้องรู้ผลของเจ้านั้นจริง ๆ
    """
    names = [_known_provider(payload.provider)] if payload.provider else list(BUILDERS)
    return ProviderTestResponse(results=[_test_one(name) for name in names])
