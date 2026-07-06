# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-06 | สถานะโดยรวม: **Sprint 1 (Foundation) เสร็จ — รอเริ่ม Sprint 2**

## Completed Work

### Sprint 1 — Backend Foundation (2026-07-06)
- Scaffold `backend/` (FastAPI + SQLAlchemy 2.x + Alembic บน SQLite) รันได้จริง
- ORM 6 ตารางครบ + portable `GUID`/`JSON` types (ADR-01) + Alembic 2 migrations (schema + seed agent)
- PM Agent Task Breakdown (persona PM, Claude API + fallback) → backlog tasks → confirm → planned
- `MetadataProvider` interface + `StubMetadataProvider` + `POST /scan` (mock baseline → backlog)
- Endpoints: projects CRUD, tasks CRUD, breakdown, confirm, scan, PATCH task, task messages
- audit_log บันทึกทุก state change; pytest 15 เคสผ่าน

### Planning (2026-07-02)
- `docs/DEVELOPMENT_PLAN.md` (4 สปรินต์, ADR, Data Model, API Contract, Risk Register)

## Files Changed (Sprint 1 — ใหม่ทั้งหมด)

- `backend/app/` — `main.py`, `config.py`, `constants.py`
- `backend/app/db/` — `base.py`, `session.py`, `types.py` (GUID + JSON)
- `backend/app/models/` — 6 ORM models
- `backend/app/schemas/` — `project.py`, `task.py`, `scan.py`
- `backend/app/api/` — `projects.py`, `tasks.py`
- `backend/app/agents/` — `pm.py`, `personas.py`
- `backend/app/metadata/` — `provider.py`, `stub.py`
- `backend/app/services/` — `tasks.py`, `audit.py`
- `backend/alembic/` — env + 2 migrations
- `backend/tests/` — conftest + 4 test modules (15 tests)
- `backend/` — `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `pytest.ini`, `alembic.ini`
- `CHANGELOG.md`, `PROJECT_STATUS.md` (อัปเดต)

## Current State

- Backend รันได้: `alembic upgrade head` → `uvicorn app.main:app` (docs ที่ `/docs`)
- pytest ผ่าน 15/15 (agent ทดสอบผ่าน fallback path — ไม่มี network call)
- `.venv/` + `dep_pm.db` เป็น local เท่านั้น (อยู่ใน `.gitignore`)
- โฟลเดอร์ยังไม่เป็น git repository

## Next Tasks (= Sprint 2, ดู docs/DEVELOPMENT_PLAN.md §6)

1. **State Machine** บังคับ transition ถูกต้อง (ผิด → 409) + เขียน audit_log ทุกครั้ง —
   ตอนนี้ `PATCH /api/tasks/:id` ยัง permissive (ยังไม่ validate transition)
2. **Routing Rules** (Blueprint §9): task type → Claude persona (PM/Architect/Developer/Reviewer)
3. **Solo Mode Agent Runtime** (Orchestrator): planned → assign → รัน persona → review → done/revision
4. **Message Bus in-process** (ADR-03): ทุก handoff/result/review_comment ลง `agent_messages`
5. Escalation: revision fail 2 ครั้ง → `escalated` (มี `revision_count` + `MAX_REVISIONS` แล้ว)
6. เพิ่ม personas DEV/REVIEWER/ARCHITECT ใน `app/agents/personas.py` (โครงมี PM แล้ว)

## Known Issues

- `PATCH /api/tasks/:id` ยังไม่บังคับ State Machine (ตั้งใจ — เลื่อนไป Sprint 2)
- Brownfield scan เป็น mock ตลอด MVP (ADR-02) — response ระบุ `is_mock: true` + prefix "[mock]"
- ชื่อ model default = `claude-sonnet-5` (ตั้งผ่าน env `CLAUDE_MODEL`) — ปรับได้ตามต้องการ

## Decisions Made (เพิ่มจาก Sprint 1)

1. **PM Agent มี fallback เสมอ** — ไม่มี API key หรือ parse ไม่ได้ → สร้าง task เดียว ไม่ 500
2. **audit + service layer แยก** (`app/services/`) — router บาง, business logic รวมศูนย์
3. Default `CLAUDE_MODEL=claude-sonnet-5`, `MAX_TOKENS_PER_TASK=4096` (ผ่าน env)
4. Alembic migration เขียน seed agent ด้วย fixed UUID `...0001` (deterministic)

## Questions for the User

1. **`git init` โปรเจกต์นี้ตอนนี้เลยไหม?** (แนะนำ: ทำ — จะได้ track Sprint 1 เป็น commit แรก)
2. Claude API key + budget/เดือน สำหรับทดสอบ PM Agent จริง (ตอนนี้รันผ่าน fallback)
3. ยืนยัน default model `claude-sonnet-5` ใช้ได้ หรือต้องการรุ่นอื่น (เช่น `claude-opus-4-8`)
4. เริ่ม Sprint 2 (State Machine + Orchestrator) ต่อเลยหรือไม่
