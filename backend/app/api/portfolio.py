"""GET /api/portfolio — ภาพรวมทุกโปรเจกต์สำหรับ Dashboard (Blueprint §13)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent import Agent
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.task import Task

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
def portfolio(db: Session = Depends(get_db)) -> dict:
    projects = db.execute(select(Project).order_by(Project.created_at)).scalars().all()

    # นับ task ต่อ (project, status) รอบเดียว
    counts_rows = db.execute(
        select(Task.project_id, Task.status, func.count(Task.id)).group_by(
            Task.project_id, Task.status
        )
    ).all()
    counts: dict[str, dict[str, int]] = {}
    for project_id, status, n in counts_rows:
        counts.setdefault(str(project_id), {})[status] = n

    # deploy ล่าสุดต่อโปรเจกต์ (ตารางยังว่างจนกว่า Sprint 4 — โครงสร้างพร้อมแล้ว)
    deployments = db.execute(
        select(Deployment).order_by(Deployment.created_at.desc())
    ).scalars().all()
    last_deploy: dict[str, Deployment] = {}
    for d in deployments:
        last_deploy.setdefault(str(d.project_id), d)

    agents = db.execute(select(Agent)).scalars().all()

    return {
        "projects": [
            {
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "status": p.status,
                "task_counts": counts.get(str(p.id), {}),
                "total_tasks": sum(counts.get(str(p.id), {}).values()),
                "last_deployment": (
                    {
                        "id": str(d.id),
                        "status": d.status,
                        "environment": d.environment,
                        "created_at": d.created_at.isoformat(),
                    }
                    if (d := last_deploy.get(str(p.id)))
                    else None
                ),
            }
            for p in projects
        ],
        "agents": [
            {
                "id": str(a.id),
                "name": a.name,
                "role": a.role,
                "mode": a.mode,
                "status": a.status,
            }
            for a in agents
        ],
    }
