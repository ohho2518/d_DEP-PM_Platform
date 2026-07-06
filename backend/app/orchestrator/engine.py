"""Solo-Mode Orchestrator (Sprint 2, DEVELOPMENT_PLAN §6).

ดึง task สถานะ ``planned`` ของโปรเจกต์ทีละตัว (เฉพาะที่ dependency เสร็จแล้ว) แล้วไล่ตาม
State Machine: assigned → in_progress → review → done หรือ revision loop จนถึง
MAX_REVISIONS → escalated. ทุก handoff/result/review_comment ลง Message Bus (ADR-03)
และทุก transition ลง audit_log ผ่าน state machine.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.routing import route_task
from app.agents.runtime import PersonaExecutor, get_executor
from app.bus import publish
from app.constants import (
    MAX_REVISIONS,
    ActorType,
    AgentRole,
    AssigneeType,
    MessageType,
    TaskStatus,
)
from app.models.task import Task
from app.orchestrator.state_machine import transition

# Agent id ที่ seed ไว้ใน migration b2f1c0d3e4a5 (Claude Solo).
SOLO_AGENT_ID = "00000000-0000-0000-0000-000000000001"
ORCHESTRATOR_ID = "orchestrator"


@dataclass
class TaskOutcome:
    task_id: str
    title: str
    final_status: str
    revisions: int


@dataclass
class RunSummary:
    project_id: str
    outcomes: list[TaskOutcome] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for o in self.outcomes:
            result[o.final_status] = result.get(o.final_status, 0) + 1
        return result


def _deps_met(db: Session, task: Task) -> bool:
    """ทุก task ใน depends_on ต้องอยู่สถานะ done/deployed ก่อนจึงเริ่มได้."""
    if not task.depends_on:
        return True
    dep_ids = [uuid.UUID(d) for d in task.depends_on]
    deps = db.execute(select(Task).where(Task.id.in_(dep_ids))).scalars().all()
    finished = {TaskStatus.DONE.value, TaskStatus.DEPLOYED.value}
    return len(deps) == len(dep_ids) and all(d.status in finished for d in deps)


def _next_runnable(db: Session, project_id: uuid.UUID) -> Task | None:
    planned = (
        db.execute(
            select(Task)
            .where(Task.project_id == project_id, Task.status == TaskStatus.PLANNED.value)
            .order_by(Task.created_at)
        )
        .scalars()
        .all()
    )
    return next((t for t in planned if _deps_met(db, t)), None)


def _run_task(db: Session, task: Task, executor: PersonaExecutor) -> TaskOutcome:
    # 1) Routing + assign
    role = route_task(db, task)
    task.assignee_type = AssigneeType.AGENT.value
    task.assignee_id = SOLO_AGENT_ID
    task.agent_role = role.value
    transition(db, task, TaskStatus.ASSIGNED, actor_type=ActorType.AGENT, actor_id=ORCHESTRATOR_ID)
    publish(
        db,
        project_id=task.project_id,
        task_id=task.id,
        from_agent_id=ORCHESTRATOR_ID,
        to_agent_id=role.value,
        message_type=MessageType.HANDOFF,
        payload={"title": task.title, "spec": task.spec},
    )

    # 2) Work / review loop (Max Revision = MAX_REVISIONS — Blueprint §5)
    transition(db, task, TaskStatus.IN_PROGRESS, actor_type=ActorType.AGENT, actor_id=role.value)
    feedback: str | None = None
    while True:
        work = executor.execute(task, role, feedback=feedback)
        publish(
            db,
            project_id=task.project_id,
            task_id=task.id,
            from_agent_id=role.value,
            to_agent_id=AgentRole.REVIEWER.value,
            message_type=MessageType.RESULT,
            payload={"work": work, "revision": task.revision_count},
        )
        transition(db, task, TaskStatus.REVIEW, actor_type=ActorType.AGENT, actor_id=role.value)

        review = executor.review(task, work)
        publish(
            db,
            project_id=task.project_id,
            task_id=task.id,
            from_agent_id=AgentRole.REVIEWER.value,
            to_agent_id=role.value,
            message_type=MessageType.REVIEW_COMMENT,
            payload={"approved": review.approved, "comment": review.comment},
        )

        if review.approved:
            transition(
                db, task, TaskStatus.DONE,
                actor_type=ActorType.AGENT, actor_id=AgentRole.REVIEWER.value,
                reason="review approved",
            )
            break

        task.revision_count += 1
        if task.revision_count >= MAX_REVISIONS:
            # Escalation Rule: review fail ครบ MAX_REVISIONS → หยุดรอคน/Senior รับช่วง
            transition(
                db, task, TaskStatus.ESCALATED,
                actor_type=ActorType.AGENT, actor_id=ORCHESTRATOR_ID,
                reason=f"review failed {task.revision_count} times",
            )
            publish(
                db,
                project_id=task.project_id,
                task_id=task.id,
                from_agent_id=ORCHESTRATOR_ID,
                to_agent_id=None,  # broadcast ถึงผู้ใช้/dashboard
                message_type=MessageType.QUESTION,
                payload={
                    "escalated": True,
                    "reason": f"review ไม่ผ่าน {task.revision_count} ครั้ง — ต้องการคนหรือ Senior Agent รับช่วง",
                    "last_comment": review.comment,
                },
            )
            break

        feedback = review.comment
        transition(
            db, task, TaskStatus.IN_PROGRESS,
            actor_type=ActorType.AGENT, actor_id=ORCHESTRATOR_ID,
            reason=f"revision #{task.revision_count}",
        )

    return TaskOutcome(
        task_id=str(task.id),
        title=task.title,
        final_status=task.status,
        revisions=task.revision_count,
    )


def run_project(
    db: Session,
    project_id: uuid.UUID,
    *,
    executor: PersonaExecutor | None = None,
    max_tasks: int | None = None,
) -> RunSummary:
    """รัน task ที่ planned ทั้งหมดของโปรเจกต์จนหมด (หรือครบ ``max_tasks``).

    Commit หลังจบแต่ละ task เพื่อให้ dashboard เห็นความคืบหน้าและงานที่เสร็จแล้ว
    ไม่ rollback หากตัวถัดไปพัง.
    """
    executor = executor or get_executor()
    summary = RunSummary(project_id=str(project_id))

    while max_tasks is None or len(summary.outcomes) < max_tasks:
        task = _next_runnable(db, project_id)
        if task is None:
            break
        outcome = _run_task(db, task, executor)
        db.commit()
        summary.outcomes.append(outcome)

    return summary
