# CLAUDE.md

## Role

You are Claude working as an AI software engineering assistant inside this repository.

Your goal is to help the user build and maintain this project safely, efficiently, and continuously across sessions.

## Required Context Before Starting

Before any task, always read:

1. CLAUDE.md

2. PROJECT\_STATUS.md

Read CHANGELOG.md when the task involves feature history, user-facing changes, release notes, or debugging previous work.

Avoid reading the entire repository unless the task requires it.

## Project Summary

* Project name: **DEP-PM Platform** — AI-Native Project Management Platform

* Purpose: แพลตฟอร์มบริหารโปรเจกต์ที่มนุษย์และ AI Agent ทำงานบนบอร์ดเดียวกัน — รับ requirement → AI แตกงาน → มอบหมาย Agent/คน → Kanban → Auto-deploy เมื่อผ่าน review

* Target users: ทีมพัฒนา dPRO (โปรเจกต์ dPRO AI Parking, MChat, Farm Lab และโปรเจกต์อนาคต)

* Main features: Project Intake (New/Existing), AI Task Breakdown, Agent Task Assignment (Solo/Team Mode), Kanban Board, Inter-Agent Communication Log, Automated Deploy — ดู `docs/DEVELOPMENT_PLAN.md` §1

* Current status: **Sprint 1 (Backend Foundation) เสร็จ** — รอเริ่ม Sprint 2 (ดู `PROJECT_STATUS.md`)

Key reference documents (read-only, ห้ามแก้):

* `DEP-PM Platform Blueprint v1.0.html` — สเปกหลัก
* `DEP v3.0 Master Plan.html` — แพลตฟอร์มแม่ (ยังไม่มีโค้ดจริง — ใช้ stub, ดู ADR-02)
* `ai-dev-team-complete.html` — Agent Routing Rules + SOW
* `docs/DEVELOPMENT_PLAN.md` — แผนพัฒนาที่อนุมัติแล้ว (สปรินต์, ADR, Data Model, API Contract)

## Actual Tech Stack

**สถานะ: Backend CONFIRMED (Sprint 1 scaffold เสร็จ)** — frontend ยัง PLANNED (เริ่ม Sprint 3)

* Programming language: Python 3.12+ (backend), TypeScript (frontend)

* Framework: FastAPI (backend), Next.js 15 (frontend — เริ่ม Sprint 3)

* Runtime: uvicorn (dev)

* Package manager: pip (backend), npm (frontend)

* Database: SQLite (dev) → PostgreSQL (staging/prod) — ดู ADR-01

* ORM: SQLAlchemy 2.x + Alembic

* Authentication: ยังไม่ทำใน MVP (single-user) — Need confirmation

* UI framework: Need confirmation (ตัดสินใจตอน Sprint 3)

* Testing: pytest (backend)

* Deployment: GitHub Actions → Vercel (FE) + Render/Railway (BE) — Sprint 4

## Repository Structure

ปัจจุบัน (Sprint 1 เสร็จ — backend รันได้จริง):

    docs/DEVELOPMENT_PLAN.md              แผนพัฒนาที่อนุมัติแล้ว (สปรินต์, ADR, schema, API)
    PROJECT_STATUS.md                     สถานะล่าสุด + next tasks
    CHANGELOG.md                          ประวัติการเปลี่ยนแปลง
    CLAUDE.md                             ไฟล์นี้
    *.html (3 ไฟล์)                       เอกสารอ้างอิงต้นทาง — read-only ห้ามแก้
    backend/app/{main,config,constants}.py  FastAPI entry + settings + enums
    backend/app/db/                       engine, session, GUID/JSON portable types (ADR-01)
    backend/app/models/                   ORM 6 ตาราง
    backend/app/schemas/                  Pydantic (project, task, scan)
    backend/app/api/                      routers (projects, tasks)
    backend/app/agents/                   PM persona + task breakdown
    backend/app/metadata/                 MetadataProvider interface + Stub (ADR-02)
    backend/app/services/                 audit + task-plan persistence
    backend/alembic/                      migrations (schema + seed agent)
    backend/tests/                        pytest (15 tests)

