"""รับงานจาก d_CEO และรายงานผลกลับ (Phase 1 — AGENTS.md §3.1).

DEP-PM = **Team Lead R&D** ปลายสาย Vinit → d_Jarvis → d_CEO → ที่นี่

กติกาที่ไฟล์นี้บังคับ
1. **1 task ธุรกิจใน d_CEO = 1 project ที่นี่** (`projects.ceo_task_id` unique) — ไม่สร้าง
   ทะเบียนงานธุรกิจซ้อน task ย่อยบนบอร์ดเราคือรายละเอียดการทำงานเท่านั้น
2. **รายงานกลับได้แค่ `qc_review`** — ปิดงานเองไม่ได้ ทุกงานต้องผ่าน QC gate ของ d_CEO
   (มติ Vinit 2026-08-02 เคส d_MOS) · guardrail อยู่ใน `integrations/ceo_client.py`
3. **d_CEO ปิดอยู่ต้องไม่ทำให้งานฝั่งเราล้ม** — เส้นทางอัตโนมัติกลืน `CeoUnavailable` เงียบ

ชั้นนี้เป็น service: ถูกเรียกจาก `api/` เท่านั้น — orchestrator ไม่รู้จักไฟล์นี้
(จงใจ: engine ไม่ต้องแก้แม้แต่บรรทัดเดียวเพื่อรองรับการเชื่อมต่อ)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.pm import breakdown_requirement
from app.bus import clip_work, latest_work_by_task
from app.config import get_settings
from app.constants import ActorType, MessageType, ProjectType, TaskStatus
from app.integrations.ceo_client import (
    CEO_STATUS_IN_PROGRESS,
    CEO_STATUS_QC_REVIEW,
    CeoClient,
    CeoTask,
    CeoUnavailable,
)
from app.models.agent_message import AgentMessage
from app.models.project import Project
from app.models.task import Task
from app.services.audit import record_audit
from app.services.tasks import persist_task_plan

CEO_ACTOR_ID = "ceo-sync"

# เพดานตัวชิ้นงานที่แนบในรายงานถึง d_CEO (ตัวอักษร) — ต่อ 1 task และรวมทั้งรายงาน
REPORT_WORK_CHAR_LIMIT = 8_000
REPORT_WORK_TOTAL_CHAR_LIMIT = 40_000

# task ที่ orchestrator กำลังถืออยู่ (มีคน/agent ทำค้างอยู่จริง)
IN_FLIGHT_STATUSES = frozenset(
    {
        TaskStatus.ASSIGNED.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.REVIEW.value,
    }
)
FINISHED_STATUSES = frozenset({TaskStatus.DONE.value, TaskStatus.DEPLOYED.value})


@dataclass
class PullResult:
    ceo_task_id: str
    project_id: str
    name: str
    task_count: int
    breakdown_source: str | None
    acknowledged: bool  # แจ้ง d_CEO ว่ารับงานแล้ว (PATCH -> in_progress) สำเร็จไหม
    detail: str


@dataclass
class ReportResult:
    ready: bool  # งานในโปรเจกต์จบครบแล้วหรือยัง
    reported: bool  # ส่งถึง d_CEO สำเร็จไหม
    detail: str
    status_sent: str | None = None
    output: str | None = None
    counts: dict[str, int] = field(default_factory=dict)


def _project_name(input_text: str) -> str:
    """ชื่อโปรเจกต์จากบรรทัดแรกของคำสั่ง (คอลัมน์ name จำกัด 200 ตัวอักษร)."""
    first_line = next((line.strip() for line in input_text.splitlines() if line.strip()), "")
    if not first_line:
        return "งานจากเลขา (ไม่มีข้อความ)"
    return first_line[:200]


def list_inbox(db: Session, client: CeoClient) -> list[CeoTask]:
    """งาน `queued` ของทีม R&D ใน d_CEO ที่ยังไม่เคยถูกดึงมาที่นี่.

    resolve team id จากชื่อทุกครั้ง — teams เป็น data ฝั่ง d_CEO ห้าม hardcode
    """
    settings = get_settings()
    team_id = client.resolve_team_id(settings.ceo_team_name)
    if team_id is None:
        return []

    taken = {
        row
        for row in db.execute(
            select(Project.ceo_task_id).where(Project.ceo_task_id.is_not(None))
        ).scalars()
    }
    return [
        task
        for task in client.list_tasks(status="queued", limit=200)
        if task.assigned_team_id == team_id and task.id not in taken
    ]


def pull_tasks(
    db: Session,
    client: CeoClient,
    *,
    task_ids: list[str] | None = None,
    breakdown: bool = True,
) -> list[PullResult]:
    """รับงานจาก inbox → สร้างโปรเจกต์ + แตกงาน + แจ้ง d_CEO ว่ารับแล้ว.

    ``task_ids=None`` = รับทุกงานที่รออยู่ | งานที่รับแล้วถูกกรองออกโดย `list_inbox`
    ผู้ใช้ยังต้อง **ยืนยัน scope** และกด Run เอง (หลัก "ยืนยันก่อนทำ" ของ ecosystem)
    """
    inbox = list_inbox(db, client)
    if task_ids is not None:
        wanted = set(task_ids)
        inbox = [task for task in inbox if task.id in wanted]

    results: list[PullResult] = []
    for ceo_task in inbox:
        project = Project(
            name=_project_name(ceo_task.input_text),
            type=ProjectType.NEW.value,
            ceo_task_id=ceo_task.id,
        )
        db.add(project)
        db.flush()
        record_audit(
            db,
            actor_type=ActorType.AGENT,
            actor_id=CEO_ACTOR_ID,
            action="project.created",
            entity_type="project",
            entity_id=str(project.id),
            diff={"source": "d_CEO", "ceo_task_id": ceo_task.id, "name": project.name},
        )
        db.commit()
        db.refresh(project)

        task_count = 0
        source: str | None = None
        if breakdown:
            result = breakdown_requirement(ceo_task.input_text)
            source = result.source
            task_count = len(persist_task_plan(db, project.id, result.plan))

        # แจ้งกลับว่ารับงานแล้ว — ล้มเหลวไม่ rollback (โปรเจกต์เกิดแล้ว ค่อย retry ตอน report)
        acknowledged = True
        detail = "รับงานแล้ว + แจ้ง d_CEO เป็น in_progress"
        try:
            client.patch_task(ceo_task.id, status=CEO_STATUS_IN_PROGRESS)
        except CeoUnavailable as exc:
            acknowledged = False
            detail = f"สร้างโปรเจกต์แล้วแต่แจ้ง d_CEO ไม่สำเร็จ: {exc}"

        results.append(
            PullResult(
                ceo_task_id=ceo_task.id,
                project_id=str(project.id),
                name=project.name,
                task_count=task_count,
                breakdown_source=source,
                acknowledged=acknowledged,
                detail=detail,
            )
        )
    return results


def _escalation_reasons(db: Session, task_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    """เหตุผลล่าสุดที่แต่ละ task ถูก escalate (จากข้อความ `question` บน bus)."""
    if not task_ids:
        return {}
    rows = (
        db.execute(
            select(AgentMessage)
            .where(
                AgentMessage.task_id.in_(task_ids),
                AgentMessage.message_type == MessageType.QUESTION.value,
            )
            .order_by(AgentMessage.created_at)
        )
        .scalars()
        .all()
    )
    reasons: dict[uuid.UUID, str] = {}
    for message in rows:  # ตัวหลังทับตัวหน้า = ได้เหตุผลล่าสุด
        payload = message.payload or {}
        if message.task_id is not None and payload.get("reason"):
            reasons[message.task_id] = str(payload["reason"])
    return reasons


def _work_product_section(db: Session, finished: list[Task]) -> list[str]:
    """หัวข้อ "ผลงาน" — ตัวชิ้นงานจริงของ **ทุก task ที่เสร็จ** เรียงตามลำดับที่วางแผนไว้.

    QC ของ d_CEO ต้องอ่านของจริงถึงจะตรวจได้ (มติจาก UAT 2026-08-03: ส่งแต่สรุปสถานะ =
    `rejected` ทันที) · คุมความยาวสองชั้นเหมือนฝั่ง orchestrator เพราะ `output` ของ d_CEO
    เป็นคอลัมน์ข้อความเดียว — รายงานที่ยาวเกินไปก็ไม่มีใครอ่าน
    """
    if not finished:
        return []
    works = latest_work_by_task(db, [t.id for t in finished])
    if not works:
        return []

    section = ["## ผลงาน (ตัวชิ้นงานจริง)", ""]
    budget = REPORT_WORK_TOTAL_CHAR_LIMIT
    omitted: list[str] = []
    for task in finished:
        work = works.get(task.id)
        if not work:
            continue
        block = clip_work(work, REPORT_WORK_CHAR_LIMIT)
        if len(block) > budget:
            omitted.append(task.title)
            continue
        budget -= len(block)
        section += [f"### {task.title}", "", block, ""]
    if omitted:
        section += [
            f"> หมายเหตุ: ตัดผลงานของ {len(omitted)} รายการออกเพราะรายงานยาวเกินเพดาน "
            f"({', '.join(omitted)}) — เปิดดูฉบับเต็มได้บนบอร์ด DEP-PM",
            "",
        ]
    return section


def build_report(db: Session, project: Project) -> ReportResult:
    """ประเมินว่าโปรเจกต์พร้อมรายงานไหม แล้วประกอบ `output` เป็น markdown.

    พร้อม = ไม่มี task ที่ยังเดินอยู่ (ทุกตัวจบเป็น done/deployed หรือค้างที่ escalated)
    """
    tasks = (
        db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.created_at))
        .scalars()
        .all()
    )
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1

    if not tasks:
        return ReportResult(False, False, "ยังไม่มี task ในโปรเจกต์นี้", counts=counts)

    # เกณฑ์ "จบรอบ" = ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง (_next_runnable คืน None)
    # ห้ามนับ planned ทั้งหมดเป็น "ยังเดินอยู่" — planned ที่ dependency ติด escalated
    # จะค้างตลอดกาล ทำให้เคสที่ต้องรีบบอกคนที่สุด (มีงาน escalate) กลายเป็นเคสที่เงียบหาย
    # (บั๊กที่เจอจาก UAT จริง 2026-08-02 — ดู CHANGELOG)
    by_id = {str(t.id): t for t in tasks}

    def _runnable(task: Task) -> bool:
        """planned ที่ dependency จบครบแล้ว = orchestrator หยิบไปทำต่อได้."""
        return all(
            (dep := by_id.get(dep_id)) is not None and dep.status in FINISHED_STATUSES
            for dep_id in (task.depends_on or [])
        )

    in_flight = [t for t in tasks if t.status in IN_FLIGHT_STATUSES]
    unconfirmed = [t for t in tasks if t.status == TaskStatus.BACKLOG.value]
    planned = [t for t in tasks if t.status == TaskStatus.PLANNED.value]
    runnable = [t for t in planned if _runnable(t)]
    blocked = [t for t in planned if not _runnable(t)]  # ค้างเพราะ dependency ไม่มีวันจบ

    if in_flight:
        return ReportResult(
            False, False, f"ยังมีงานที่ agent ถืออยู่ {len(in_flight)} รายการ", counts=counts
        )
    if unconfirmed:
        return ReportResult(
            False,
            False,
            f"ยังไม่ได้ยืนยัน scope ({len(unconfirmed)} task ค้าง backlog)",
            counts=counts,
        )
    if runnable:
        return ReportResult(
            False, False, f"ยังมีงานที่รันได้อีก {len(runnable)} รายการ — กด Run ก่อน", counts=counts
        )

    finished = [t for t in tasks if t.status in FINISHED_STATUSES]
    escalated = [t for t in tasks if t.status == TaskStatus.ESCALATED.value]
    reasons = _escalation_reasons(db, [t.id for t in escalated])
    tokens_in = sum(t.tokens_input or 0 for t in tasks)
    tokens_out = sum(t.tokens_output or 0 for t in tasks)

    lines = [
        f"# ผลงานจากทีม R&D — {project.name}",
        "",
        f"งานทั้งหมด **{len(tasks)}** รายการ · เสร็จ **{len(finished)}** · "
        f"ต้องการคนตัดสิน **{len(escalated)}**"
        + (f" · ค้างเพราะรอตัวข้างบน **{len(blocked)}**" if blocked else ""),
        "",
    ]
    if escalated or blocked:
        lines += [
            "> ⚠️ **งานรอบนี้ยังไม่จบสมบูรณ์** — มีงานที่ agent ทำต่อเองไม่ได้ "
            "ต้องให้คนเข้ามาตัดสินหรือรับช่วง (รายละเอียดด้านล่าง)",
            "",
        ]
    if finished:
        lines.append("## งานที่ทำเสร็จ")
        lines += [
            f"- [{t.priority}] {t.title}"
            + (f" (แก้ {t.revision_count} รอบ)" if t.revision_count else "")
            + (" · deploy แล้ว" if t.status == TaskStatus.DEPLOYED.value else "")
            for t in finished
        ]
        lines.append("")
    if escalated:
        lines.append("## งานที่ต้องการคนตัดสิน (escalated)")
        lines += [
            f"- [{t.priority}] {t.title} — {reasons.get(t.id, 'review ไม่ผ่านครบจำนวนรอบที่กำหนด')}"
            for t in escalated
        ]
        lines.append("")
    if blocked:
        lines.append("## งานที่ค้างเพราะรองานข้างบน")
        for t in blocked:
            waiting_on = [
                by_id[d].title
                for d in (t.depends_on or [])
                if d in by_id and by_id[d].status not in FINISHED_STATUSES
            ]
            lines.append(f"- [{t.priority}] {t.title} — รอ: {', '.join(waiting_on) or 'ไม่ทราบ'}")
        lines.append("")
    # ตัวชิ้นงานจริง — QC ของ d_CEO ปฏิเสธรอบ 2026-08-03 เพราะ "ไม่มี artifact ให้ตรวจ"
    # (รายงานเดิมมีแต่ชื่อ task กับตัวเลข) · ผลงานอยู่ใน agent_messages มาตลอด แค่ไม่ถูกหยิบมา
    lines += _work_product_section(db, finished)
    lines += [
        "## ต้นทุน",
        f"token: input {tokens_in:,} · output {tokens_out:,}",
        "",
        "## อ้างอิง",
        f"DEP-PM project `{project.id}` — เปิดบอร์ด/บทสนทนา agent ย้อนหลังได้ที่ "
        f"`/projects/{project.id}` (backend `:8500`)",
    ]

    return ReportResult(
        True,
        False,
        "พร้อมรายงาน",
        status_sent=None,
        output="\n".join(lines),
        counts=counts,
    )


def report_project(db: Session, client: CeoClient, project: Project) -> ReportResult:
    """ส่งผลงานกลับ d_CEO เป็น `qc_review` (ห้ามส่ง done — ต้องผ่าน QC gate).

    ไม่ raise `CeoUnavailable` ออกไป — คืนผลให้ caller ตัดสินใจ (endpoint แจ้งผู้ใช้,
    เส้นทางอัตโนมัติหลัง `/run` เพิกเฉยเงียบ)
    """
    if not project.ceo_task_id:
        return ReportResult(False, False, "โปรเจกต์นี้ไม่ได้มาจาก d_CEO (ไม่มี ceo_task_id)")

    draft = build_report(db, project)
    if not draft.ready or draft.output is None:
        return draft

    try:
        client.patch_task(project.ceo_task_id, status=CEO_STATUS_QC_REVIEW, output=draft.output)
    except CeoUnavailable as exc:
        draft.detail = f"ประกอบรายงานแล้วแต่ส่งไม่สำเร็จ: {exc}"
        return draft

    record_audit(
        db,
        actor_type=ActorType.AGENT,
        actor_id=CEO_ACTOR_ID,
        action="ceo.reported",
        entity_type="project",
        entity_id=str(project.id),
        diff={
            "ceo_task_id": project.ceo_task_id,
            "status": CEO_STATUS_QC_REVIEW,
            "counts": draft.counts,
        },
    )
    db.commit()

    draft.reported = True
    draft.status_sent = CEO_STATUS_QC_REVIEW
    draft.detail = "ส่งผลงานเข้า QC gate ของ d_CEO แล้ว"
    return draft
