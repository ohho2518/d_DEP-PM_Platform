"""API routers (FastAPI)."""
from app.api.agent_messages import router as agent_messages_router
from app.api.ceo import router as ceo_router
from app.api.deployments import router as deployments_router
from app.api.portfolio import router as portfolio_router
from app.api.projects import router as projects_router
from app.api.settings import router as settings_router
from app.api.tasks import router as tasks_router

__all__ = [
    "projects_router",
    "tasks_router",
    "agent_messages_router",
    "portfolio_router",
    "deployments_router",
    "ceo_router",
    "settings_router",
]
