"""ประตูหน้าบ้าน (`API_TOKEN`) — เปิดใช้แล้วต้องกันจริง และต้องไม่กันของที่ต้องผ่าน.

ทำไมถึงมี: หน้า `/settings` แก้คีย์ของผู้ให้บริการ AI ได้ ⇒ ใครยิงถึงพอร์ตก็เปลี่ยนคีย์ได้
(RISK #5.2) · ไม่ตั้งค่า = ไม่ตรวจ ตามเดิมสำหรับ dev บน localhost
"""
from __future__ import annotations

import pytest

from app.api.auth import TOKEN_HEADER
from app.config import get_settings

TOKEN = "dep-pm-test-token-2026"


@pytest.fixture
def locked(monkeypatch):
    monkeypatch.setattr(get_settings(), "api_token", TOKEN)


def test_api_is_open_when_no_token_is_configured(client):
    """ค่าปริยายต้องไม่เปลี่ยนพฤติกรรมของ dev ที่ใช้อยู่."""
    assert client.get("/api/portfolio").status_code == 200


def test_locked_api_rejects_a_request_without_the_header(client, locked):
    resp = client.get("/api/portfolio")

    assert resp.status_code == 401
    assert TOKEN_HEADER in resp.json()["detail"]


def test_locked_api_accepts_the_right_token(client, locked):
    assert client.get("/api/portfolio", headers={TOKEN_HEADER: TOKEN}).status_code == 200


def test_wrong_token_is_rejected(client, locked):
    assert client.get("/api/portfolio", headers={TOKEN_HEADER: "not-the-token"}).status_code == 401


def test_thai_token_is_refused_at_startup_because_headers_cannot_carry_it():
    """ตั้ง token ไทย = ล็อกตัวเองออกจาก API — client ส่ง header ไม่ออกตั้งแต่ต้นทาง.

    เจอจริง 2026-08-14 ตอนเขียนเทสต์นี้เอง: httpx โยน `UnicodeEncodeError` ก่อนยิงด้วยซ้ำ
    ⇒ กันที่ config พร้อมบอกวิธีสร้าง token ที่ถูกต้อง ดีกว่าปล่อยให้ไปเจอตอนใช้จริง
    """
    import pydantic

    from app.config import Settings

    with pytest.raises(pydantic.ValidationError, match="ASCII"):
        Settings(api_token="โทเคนภาษาไทย")


def test_health_stays_open_for_probes(client, locked):
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["api_auth_enabled"] is True  # บอกได้ว่าล็อกแล้ว — ไม่ใช่ความลับ


def test_ci_callback_keeps_using_its_own_secret(client, locked):
    """`PATCH /api/deployments/:id` มี `X-DEP-PM-Secret` อยู่แล้ว — ถ้าบังคับ token ด้วย
    workflow ที่ติดตั้งไปแล้วทุกตัวจะพังทันที (เจตนาเดียวกับที่ยกเว้น /health)."""
    resp = client.patch(
        "/api/deployments/11111111-1111-1111-1111-111111111111",
        json={"status": "success"},
    )

    assert resp.status_code != 401  # ผ่านประตูหน้าบ้าน แล้วไปเจอด่านของตัวเอง/404
