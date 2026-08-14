"""Run Manager — รอบรัน orchestrator แบบ **เบื้องหลัง** (Phase 2).

ทำไมต้องมี: `/run` เดิมรันจนจบใน request เดียว — UAT จริง 2026-08-02 วัดได้ **6 tasks =
297 วินาที** ขณะที่ผู้เรียกฝั่งบน (d_Jarvis) ตั้ง timeout ไว้ 5 นาที ⇒ ใช้งานประจำไม่ได้
ตอนนี้จึงรับงานแล้วตอบ `202 + run_id` ทันที แล้วให้ผู้เรียกถามความคืบหน้าเอาเอง

ขอบเขต (ตั้งใจให้เล็ก — ไม่ใช่ job queue):

* สถานะรอบรันอยู่ **ในหน่วยความจำของโปรเซสเดียว** เหมือน message bus (ADR-03) —
  restart backend = ประวัติรอบรันหาย แต่ task/audit/message ใน DB ไม่หาย (เป็นของจริง)
* **1 โปรเจกต์ = 1 รอบรันพร้อมกัน** ยิงซ้อน → `RunAlreadyActive` → API ตอบ 409 (ปิด Risk #3)
* ไม่มี retry / priority / worker ข้ามโปรเซส — ถ้าวันหนึ่งต้องการ ให้เปลี่ยนที่ไฟล์นี้
  ไฟล์เดียว (endpoint กับ orchestrator ไม่รู้จักวิธีรัน)

งานเบื้องหลังใช้ session ของตัวเอง 1 ตัวต่อ 1 รอบ (`get_session_factory`) — ใช้ session
ของ request ไม่ได้เพราะมันถูกปิดไปพร้อม response
"""
from __future__ import annotations

import logging
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.constants import RunStatus
from app.db.base import utcnow
from app.integrations.ceo_client import CeoClient
from app.models.project import Project
from app.orchestrator.engine import TaskOutcome, run_project
from app.services import ceo_sync

logger = logging.getLogger(__name__)

#: เก็บประวัติรอบรันล่าสุดกี่รอบ (กันหน่วยความจำโตไม่จำกัดในโปรเซสที่รันยาว)
MAX_HISTORY = 50

SessionFactory = Callable[[], Session]


