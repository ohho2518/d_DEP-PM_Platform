"""API routers (FastAPI)."""
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router

__all__ = ["projects_router", "tasks_router"]
