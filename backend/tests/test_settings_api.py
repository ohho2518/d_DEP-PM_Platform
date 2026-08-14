"""หน้า Settings — ตั้งคีย์/ลำดับสำรองของผู้ให้บริการ AI (ใบสั่งงาน 2026-08-06).

⚠️ ทุกเทสต์ในไฟล์นี้ชี้ `.env` ไปที่ `tmp_path` — **ห้ามแตะ `backend/.env` ของจริง**
(ไฟล์นั้นมีคีย์จริงของผู้ใช้ · WORKING_RULES Rule 8)
"""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.services import env_file


@pytest.fixture
def env_at(tmp_path, monkeypatch):
    """สร้าง `.env` ปลอมพร้อมคอมเมนต์/ตัวแปรอื่น แล้วบังคับให้ service เขียนที่ไฟล์นั้น."""
    path = tmp_path / ".env"
    path.write_text(
        "# DEP-PM backend env\n"
        "DATABASE_URL=sqlite:///./dep_pm.db\n"
        "\n"
        "# --- AI ---\n"
        "ANTHROPIC_API_KEY=sk-ant-เดิม-1234\n"
        "CLAUDE_MODEL=claude-sonnet-5\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(env_file, "env_path", lambda: path)
    return path


def test_get_never_returns_the_full_key(client, monkeypatch):
    """คีย์ห้ามออกจาก API แบบเต็ม — เห็นได้แค่พอยืนยันว่าใช่ตัวที่ตั้งใจ."""
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-ant-ความลับ-9f3a")

    body = client.get("/api/settings/llm").json()
    anthropic = next(p for p in body["providers"] if p["name"] == "anthropic")

    assert anthropic["key_set"] is True
    assert "ความลับ" not in anthropic["key_masked"]
    assert anthropic["key_masked"].endswith("9f3a")
    assert "sk-ant-ความลับ-9f3a" not in client.get("/api/settings/llm").text


def test_get_reports_providers_without_a_key(client):
    body = client.get("/api/settings/llm").json()  # conftest ล้างคีย์ทุกเจ้าไว้
    assert [p["key_set"] for p in body["providers"]] == [False, False, False]
    assert all(p["key_masked"] == "" for p in body["providers"])


def test_saving_without_a_key_keeps_the_existing_one(client, env_at):
    """เปิดหน้าเว็บแล้วกดบันทึกเฉย ๆ **ต้องไม่ลบคีย์ทิ้ง** (ไม่ส่ง = ไม่แตะ)."""
    resp = client.put("/api/settings/llm", json={"provider": "anthropic"})

    assert resp.status_code == 200
    assert "ANTHROPIC_API_KEY=sk-ant-เดิม-1234" in env_at.read_text(encoding="utf-8")


def test_sending_an_empty_key_clears_it(client, env_at):
    """ส่งสตริงว่าง = ตั้งใจลบ — ต้องต่างจาก 'ไม่ส่ง' อย่างชัดเจน."""
    client.put("/api/settings/llm", json={"keys": {"anthropic": ""}})

    assert "ANTHROPIC_API_KEY=\n" in env_at.read_text(encoding="utf-8")
    assert get_settings().anthropic_api_key == ""


def test_saving_keeps_comments_and_other_variables(client, env_at):
    client.put("/api/settings/llm", json={"keys": {"openai": "sk-openai-ใหม่"}})

    text = env_at.read_text(encoding="utf-8")
    assert "# DEP-PM backend env" in text  # คอมเมนต์ไม่หาย
    assert "DATABASE_URL=sqlite:///./dep_pm.db" in text  # ตัวแปรอื่นไม่หาย
    assert text.count("OPENAI_API_KEY=") == 1  # ต่อท้ายครั้งเดียว ไม่ซ้ำ
    assert "OPENAI_API_KEY=sk-openai-ใหม่" in text


def test_written_env_has_no_bom(client, env_at):
    """BOM ที่หัวไฟล์ทำให้ key บรรทัดแรกอ่านไม่ออกแล้วแอปตกไปใช้ค่าปริยาย **เงียบ ๆ**
    (WORKING_RULES §6.1ข — เจอจริงกับ `STT_MODEL` มาแล้ว)."""
    client.put("/api/settings/llm", json={"keys": {"anthropic": "sk-ใหม่"}})

    assert env_at.read_bytes()[:3] != b"\xef\xbb\xbf"


def test_changes_take_effect_without_restart(client, env_at):
    """กรอกแล้วต้องใช้ได้ทันที — ตอนเครดิตหมดจริงไม่มีใครอยากมา restart backend."""
    client.put(
        "/api/settings/llm",
        json={
            "keys": {"openai": "sk-openai-live"},
            "provider": "openai",
            "fallbacks": ["anthropic"],
        },
    )

    settings = get_settings()
    assert settings.openai_api_key == "sk-openai-live"
    assert settings.llm_provider == "openai"
    assert settings.llm_fallback_list == ["anthropic"]
    assert client.get("/health").json()["llm_providers"] == ["openai"]


def test_unknown_provider_is_rejected(client, env_at):
    resp = client.put("/api/settings/llm", json={"keys": {"ไม่มีเจ้านี้": "x"}})
    assert resp.status_code == 400
    assert "ไม่รู้จักผู้ให้บริการ" in resp.json()["detail"]


def test_backup_is_written_before_overwriting(client, env_at, monkeypatch, tmp_path):
    """Rule 1: สำรองไฟล์เดิมก่อนเขียนทับเสมอ."""
    backups: list[str] = []
    monkeypatch.setattr(
        env_file, "backup_env", lambda path: backups.append(path.read_text(encoding="utf-8"))
    )
    client.put("/api/settings/llm", json={"keys": {"anthropic": "sk-ใหม่"}})

    assert backups and "sk-ant-เดิม-1234" in backups[0]


def test_test_button_reports_missing_key_without_touching_the_network(client):
    """ไม่มีคีย์ = ตอบทันทีว่า `account` — ต้องไม่พยายามยิงออกเน็ต (เทสต์ทั้ง suite ต้อง hermetic)."""
    body = client.post("/api/settings/llm/test", json={"provider": "anthropic"}).json()

    assert body["results"][0] == {
        "provider": "anthropic",
        "ok": False,
        "model": "",
        "latency_ms": body["results"][0]["latency_ms"],
        "kind": "account",
        "detail": "ยังไม่ได้ตั้งคีย์ของผู้ให้บริการนี้",
    }


def test_test_button_covers_every_provider_when_none_is_given(client):
    body = client.post("/api/settings/llm/test", json={}).json()
    assert [r["provider"] for r in body["results"]] == ["anthropic", "openai", "google"]
