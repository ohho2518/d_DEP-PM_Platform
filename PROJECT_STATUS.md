# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-06 | สถานะโดยรวม: **Sprint 2 (Orchestration Engine) เสร็จ — รอเริ่ม Sprint 3**

## Completed Work

### Sprint 2 — Task Orchestration Engine + Solo Mode Runtime (2026-07-06)
- State Machine บังคับ transition (ผิด → 409) + audit_log ทุก state change
- Routing Rules (keyword → Architect/Dev) + log ทุก decision
- Solo Mode Runtime: ClaudeExecutor (persona ตาม role) + FallbackExecutor (deterministic)
- Orchestrator: planned → … → done | revision (สูงสุด 2) | escalated; เคารพ dependency
- Message Bus in-process (ADR-03) — ทุกข้อความลง `agent_messages` เสมอ
- Endpoints: `POST /api/projects/:id/run`, `POST /api/agent-messages`
- E2E DoD ผ่าน: requirement → breakdown → confirm → run → done ครบโดยไม่มี manual intervention

### Sprint 1 — Backend Foundation (2026-07-06)
- Scaffold FastAPI + SQLAlchemy + Alembic (SQLite), ORM 6 ตาราง, PM Agent breakdown,
  Metadata Stub, intake endpoints, seed Claude Solo agent

## Files Changed (Sprint 2)

- ใหม่: `backend/app/orchestrator/` (`state_machine.py`, `engine.py`), `backend/app/bus/`
  (`dispatcher.py`), `backend/app/agents/routing.py`, `backend/app/agents/runtime.py`,
  `backend/app/api/agent_messages.py`, `backend/tests/test_state_machine.py`,
  `backend/tests/test_orchestrator.py`, `backend/tests/test_routing_bus.py`
- แก้: `app/agents/personas.py` (+3 personas), `app/api/tasks.py` (PATCH enforce state machine),
  `app/api/projects.py` (confirm ผ่าน transition, + `/run`), `app/api/__init__.py`, `app/main.py`

## Current State

- Backend รันได้: `alembic upgrade head` → `uvicorn app.main:app`
- pytest **32/32 ผ่าน** (orchestrator ทดสอบด้วย FallbackExecutor + mock reviewer — ไม่มี network)
- Solo Mode ครบวงจรบน API แล้ว; ยังไม่ได้ทดสอบกับ Claude API จริง (ไม่มี key)
- git: commit Sprint 1 แล้ว (`e512771`) — Sprint 2 รอ commit ถัดไป

## Next Tasks (= Sprint 3, ดู docs/DEVELOPMENT_PLAN.md §6)

1. Scaffold `frontend/` (Next.js 15 + TypeScript)
2. Kanban Board ต่อโปรเจกต์ (คอลัมน์ตาม status, ลาก/ปุ่มเรียก `PATCH /api/tasks/:id`)
3. Message Log Viewer (จาก `GET /api/tasks/:id/messages`)
4. Portfolio View — **ต้องเพิ่ม `GET /api/portfolio` ฝั่ง backend ก่อน** (ยังไม่มี)
5. หน้า New Project (requirement → task plan → ยืนยัน scope)
6. Refresh แบบ polling/SSE (ADR-04)

## Known Issues

- `GET /api/portfolio` และ `POST/GET /api/deployments` ยังไม่ implement (portfolio ทำต้น Sprint 3,
  deployments เป็นของ Sprint 4 ตามแผน)
- Reviewer ของ ClaudeExecutor: ถ้า parse JSON review ไม่ได้ → auto-approve พร้อม note
  (กัน escalation จาก output เพี้ยน — ทบทวนเมื่อใช้ key จริง)
- `POST /api/projects/:id/run` เป็น synchronous — โปรเจกต์ใหญ่จะ block request
  (พอสำหรับ MVP; พิจารณา background job ตอน Sprint 4)
- Brownfield scan ยังเป็น mock ตลอด MVP (ADR-02)

## Decisions Made (เพิ่มจาก Sprint 2)

1. **Escalation ตีความ "Max Revision = 2" = reject ครั้งที่ 2 → escalated** (revision จริง 1 รอบ)
   ตรงกับ "Review --fail 2 ครั้ง--> Escalated" ใน Blueprint §5
2. **ทุก status change ผ่าน `transition()` เท่านั้น** — ห้าม set `task.status` ตรง ๆ
3. Orchestrator **commit ต่อ task** — งานที่เสร็จแล้วไม่ rollback ถ้าตัวถัดไปพัง
4. Reviewer parse fail → auto-approve (documented) แทนที่จะเสี่ยง escalate ทุก task
5. Dependency ไม่ครบ (เช่น dependency escalated) → task ค้างที่ planned ไม่ถูกรัน

## Questions for the User

1. Commit Sprint 2 แล้ว — เริ่ม Sprint 3 (Frontend/Kanban) เลย หรือทดสอบ Claude API จริงก่อน?
2. Sprint 3 ต้องตัดสินใจ UI framework (Blueprint แนะ Next.js 15 — ยืนยัน UI lib เช่น shadcn/ui?)
3. `GET /api/portfolio` จะทำเป็นงานแรกของ Sprint 3 ฝั่ง backend — โอเคไหม