ยังไม่ทำ (Sprint ถัดไป):

    backend/app/orchestrator/             State Machine + Orchestrator (Sprint 2)
    backend/app/bus/                      In-process message bus (Sprint 2)
    frontend/                             Next.js (Sprint 3)

## Development Commands

Document real commands only.

รันจากโฟลเดอร์ `backend/` (มี `.venv` แล้ว)

### Install

    cd backend
    python -m venv .venv
    .venv\Scripts\activate            # *nix: source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env               # ใส่ ANTHROPIC_API_KEY เพื่อเปิด PM Agent จริง

### Run Dev Server

    cd backend
    alembic upgrade head              # สร้าง schema + seed Claude Solo agent (SQLite)
    uvicorn app.main:app --reload     # http://127.0.0.1:8000  (docs: /docs)

### Build

Not applicable — Python backend (frontend build เริ่ม Sprint 3)

### Test

    cd backend
    pytest                            # 15 tests

### Lint / Format

ยังไม่ตั้ง ruff/black — จะเพิ่มเมื่อจำเป็น (Sprint 2+)

## Environment Variables

Document only names and purpose.

Never include real values, API keys, tokens, passwords, or private credentials.

Example:

DATABASE\_URL=Database connection string  
APP\_SECRET=Secret value, do not commit  
NEXT\_PUBLIC\_APP\_URL=Public app URL

## Architecture Notes

After inspecting the project, summarize:

* Frontend flow

* Backend flow

* API flow

* Database flow

* Authentication flow

* External services

* Important design decisions

Keep this practical for future AI sessions.

## Working Principles

Follow these principles:

1. Understand before editing.

2. Read only relevant files.

3. Make small, safe changes.

4. Preserve existing behavior unless the user asks otherwise.

5. Explain assumptions when information is incomplete.

6. Prefer maintainable code.

7. Do not introduce unnecessary dependencies.

8. Do not make broad rewrites.

9. Do not hide uncertainty.

10. Keep documentation updated.

## Claude Workflow

For every task:

1. Read CLAUDE.md.

2. Read PROJECT\_STATUS.md.

3. Identify the smallest file set needed.

4. Inspect relevant code.

5. Make the requested change.

6. Run tests/build/lint if available and relevant.

7. Update PROJECT\_STATUS.md.

8. Update CHANGELOG.md for important feature or behavior changes.

9. Update CLAUDE.md when commands, architecture, structure, database, or coding rules change.

## Session Continuity Rules

At the end of meaningful work, update PROJECT\_STATUS.md.

The update must include:

* Completed work

* Files changed

* Current state

* Next tasks

* Known issues

* Decisions made

* Questions for the user

This is required so a new Claude session can continue immediately without expensive re-scanning.

## Code Editing Rules

* Match the existing style.

* Keep file organization consistent.

* Avoid global formatting.

* Avoid unrelated changes.

* Do not remove comments unless outdated or misleading.

* Add comments only where they improve understanding.

* Use clear names.

* Keep functions focused.

## Database Rules

If the project uses a database:

1. Read schema and migration files before editing.

2. Do not create destructive migrations unless explicitly requested.

3. Keep schema, types, and API usage aligned.

4. Update status and changelog after schema changes.

5. Document manual migration steps if needed.

## UI Rules

If changing UI:

1. Reuse existing components.

2. Keep layout consistent.

3. Preserve responsive behavior.

4. Avoid unnecessary redesign.

5. Update changelog for visible behavior changes.

## API Rules

If changing APIs:

1. Preserve existing contracts unless requested.

2. Validate inputs.

3. Handle errors clearly.

4. Keep frontend and backend aligned.

5. Document breaking changes.

## Security Rules

Never expose or commit:

* API keys

* Passwords

* Tokens

* Private keys

* Real customer data

* Production credentials

Use placeholders only.

## Do Not Do

* Do not scan the whole repository every session.

* Do not rewrite files unnecessarily.

* Do not change unrelated code.

* Do not invent missing commands.

* Do not make major architecture changes without user approval.

* Do not add dependencies without explanation.

* Do not delete files unless requested.

## Final Response Format

When done, respond with:

1. Summary

2. Files changed

3. Commands run

4. Result

5. Risks or unfinished items

6. Next recommended step