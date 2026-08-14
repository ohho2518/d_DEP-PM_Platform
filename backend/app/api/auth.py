"""ประตูหน้าบ้านของ API — shared token ตัวเดียวสำหรับผู้ใช้คนเดียว (2026-08-14).

**ทำไมเพิ่งมี:** ระบบนี้เป็น single-user บน localhost มาตลอด จึงยอมรับว่าไม่มี auth ได้ ·
แต่ตั้งแต่มีหน้า `/settings` ที่ **แก้คีย์ของผู้ให้บริการ AI ได้** ใครก็ตามที่ยิงถึงพอร์ตนี้
เปลี่ยน/ลบคีย์ได้ทันที ⇒ auth กลายเป็นเงื่อนไขก่อนเปิดพอร์ตออกนอกเครื่อง (RISK #5.2)

**ยังเป็น token เดียว ไม่ใช่ระบบผู้ใช้** — Blueprint §15 วางไว้ว่าจะมี RBAC ตอน multi-user
ที่นี่แก้แค่ปัญหาที่มีจริงวันนี้: กันคนนอกยิงเข้ามา · ไม่ตั้งค่า = ไม่ตรวจ (dev เหมือนเดิม)
"""
from __future__ import annotations

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings

TOKEN_HEADER = "X-DEP-PM-Token"

#: เส้นทางที่ไม่ต้องมี token — probe ของ monitor + หน้าเอกสารของ FastAPI (ไม่มีข้อมูลผู้ใช้)
OPEN_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"})

#: callback ของ CI มี **ความลับของตัวเอง** อยู่แล้ว (`X-DEP-PM-Secret` — Risk #1)
#: ถ้าบังคับ token ตัวนี้ด้วย workflow ที่ติดตั้งไปแล้วทุกตัวจะพังทันที
_CI_CALLBACK_PREFIX = "/api/deployments/"


def _is_open(request: Request) -> bool:
    path = request.url.path
    if path in OPEN_PATHS or not path.startswith("/api/"):
        return True
    # CORS preflight ไม่พก header ที่ custom มาด้วย — บล็อกแล้ว browser จะเรียกจริงไม่ได้เลย
    if request.method == "OPTIONS":
        return True
    return request.method == "PATCH" and path.startswith(_CI_CALLBACK_PREFIX)


async def require_api_token(request: Request, call_next):
    """Middleware: ตรวจ `X-DEP-PM-Token` ทุก `/api/*` เมื่อ `API_TOKEN` ถูกตั้งค่า.

    อ่าน settings ใหม่ทุก request เพราะหน้า Settings แก้ค่าได้ระหว่างรัน (ไม่ cache ไว้ตอน import)
    · เทียบเป็น **bytes** ผ่าน `hmac.compare_digest` — เวอร์ชัน str รับแต่ ASCII ทำให้ token
    ภาษาไทยกลายเป็น 500 แทน 401 (บทเรียนจริงจาก callback secret เมื่อ 2026-08-03)
    """
    token = get_settings().api_token.strip()
    if token and not _is_open(request):
        supplied = request.headers.get(TOKEN_HEADER, "")
        if not hmac.compare_digest(supplied.encode("utf-8"), token.encode("utf-8")):
            return JSONResponse(
                status_code=401,
                content={"detail": f"ต้องแนบ header {TOKEN_HEADER} ให้ตรงกับ API_TOKEN"},
            )
    return await call_next(request)