class RunAlreadyActive(RuntimeError):
    """โปรเจกต์นี้มีรอบรันค้างอยู่ — ห้ามยิงซ้อน (Risk #3: orchestrator ไม่ thread-safe ต่อโปรเจกต์)."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"โปรเจกต์นี้กำลังรันอยู่แล้ว (run_id={run_id})")
        self.run_id = run_id


@dataclass
class RunRecord:
    """สถานะของรอบรันหนึ่งรอบ — อ่าน/เขียนผ่าน :class:`RunManager` เท่านั้น (มี lock คุม)."""

    run_id: str
    project_id: str
    total: int
    status: str = RunStatus.RUNNING.value
    processed: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    outcomes: list[dict[str, object]] = field(default_factory=list)
    ceo_report: dict[str, object] | None = None
    error: str | None = None
    #: รอบจบเรียบร้อยแต่ **หยุดก่อนงานหมด** — ตอนนี้มีเหตุเดียวคือถึงเพดานค่าใช้จ่าย (§5)
    #: คนละช่องกับ ``error`` โดยเจตนา: นี่ไม่ใช่ความล้มเหลว รอบยัง ``succeeded``
    #: และงานที่เหลือยังค้าง ``planned`` รอกด Run ใหม่ได้ทันทีที่ขยับเพดาน
    stopped_reason: str | None = None
    started_at: datetime = field(default_factory=utcnow)
    finished_at: datetime | None = None
    cancel_requested: bool = False
    done: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)

    def snapshot(self) -> dict:
        """สำเนาสำหรับตอบ HTTP — ``total`` คือ task ที่ ``planned`` ตอนเริ่มรอบ.

        ``processed`` < ``total`` ตอนรอบจบเป็นเรื่องปกติ: task ที่ dependency ติด escalated
        จะค้าง ``planned`` ตลอดรอบ (ดู ``engine.planned_task_count``)
        """
        return {
            "run_id": self.run_id,
            "project_id": self.project_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "counts": dict(self.counts),
            "outcomes": list(self.outcomes),
            "ceo_report": self.ceo_report,
            "error": self.error,
            "stopped_reason": self.stopped_reason,
            "cancel_requested": self.cancel_requested,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class RunManager:
    """ทะเบียนรอบรันในหน่วยความจำ + lock ต่อโปรเจกต์."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runs: OrderedDict[str, RunRecord] = OrderedDict()
        self._active: dict[str, str] = {}  # project_id -> run_id ที่กำลังรัน

    # --- public API ---------------------------------------------------------

    def start(
        self,
        project_id: uuid.UUID,
        *,
        session_factory: SessionFactory,
        ceo_client: CeoClient | None = None,
        total: int = 0,
    ) -> RunRecord:
        """จองคิวโปรเจกต์ + สตาร์ต thread แล้วคืน record ทันที (ไม่รอผล).

        raise :class:`RunAlreadyActive` ถ้าโปรเจกต์นี้ยังรันค้างอยู่
        """
        pid = str(project_id)
        with self._lock:
            active = self._active.get(pid)
            if active is not None:
                raise RunAlreadyActive(active)
            record = RunRecord(run_id=str(uuid.uuid4()), project_id=pid, total=total)
            self._runs[record.run_id] = record
            self._active[pid] = record.run_id
            self._trim()

        thread = threading.Thread(
            target=self._work,
            args=(record, project_id, session_factory, ceo_client),
            name=f"run-{record.run_id[:8]}",
            daemon=True,
        )
        thread.start()
        return record

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def latest_for_project(self, project_id: uuid.UUID | str) -> RunRecord | None:
        """รอบรันล่าสุดของโปรเจกต์ — UI ที่เพิ่งรีเฟรชหน้าใช้ตัวนี้หา progress ที่ค้างอยู่."""
        pid = str(project_id)
        with self._lock:
            for record in reversed(self._runs.values()):
                if record.project_id == pid:
                    return record
        return None

    def cancel(self, run_id: str) -> RunRecord | None:
        """ขอให้รอบรันหยุด — **หยุดหลัง task ที่กำลังทำอยู่จบ** ไม่ตัดกลางคัน.

        คืน None ถ้าไม่รู้จัก run นี้ · รอบที่จบไปแล้วถือว่าไม่มีอะไรให้ยกเลิก (คืน record เดิม)
        """
        with self._lock:
            record = self._runs.get(run_id)
            if record is None or record.status != RunStatus.RUNNING.value:
                return record
            record.cancel_requested = True
            return record

    def wait(self, run_id: str, timeout: float = 60.0) -> RunRecord | None:
        """รอรอบรันจบ — ใช้ใน test และตอนปิดระบบ (production ไม่ควรเรียก)."""
        record = self.get(run_id)
        if record is None:
            return None
        record.done.wait(timeout)
        return record

    def reset(self) -> None:
        """ล้างทะเบียนทั้งหมด — สำหรับ test เท่านั้น."""
        with self._lock:
            self._runs.clear()
            self._active.clear()

    # --- internals ----------------------------------------------------------

    def _trim(self) -> None:
        """ตัดประวัติเก่าที่จบแล้วทิ้งเมื่อเกิน ``MAX_HISTORY`` (ที่ยังรันอยู่ไม่ตัด)."""
        while len(self._runs) > MAX_HISTORY:
            for run_id, record in self._runs.items():
                if record.status != RunStatus.RUNNING.value:
                    del self._runs[run_id]
                    break
            else:
                return  # ทั้งหมดยังรันอยู่ — ไม่ตัด

    def _work(
        self,
        record: RunRecord,
        project_id: uuid.UUID,
        session_factory: SessionFactory,
        ceo_client: CeoClient | None,
    ) -> None:
        """ตัวงานจริงใน thread — engine commit ต่อ task อยู่แล้ว ที่นี่จึงไม่ commit ซ้ำ."""
        db = session_factory()
        try:
            summary = run_project(
                db,
                project_id,
                on_outcome=lambda o: self._record_outcome(record, o),
                should_continue=lambda: not record.cancel_requested,
            )
            # getattr เพราะ test เสียบ engine ปลอมที่ไม่คืนอะไร — ที่นี่สนใจการจัดการรอบรัน
            # ไม่ใช่ตัว engine (ดู test_runs.py) · engine จริงคืน RunSummary เสมอ
            with self._lock:
                record.stopped_reason = getattr(summary, "stopped_reason", None)
            if record.cancel_requested:
                # ยกเลิกกลางคัน = รอบนี้ยังไม่จบ → **ไม่รายงานกลับ d_CEO**
                # (งานที่ทำเสร็จไปแล้วยังอยู่ ผู้ใช้กด Run ใหม่ทำต่อ หรือกดส่งผลเองได้)
                self._finish(record, RunStatus.CANCELLED)
            else:
                self._report_to_ceo(record, db, project_id, ceo_client)
                self._finish(record, RunStatus.SUCCEEDED)
        except Exception as exc:  # noqa: BLE001 — thread ห้ามตายเงียบ ต้องเก็บเหตุไว้ให้ UI เห็น
            logger.exception("run %s ของโปรเจกต์ %s ล้มเหลว", record.run_id, record.project_id)
            db.rollback()
            self._finish(record, RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}")
        finally:
            db.close()
            record.done.set()

    def _record_outcome(self, record: RunRecord, outcome: TaskOutcome) -> None:
        with self._lock:
            record.processed += 1
            record.counts[outcome.final_status] = record.counts.get(outcome.final_status, 0) + 1
            record.outcomes.append(
                {
                    "task_id": outcome.task_id,
                    "title": outcome.title,
                    "final_status": outcome.final_status,
                    "revisions": outcome.revisions,
                }
            )

    def _report_to_ceo(
        self,
        record: RunRecord,
        db: Session,
        project_id: uuid.UUID,
        ceo_client: CeoClient | None,
    ) -> None:
        """โปรเจกต์ที่มาจาก d_CEO และงานจบครบ → รายงานกลับเข้า QC gate ให้อัตโนมัติ.

        ล้มเหลว = บันทึกไว้เฉย ๆ **ห้ามทำให้รอบรันกลายเป็น failed** (งานพัฒนาเสร็จจริงไปแล้ว
        ผู้ใช้ยิง ``POST /api/ceo/report/:id`` ซ้ำเองได้)
        """
        if ceo_client is None:
            return
        project = db.get(Project, project_id)
        if project is None or not project.ceo_task_id:
            return
        try:
            result = ceo_sync.report_project(db, ceo_client, project)  # commit เองข้างใน
            report: dict[str, object] = {
                "ready": result.ready,
                "reported": result.reported,
                "status_sent": result.status_sent,
                "detail": result.detail,
            }
        except Exception as exc:  # noqa: BLE001 — ปลายทางล่มไม่ควรทำให้ผลงานที่ทำเสร็จหาย
            logger.exception("รายงานผลกลับ d_CEO ไม่สำเร็จ (run %s)", record.run_id)
            db.rollback()
            report = {
                "ready": True,
                "reported": False,
                "status_sent": None,
                "detail": f"ส่งรายงานไม่สำเร็จ: {type(exc).__name__}: {exc}",
            }
        with self._lock:
            record.ceo_report = report

    def _finish(self, record: RunRecord, status: RunStatus, *, error: str | None = None) -> None:
        with self._lock:
            record.status = status.value
            record.error = error
            record.finished_at = utcnow()
            self._active.pop(record.project_id, None)


#: singleton ต่อโปรเซส — เหมือน bus (ADR-03) คือของประจำโปรเซส ไม่ใช่ของ request
_manager = RunManager()


def start_run(
    project_id: uuid.UUID,
    *,
    session_factory: SessionFactory,
    ceo_client: CeoClient | None = None,
    total: int = 0,
) -> RunRecord:
    return _manager.start(
        project_id, session_factory=session_factory, ceo_client=ceo_client, total=total
    )


def get_run(run_id: str) -> RunRecord | None:
    return _manager.get(run_id)


def latest_run_for_project(project_id: uuid.UUID | str) -> RunRecord | None:
    return _manager.latest_for_project(project_id)


def cancel_run(run_id: str) -> RunRecord | None:
    return _manager.cancel(run_id)


def wait_for_run(run_id: str, timeout: float = 60.0) -> RunRecord | None:
    return _manager.wait(run_id, timeout=timeout)


def reset_runs() -> None:
    _manager.reset()
