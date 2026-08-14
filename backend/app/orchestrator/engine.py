"""Solo-Mode Orchestrator (Sprint 2, DEVELOPMENT_PLAN §6).

ดึง task สถานะ ``planned`` ของโปรเจกต์ทีละตัว (เฉพาะที่ dependency เสร็จแล้ว) แล้วไล่ตาม
State Machine: assigned → in_progress → review → done หรือ revision loop จนถึง
MAX_REVISIONS → escalated. ทุก handoff/result/review_comment ลง Message Bus (ADR-03)
และทุก transition ลง audit_log ผ่าน state machine.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.providers import AllProvidersUnavailable
from app.agents.routing import route_task
from app.agents.runtime import PersonaExecutor, ProviderUse, get_executor
from app.bus import clip_work, latest_work_by_task, publish
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

# เพดานผลงานของงานก่อนหน้าที่ส่งเป็น context (ตัวอักษร) — ต่อ 1 ชิ้น และรวมทั้งก้อน
# ราว ๆ 24,000 ตัวอักษร ≈ 8k token ของ input ซึ่งยังห่างจากเพดาน context ของโมเดลมาก
# แต่กันเคส task ปลายกราฟที่มีบรรพบุรุษสิบกว่าตัวไม่ให้ prompt บวมจนต้นทุนพุ่ง
UPSTREAM_WORK_CHAR_LIMIT = 6_000
UPSTREAM_CONTEXT_CHAR_LIMIT = 24_000

# เหตุผล escalate ไปโผล่เป็น bullet เดียวในรายงานถึง d_CEO — ยาวกว่านี้อ่านไม่รู้เรื่อง
# (คอมเมนต์เต็มยังอยู่ใน `last_comment` และใน Message Log ของบอร์ด)
ESCALATION_REASON_CHAR_LIMIT = 400


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


def planned_task_count(db: Session, project_id: uuid.UUID) -> int:
    """จำนวน task สถานะ ``planned`` ตอนนี้ — ใช้ตั้ง "เป้า" ของรอบรันเพื่อคำนวณ progress.

    ไม่ใช่จำนวนที่จะรันได้จริงเสมอไป: ตัวที่ dependency ติด escalated จะค้าง ``planned``
    ตลอดรอบ (เจตนา — เห็นได้จาก ``processed`` < ``total`` ตอนรอบจบ)
    """
    return int(
        db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id, Task.status == TaskStatus.PLANNED.value)
        ).scalar_one()
    )


def _ancestor_tasks(db: Session, task: Task) -> list[Task]:
    """ทุก task ที่อยู่ "เหนือ" task นี้ในกราฟพึ่งพา (dependency ตรง + ของมันต่อ ๆ ไป).

    คืนแบบ **topological**: ต้นน้ำมาก่อนปลายน้ำเสมอ (DFS post-order) — อ่านต่อกันเป็นเรื่องได้
    · ห้ามเรียงด้วย ``created_at``: นาฬิกาบน Windows หยาบพอที่ task ซึ่งถูกสร้างติด ๆ กัน
    จะได้เวลาเท่ากัน แล้วลำดับจะสลับไปมา (เจอจริงตอนเขียนเทสต์ 2026-08-03)
    · ``seen`` กันกราฟที่มีวง (แผนจาก LLM อ้างวนกันเองได้)
    """
    rows = (
        db.execute(select(Task).where(Task.project_id == task.project_id)).scalars().all()
    )
    by_id = {str(row.id): row for row in rows}
    ordered: list[Task] = []
    seen: set[str] = {str(task.id)}

    def visit(node: Task) -> None:
        for dep_id in node.depends_on or []:
            dep = by_id.get(dep_id)
            if dep is None or dep_id in seen:
                continue
            seen.add(dep_id)
            visit(dep)  # dependency ของ dependency ออกก่อน
            ordered.append(dep)

    visit(task)
    return ordered


def upstream_context(db: Session, task: Task) -> str | None:
    """ผลงานล่าสุดของ task ที่อยู่เหนือขึ้นไป **ทั้งกราฟ** — ประกอบเป็นข้อความให้ agent อ่าน.

    ทำไมต้องมี: ก่อนหน้านี้ agent เห็นแค่ title/spec ของ task ตัวเอง งานประเภท
    "รวมเนื้อหาจากงานก่อนหน้า" จึงผลิตได้แค่โครงเปล่าแล้วถูก reviewer ปฏิเสธจน escalate
    (UAT 2026-08-03: agent เขียนไว้เองว่า "ไม่มีเนื้อหาต้นฉบับของ T2, T3, T4 แนบมาด้วย")

    คุมขนาดสองชั้นเพราะ context ทั้งกราฟโตเร็ว: ต่อชิ้น ``UPSTREAM_WORK_CHAR_LIMIT``
    และรวม ``UPSTREAM_CONTEXT_CHAR_LIMIT`` — ตัดตัวเก่าสุดออกก่อน (ตัวใกล้ตัวเรามักสำคัญกว่า)
    """
    ancestors = _ancestor_tasks(db, task)
    if not ancestors:
        return None
    works = latest_work_by_task(db, [t.id for t in ancestors])
    if not works:
        return None

    blocks: list[str] = []
    budget = UPSTREAM_CONTEXT_CHAR_LIMIT
    dropped = 0
    for ancestor in reversed(ancestors):  # ใกล้ตัวเราก่อน แล้วค่อยไล่ขึ้นไป
        work = works.get(ancestor.id)
        if not work:
            continue
        block = f"### {ancestor.title}\n{clip_work(work, UPSTREAM_WORK_CHAR_LIMIT)}"
        if len(block) > budget:
            dropped += 1
            continue
        budget -= len(block)
        blocks.append(block)
    if not blocks:
        return None

    blocks.reverse()  # คืนลำดับตามแผน (เก่า → ใหม่) ให้อ่านต่อกันเป็นเรื่อง
    header = (
        "ผลงานจริงของงานก่อนหน้าที่ task นี้ต้องใช้ต่อ — ใช้เนื้อหาข้างล่างนี้ทำงาน "
        "**ห้ามสมมติเนื้อหาเองหรือใส่ placeholder**"
    )
    if dropped:
        header += f"\n(ตัดผลงานของงานเก่า {dropped} รายการออกเพราะยาวเกินเพดานรวม)"
    return f"{header}\n\n" + "\n\n".join(blocks)


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


def _maybe_auto_deploy(db: Session, task: Task) -> None:
    """Task done + AUTO_DEPLOY_ENABLED => สร้าง staging deployment (Blueprint §12).

    เส้นทาง auto ยิงได้เฉพาะ staging เท่านั้น — production ต้องสั่งมือผ่าน
    POST /api/deployments (Manual Approval Gate). Import ภายในฟังก์ชันกัน circular
    (services/deploy ไม่รู้จัก orchestrator อยู่แล้ว แต่กันไว้ตาม dependency direction).
    """
    from app.config import get_settings
    from app.constants import DeploymentTrigger
    from app.services.deploy import create_deployment

    if not get_settings().auto_deploy_enabled:
        return
    create_deployment(
        db,
        project_id=task.project_id,
        task_id=task.id,
        environment="staging",
        triggered_by=DeploymentTrigger.AUTO,
        actor_id=ORCHESTRATOR_ID,
    )


def _escalate(
    db: Session, task: Task, *, audit_reason: str, reason: str, last_comment: str
) -> None:
    """หยุด task ไว้ที่ ``escalated`` แล้ว broadcast ให้คนเห็นบนบอร์ด/ในรายงานถึง d_CEO.

    เข้าทางนี้ได้ 2 เหตุ: review ไม่ผ่านครบ ``MAX_REVISIONS`` · reviewer ชี้ว่าต้องใช้คน
    (``needs_human``) — ``reason`` คือข้อความที่ `ceo_sync._escalation_reasons` หยิบไปแสดง
    """
    transition(
        db, task, TaskStatus.ESCALATED,
        actor_type=ActorType.AGENT, actor_id=ORCHESTRATOR_ID,
        reason=audit_reason,
    )
    publish(
        db,
        project_id=task.project_id,
        task_id=task.id,
        from_agent_id=ORCHESTRATOR_ID,
        to_agent_id=None,  # broadcast ถึงผู้ใช้/dashboard
        message_type=MessageType.QUESTION,
        payload={"escalated": True, "reason": reason, "last_comment": last_comment},
    )


def _provider_use(executor: PersonaExecutor) -> ProviderUse:
    """ใครทำงานชิ้นล่าสุด — executor ที่ไม่ได้เรียกโมเดล (deterministic/เทสต์) ไม่มี attribute นี้."""
    use = getattr(executor, "last_use", None)
    return use if isinstance(use, ProviderUse) else ProviderUse()


def _tag_work_product(work: str, used: ProviderUse) -> str:
    """ติดป้ายเมื่องานชิ้นนี้ทำด้วย **ตัวสำรอง** — คุณภาพและสไตล์ต่างกันจริง คนตรวจต้องรู้.

    ป้ายอยู่ในตัว work product เอง (ไม่ใช่แค่ payload) เพราะผลงานถูกส่งต่อเข้ารายงานถึง d_CEO
    และไปถึง QC — "ห้ามสลับเงียบ" ของใบสั่งงาน 2026-08-06 §4
    """
    if not used.degraded:
        return work
    return (
        f"{work}\n\n"
        f"> 🤖 ทำโดย {used.provider}/{used.model} — **ตัวสำรอง** "
        f"(ตัวหลัก `{used.primary}` ใช้ไม่ได้ตอนนั้น)"
    )


@contextmanager
def _llm_available(db: Session, task: Task) -> Iterator[None]:
    """ทุกผู้ให้บริการใช้ไม่ได้ → หยุดอย่างมีศักดิ์ศรี แล้วโยนต่อให้รอบรันจบเป็น ``failed``.

    - task ไป ``escalated`` **ไม่ค้าง ``in_progress``** ที่ต้องมาแก้มือทีหลัง
    - **commit ทันทีก่อนโยนต่อ** เพราะผู้เรียก (`services/runs.py`) จะ `db.rollback()`
      เมื่อรับ exception — ไม่งั้นการ escalate ที่เพิ่งบันทึกจะหายไปพร้อมกัน
      (จุดเดียวในไฟล์นี้ที่ commit เอง — ทางปกติยัง commit ที่ `run_project` ตามกติกา §9.1.3)
    """
    try:
        yield
    except AllProvidersUnavailable as exc:
        _escalate(
            db,
            task,
            audit_reason="llm providers unavailable",
            reason=(
                "ผู้ให้บริการ AI ใช้ไม่ได้ทั้งหมด — "
                f"{clip_work(str(exc), ESCALATION_REASON_CHAR_LIMIT)}"
            ),
            last_comment=str(exc),
        )
        db.commit()
        raise


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
    # ผลงานของงานก่อนหน้าไม่เปลี่ยนระหว่างรอบ revision — ประกอบครั้งเดียวพอ
    context = upstream_context(db, task)
    feedback: str | None = None
    while True:
        with _llm_available(db, task):
            work = executor.execute(task, role, feedback=feedback, context=context)
        used = _provider_use(executor)
        work = _tag_work_product(work, used)
        publish(
            db,
            project_id=task.project_id,
            task_id=task.id,
            from_agent_id=role.value,
            to_agent_id=AgentRole.REVIEWER.value,
            message_type=MessageType.RESULT,
            payload={
                "work": work,
                "revision": task.revision_count,
                "provider": used.provider,
                "model": used.model,
            },
        )
        transition(db, task, TaskStatus.REVIEW, actor_type=ActorType.AGENT, actor_id=role.value)

        with _llm_available(db, task):
            review = executor.review(task, work)
        reviewed_by = _provider_use(executor)
        publish(
            db,
            project_id=task.project_id,
            task_id=task.id,
            from_agent_id=AgentRole.REVIEWER.value,
            to_agent_id=role.value,
            message_type=MessageType.REVIEW_COMMENT,
            payload={
                "approved": review.approved,
                "comment": review.comment,
                "needs_human": review.needs_human,
                # QC ปลายทางต้องรู้ว่า "ตรวจด้วยรุ่นไหน" (ใบสั่งงาน 2026-08-06 §4)
                "provider": reviewed_by.provider,
                "model": reviewed_by.model,
            },
        )

        if review.approved:
            transition(
                db, task, TaskStatus.DONE,
                actor_type=ActorType.AGENT, actor_id=AgentRole.REVIEWER.value,
                reason="review approved",
            )
            _maybe_auto_deploy(db, task)
            break

        if review.needs_human:
            # งานติดเพราะขาดข้อมูล/สิทธิ์ที่ agent หามาเองไม่ได้ — วน revision ต่อไม่มีประโยชน์
            # (ได้คำตอบเดิม) และคำสั่ง "ไปตามข้อมูลมา" เคยบีบให้ agent เขียนว่า "escalate แล้ว"
            # ทั้งที่ทำไม่ได้ = กุการกระทำ · ไม่นับเป็น revision เพราะไม่ใช่ความผิดของงาน
            # (UAT รอบ 3 + QC ของ d_CEO 2026-08-03 — ดู runbook §7)
            _escalate(
                db, task,
                audit_reason="needs human input",
                reason=f"ต้องการข้อมูล/การตัดสินใจจากคน — {clip_work(review.comment, ESCALATION_REASON_CHAR_LIMIT)}",
                last_comment=review.comment,
            )
            break

        task.revision_count += 1
        if task.revision_count >= MAX_REVISIONS:
            # Escalation Rule: review fail ครบ MAX_REVISIONS → หยุดรอคน/Senior รับช่วง
            _escalate(
                db, task,
                audit_reason=f"review failed {task.revision_count} times",
                reason=f"review ไม่ผ่าน {task.revision_count} ครั้ง — ต้องการคนหรือ Senior Agent รับช่วง",
                last_comment=review.comment,
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
    on_outcome: Callable[[TaskOutcome], None] | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> RunSummary:
    """รัน task ที่ planned ทั้งหมดของโปรเจกต์จนหมด (หรือครบ ``max_tasks``).

    Commit หลังจบแต่ละ task เพื่อให้ dashboard เห็นความคืบหน้าและงานที่เสร็จแล้ว
    ไม่ rollback หากตัวถัดไปพัง.

    ``on_outcome`` ถูกเรียกหลัง commit ของแต่ละ task — ใช้รายงานความคืบหน้าออกไปข้างนอก
    (Phase 2: run manager อัปเดต progress ของรอบรัน) โดย engine ไม่ต้องรู้จักผู้ฟัง

    ``should_continue`` ถูกถาม **ก่อนหยิบ task ถัดไป** — คืน False = หยุดรอบรันตรงนั้น
    (ผู้ใช้กดยกเลิก) · จงใจไม่ตัดกลาง task: งานที่ agent ทำค้างจะกลายเป็นสถานะกำพร้า
    ต้องมาแก้มือ และเราจ่ายค่า token ไปแล้วโดยไม่ได้ผลงาน — engine ไม่รู้ว่าใครสั่งหยุด
    """
    executor = executor or get_executor()
    summary = RunSummary(project_id=str(project_id))

    while max_tasks is None or len(summary.outcomes) < max_tasks:
        if should_continue is not None and not should_continue():
            break
        task = _next_runnable(db, project_id)
        if task is None:
            break
        outcome = _run_task(db, task, executor)
        db.commit()
        summary.outcomes.append(outcome)
        if on_outcome is not None:
            on_outcome(outcome)

    return summary
