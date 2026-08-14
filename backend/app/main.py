"""FastAPI entry point for the DEP-PM backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.providers import available_providers, provider_chain
from app.api import (
    agent_messages_router,
    ceo_router,
    deployments_router,
    portfolio_router,
    projects_router,
    settings_router,
    tasks_router,
)
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="DEP-PM Platform API",
    version="0.1.0",
    description="AI-Native Project Management Platform — Sprint 1 (Foundation)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(agent_messages_router)
app.include_router(portfolio_router)
app.include_router(deployments_router)
app.include_router(ceo_router)
app.include_router(settings_router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe + ความพร้อมของสิ่งที่ต่อออกนอกตัวเอง.

    `ceo_enabled` = ตั้งค่าเชื่อม d_CEO ไว้ไหม (ออนไลน์จริงหรือไม่ดูที่ `/api/ceo/status`)
    `llm_providers` = ผู้ให้บริการ AI ที่ตั้งคีย์ไว้แล้ว **ตามลำดับที่จะถูกเรียก**
    (ใบสั่งงาน 2026-08-06 — ต้องดูออกจากภายนอกว่าตอนนี้บ้านนี้ยังมีใครทำงานให้ได้บ้าง)
    """
    return {
        "status": "ok",
        "agent_enabled": settings.agent_enabled,
        "ceo_enabled": settings.ceo_enabled,
        "llm_providers": available_providers(),
        "llm_chain": provider_chain(),
    }
