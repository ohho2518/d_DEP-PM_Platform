"""ลำดับสำรองของผู้ให้บริการ LLM + การแยกชนิด error (ใบสั่งงาน 2026-08-06 §3).

ทำไมต้องล็อกไว้: 2026-08-06 เครดิตบัญชี Anthropic หมด แล้วทั้ง eco หยุดพร้อมกัน **แบบเงียบ** —
งานไปกอง `rejected` ปนกับงานที่ QC ตีกลับจริง เจ้าของแยกไม่ออกว่าบัญชีพังหรืองานไม่ผ่าน
ตารางแยก error คือจุดที่พลาดแล้ว **ไม่มีอะไรมาเตือน** จึงต้องมีเทสต์ครบทุกแถว
"""
from __future__ import annotations

import pytest

from app.agents import providers
from app.agents.providers import (
    AllProvidersUnavailable,
    LlmAccountError,
    LlmRequestError,
    LlmTemporaryError,
    call_chain,
    classify_error,
    provider_chain,
)
from app.config import get_settings


class FakeSdkError(Exception):
    """เลียนแบบ exception ของ SDK: มี `status_code` + ข้อความเต็มของฝั่งผู้ให้บริการ."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    """ลองซ้ำได้ แต่อย่าให้ suite รอจริง."""
    monkeypatch.setattr(providers, "RETRY_SLEEP_SECONDS", 0)


@pytest.fixture
def chain_of(monkeypatch):
    """ตั้งตัวหลัก + ลำดับสำรองผ่าน settings (เหมือนที่ผู้ใช้ตั้งจากหน้า Settings)."""

    def _set(primary: str, fallbacks: str = "") -> None:
        settings = get_settings()
        monkeypatch.setattr(settings, "llm_provider", primary)
        monkeypatch.setattr(settings, "llm_fallbacks", fallbacks)

    return _set


# ---------------------------------------------------------------------------
# ตาราง §3 — แยกชนิดความผิดพลาด
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "message,status",
    [
        ("Your credit balance is too low to access the Anthropic API.", 400),  # เคสจริง 6 ส.ค.
        ("invalid x-api-key", 401),
        ("permission denied", 403),
        ("You exceeded your current quota, please check your plan and billing details.", 429),
    ],
)
def test_account_problems_are_classified_as_account_error(message, status):
    """400 ที่ข้อความบอกว่าเครดิต/บัญชีมีปัญหา = บัญชีใช้ไม่ได้ **ไม่ใช่โจทย์ผิด**."""
    error = classify_error("anthropic", FakeSdkError(message, status))
    assert isinstance(error, LlmAccountError)
    assert message[:20] in error.body  # เก็บ body ไม่ใช่แค่รหัสสถานะ (บทเรียน 29 ก.ค.)


@pytest.mark.parametrize("status", [429, 500, 502, 503, 529])
def test_rate_limit_and_server_errors_are_temporary(status):
    assert isinstance(classify_error("openai", FakeSdkError("overloaded", status)), LlmTemporaryError)


def test_network_error_without_status_is_temporary():
    """timeout/เน็ตหลุดไม่มีรหัสสถานะ — ต้องยังไปต่อได้ ไม่ใช่หยุดทั้งงาน."""
    assert isinstance(classify_error("google", TimeoutError("read timeout")), LlmTemporaryError)


@pytest.mark.parametrize(
    "message,status",
    [
        ("prompt is too long: 250000 tokens > 200000 maximum", 400),
        ("model not found", 404),
        ("Unprocessable Entity", 422),
    ],
)
def test_bad_request_is_request_error_not_provider_problem(message, status):
    assert isinstance(classify_error("anthropic", FakeSdkError(message, status)), LlmRequestError)


# ---------------------------------------------------------------------------
# ลำดับสำรอง
# ---------------------------------------------------------------------------
def test_account_error_switches_provider_without_retrying_the_dead_one(chain_of):
    """เครดิตหมด = ลองซ้ำเจ้าเดิมไม่มีประโยชน์ — ต้องเรียกเจ้าแรก **ครั้งเดียว** แล้วสลับ."""
    chain_of("anthropic", "openai")
    tries = {"anthropic": 0, "openai": 0}

    def dead(system, prompt):
        tries["anthropic"] += 1
        raise FakeSdkError("Your credit balance is too low", 400)

    def alive(system, prompt):
        tries["openai"] += 1
        return "งานเสร็จด้วยตัวสำรอง"

    reply = call_chain("sys", "prompt", calls={"anthropic": dead, "openai": alive})

    assert reply.text == "งานเสร็จด้วยตัวสำรอง"
    assert reply.provider == "openai"  # ต้องบอกได้ว่าใครทำ (ห้ามสลับเงียบ)
    assert tries == {"anthropic": 1, "openai": 1}


def test_temporary_error_retries_same_provider_before_switching(chain_of):
    chain_of("anthropic", "openai")
    tries = {"anthropic": 0, "openai": 0}

    def flaky(system, prompt):
        tries["anthropic"] += 1
        raise FakeSdkError("overloaded", 529)

    def alive(system, prompt):
        tries["openai"] += 1
        return "ok"

    call_chain("sys", "prompt", calls={"anthropic": flaky, "openai": alive})

    assert tries["anthropic"] == 1 + providers.TEMPORARY_RETRIES  # ถอยแล้วลองใหม่ก่อน
    assert tries["openai"] == 1


def test_request_error_stops_immediately_and_never_pays_a_second_provider(chain_of):
    """โจทย์ผิด → สลับไปก็ผิดเหมือนกัน แถมจ่ายสองเจ้า (ข้อ 3 ของ Verify ในใบสั่งงาน)."""
    chain_of("anthropic", "openai")
    tries = {"openai": 0}

    def too_long(system, prompt):
        raise FakeSdkError("prompt is too long: 250000 tokens > 200000 maximum", 400)

    def alive(system, prompt):
        tries["openai"] += 1
        return "ไม่ควรถูกเรียก"

    with pytest.raises(LlmRequestError):
        call_chain("sys", "prompt", calls={"anthropic": too_long, "openai": alive})

    assert tries["openai"] == 0


def test_provider_without_key_is_skipped_not_fatal(chain_of):
    """`calls[name] is None` = ยังไม่ได้ตั้งคีย์ → ข้ามไปเจ้าถัดไป."""
    chain_of("anthropic", "openai")
    reply = call_chain(
        "sys", "prompt", calls={"anthropic": None, "openai": lambda s, p: "สำรองทำงาน"}
    )
    assert reply.text == "สำรองทำงาน" and reply.provider == "openai"


def test_unknown_provider_name_in_env_is_ignored(chain_of):
    """ตั้งชื่อเจ้าผิดหนึ่งตัวไม่ควรทำให้ระบบล่ม — ข้ามเงียบ ๆ ตามแบบกลางของบ้าน."""
    chain_of("anthropic", "ไม่มีเจ้านี้,openai")
    assert provider_chain() == ["anthropic", "openai"]


def test_primary_argument_overrides_env_but_keeps_the_same_fallbacks(chain_of):
    """Team Mode: แต่ละบทบาทมีตัวหลักของตัวเอง แต่ลำดับสำรองใช้ชุดเดียวกันทั้งระบบ."""
    chain_of("anthropic", "google")
    assert provider_chain("openai") == ["openai", "google"]


def test_all_providers_down_reports_who_failed_and_why(chain_of):
    """ข้อความต้องบอกครบ ไม่ใช่ 'เรียก LLM ไม่สำเร็จ' ลอย ๆ แบบที่ทำให้ 6 ส.ค. หาสาเหตุไม่เจอ."""
    chain_of("anthropic", "openai")

    def dead_account(system, prompt):
        raise FakeSdkError("Your credit balance is too low", 400)

    def dead_temporary(system, prompt):
        raise FakeSdkError("service unavailable", 503)

    with pytest.raises(AllProvidersUnavailable) as exc_info:
        call_chain("sys", "prompt", calls={"anthropic": dead_account, "openai": dead_temporary})

    detail = str(exc_info.value)
    assert "anthropic" in detail and "credit balance" in detail
    assert "openai" in detail and "service unavailable" in detail
    assert exc_info.value.failures.keys() == {"anthropic", "openai"}


def test_no_provider_configured_at_all_is_still_a_clear_message(chain_of):
    chain_of("anthropic", "")
    with pytest.raises(AllProvidersUnavailable) as exc_info:
        call_chain("sys", "prompt", calls={"anthropic": None})
    assert "ยังไม่ได้ตั้งคีย์" in str(exc_info.value)


def test_available_providers_follows_the_keys_that_are_set(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    assert providers.available_providers() == ["openai"]  # conftest ล้างคีย์อื่นไว้แล้ว
