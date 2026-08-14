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
    #: ราคาต่อ 1 ล้านโทเคน (USD) ที่ระบบใช้ **ประมาณการ** ค่าใช้จ่าย — แก้ได้ที่ `.env` เท่านั้น
    #: (อ่านอย่างเดียวตั้งใจ: เป็นตัวเลขที่ต้องยืนยันกับบิลจริง ไม่ใช่ค่าที่ควรกดเปลี่ยนเล่น)
    price_in: float = 0.0
    price_out: float = 0.0


class LlmSettingsRead(BaseModel):
    provider: str  # ตัวหลัก
    fallbacks: list[str]  # ลำดับสำรอง
    providers: list[ProviderStatus]
    #: เพดานค่าใช้จ่าย **ต่อโปรเจกต์** (USD) · 0 = ไม่จำกัด
    budget_usd: float = 0.0
    #: เกินเพดานแล้วทำอะไร — warn (เตือน) | stop (ไม่เริ่ม task ใหม่)
    budget_action: str = "warn"


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
    #: เพดานต่อโปรเจกต์ (USD) · 0 = ไม่จำกัด · ติดลบไม่รับ
    budget_usd: float | None = Field(default=None, ge=0)
    #: warn | stop — ค่าอื่นถูกปฏิเสธที่ router (ไม่ปล่อยให้ตกไปเป็น warn เงียบ ๆ)
    budget_action: str | None = None


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
