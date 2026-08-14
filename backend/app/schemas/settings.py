"""Pydantic schemas ของหน้า Settings (ผู้ให้บริการ AI).

🔒 **คีย์ไม่เคยออกจาก API แบบเต็ม** — ขาออกมีแต่ `key_masked`/`key_set` เท่านั้น
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderStatus(BaseModel):
    """สถานะของผู้ให้บริการหนึ่งเจ้าเท่าที่ปลอดภัยจะบอกออกไป."""

    name: str
    model: str
    key_set: bool
    key_masked: str = ""  # เช่น "sk-a…4f2a" · ว่าง = ยังไม่ได้ตั้งคีย์


class LlmSettingsRead(BaseModel):
    provider: str  # ตัวหลัก
    fallbacks: list[str]  # ลำดับสำรอง
    providers: list[ProviderStatus]


class LlmSettingsUpdate(BaseModel):
    """ค่าใหม่จากหน้า Settings.

    ⚠️ **ไม่ส่ง key มา = ไม่แตะของเดิม · ส่งสตริงว่าง = ตั้งใจลบ** — สองกรณีนี้ต้องต่างกัน
    ไม่งั้นแค่เปิดหน้าเว็บแล้วกดบันทึกจะลบคีย์ทิ้งทั้งหมด
    """

    provider: str | None = None
    fallbacks: list[str] | None = None
    #: ชื่อผู้ให้บริการ -> คีย์ใหม่ (ไม่ส่ง = คงเดิม)
    keys: dict[str, str] = Field(default_factory=dict)
    #: ชื่อผู้ให้บริการ -> ชื่อรุ่นใหม่ (ไม่ส่ง = คงเดิม)
    models: dict[str, str] = Field(default_factory=dict)


class ProviderTestRequest(BaseModel):
    #: ไม่ระบุ = ทดสอบทุกเจ้าที่ตั้งคีย์ไว้
    provider: str | None = None


class ProviderTestResult(BaseModel):
    provider: str
    ok: bool
    model: str = ""
    latency_ms: int = 0
    #: ชนิดปัญหาเมื่อ ok=false — account | temporary | request | unknown
    kind: str | None = None
    detail: str = ""


class ProviderTestResponse(BaseModel):
    results: list[ProviderTestResult]
