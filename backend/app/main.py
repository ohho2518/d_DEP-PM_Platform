"""FastAPI entry point for the DEP-PM backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent_messages_router, projects_router, tasks_router
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


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe + whether the PM Agent has a live API key configured."""
    return {"status": "ok", "agent_enabled": settings.agent_enabled}
