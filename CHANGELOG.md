# CHANGELOG — DEP-PM Platform

## 2026-07-06 — Engineering Documentation Set (ตาม MASTER PROMPT)

- สร้างชุดเอกสารวิศวกรรมใน `docs/` ครอบคลุม 25 sections ของ
  "MASTER PROMPT: Complete Software Engineering Documentation Generator":
  - `ARCHITECTURE.md` (§1-4) — overview/non-goals/constraints, HLA + Mermaid 3 diagrams,
    tech stack พร้อม WHY/tradeoffs/ทางเลือกที่ไม่เลือก, folder structure + dependency direction
  - `SYSTEM_DOCUMENTATION.md` (§5-9, 13-14, 16-22, 24) — วิเคราะห์ทุกโมดูล, algorithms,
    business logic + state diagram, frontend/backend, performance/testing/deployment/maintenance,
    technical debt จัดอันดับ, glossary
  - `API.md` (§12) — 12 endpoints พร้อม request/response ตัวอย่าง + error codes
  - `DATABASE.md` (§10-11) — ER diagram, ทุกตาราง/index/query pattern, migration history + กติกา
  - `SECURITY.md` (§15) — threat model, OWASP mapping, สถานะตรงไปตรงมา (ยังไม่มี auth)
    + security gate ก่อน production
  - `AI_AGENT_GUIDE.md` (§23) — architecture rules, forbidden changes, safe refactoring,
    documentation rules, common mistakes จากประสบการณ์จริง
- อัปเดต `CLAUDE.md` ให้ index เอกสารชุดนี้

## 2026-07-06 — Sprint 3: Kanban Dashboard + Message Log + Portfolio

- **Backend:** เพิ่ม `GET /api/portfolio` — task counts ต่อสถานะทุกโปรเจกต์, รายชื่อ agents,
  deploy ล่าสุด (ตาราง deployments พร้อมแล้ว ค่าจริงเริ่ม Sprint 4); pytest 34 เคสผ่าน
- **Frontend scaffold:** Next.js **16.2.10** (create-next-app@latest — ใหม่กว่าแผนที่ระบุ 15)
  + TypeScript + Tailwind, App Router, `src/` layout
- **Portfolio page** (`/`): การ์ดโปรเจกต์ + แถบสัดส่วนสถานะ + agent pills
- **New Project page** (`/projects/new`): ครบวงจร STEP 1-4 ของ Blueprint §6 —
  กรอก requirement → PM Agent แตกงาน (หรือ scan mock สำหรับ existing) → เห็น plan → ยืนยัน scope
- **Kanban Board** (`/projects/[id]`): 8 คอลัมน์ตาม status, การ์ดแสดง assignee pill
  (🤖 agent role / 👤 human) + revision count, ปุ่มเปลี่ยนสถานะเฉพาะ transition ที่ถูกต้อง
  (mirror State Machine — backend ยังบังคับ 409 อีกชั้น), ปุ่ม "Run Agents" เรียก orchestrator
- **Message Log Viewer**: task detail panel แสดงบทสนทนา agent (handoff/result/review_comment/question)
- **Polling refresh (ADR-04)**: `usePolling` hook — refetch ทุก 4 วิ เฉพาะแท็บ active
- **E2E verified:** create → breakdown → confirm → run → done ผ่าน API + ทุกหน้า (/, /projects/new,
  /projects/[id]) ตอบ 200 บน production build

## 2026-07-06 — Sprint 2: Task Orchestration Engine + Solo Mode Runtime

- **State Machine** (`app/orchestrator/state_machine.py`): บังคับ transition ตาม Blueprint §5
  เท่านั้น — ผิด transition ตอบ **409**; ทุก transition เขียน `audit_log` อัตโนมัติ
  (`PATCH /api/tasks/:id` และ confirm-scope เปลี่ยนมาใช้เส้นทางนี้ทั้งหมด)
- **Routing Rules** (`app/agents/routing.py`): keyword heuristic → Senior Architect / Developer
  พร้อม log ทุก routing decision ลง audit (Risk #5)
- **Solo Mode Agent Runtime** (`app/agents/runtime.py`): `ClaudeExecutor` (persona prompt ตาม role)
  + `FallbackExecutor` (deterministic, ไม่มี network) — เพิ่ม personas DEV / ARCHITECT / REVIEWER
- **Orchestrator** (`app/orchestrator/engine.py`): planned → assigned → in_progress → review →
  done | revision loop | escalated; เคารพ dependency (`depends_on` ต้อง done ก่อน);
  Escalation Rule: review fail ครบ MAX_REVISIONS (2) → `escalated` + broadcast แจ้งผู้ใช้
- **Message Bus in-process** (`app/bus/` — ADR-03): ทุก handoff/result/review_comment/question
  ลงตาราง `agent_messages` เสมอ + fan-out ไป subscriber ใน process
- Endpoints ใหม่: `POST /api/projects/:id/run` (รัน orchestrator), `POST /api/agent-messages`
- pytest 32 เคสผ่าน (เพิ่ม 17: transition matrix, routing, bus, E2E happy path,
  revision loop, escalation, dependency ordering)

## 2026-07-06 — Sprint 1: Backend Foundation

- Scaffold `backend/` — FastAPI + SQLAlchemy 2.x + Alembic บน SQLite (รันได้จริง)
- ORM 6 ตารางครบ (projects, tasks, agents, agent_messages, deployments, audit_log) พร้อม
  portable types: `GUID` + `JSON` decorator เพื่อย้าย PostgreSQL ได้โดยไม่แก้ model (ADR-01)
- Alembic 2 migrations: สร้าง schema + seed "Claude Solo" agent (mode=solo)
- **PM Agent Task Breakdown** (persona PM, Claude API): requirement → Task Plan JSON →
  validate ด้วย Pydantic + retry 1 ครั้งเมื่อ parse ไม่ได้ (Risk #7); ไม่มี API key → fallback
  task เดียว ไม่ล้ม flow
- Intake endpoints: `POST /api/projects`, `GET/POST /api/projects/:id/tasks`,
  `POST .../breakdown`, `POST .../confirm` (backlog → planned), `POST .../scan`
- `MetadataProvider` interface + `StubMetadataProvider` → `POST /api/projects/:id/scan`
  คืน mock Baseline Report (ระบุ "(mock)" ชัด — Risk #1) แปลงเป็น backlog tasks ได้ (ADR-02)
- `PATCH /api/tasks/:id`, `GET /api/tasks/:id/messages`; audit_log บันทึกทุก state change
- pytest 15 เคสผ่านทั้งหมด; `/health` รายงาน `agent_enabled`

## 2026-07-02 — Planning Phase Complete

- อ่านและวิเคราะห์เอกสารตั้งต้น 3 ไฟล์ (Blueprint v1.0, DEP v3.0 Master Plan, AI Dev Team Guide)
- จัดทำ `docs/DEVELOPMENT_PLAN.md` — แผนพัฒนา MVP 4 สปรินต์ (~8 สัปดาห์) ประกอบด้วย:
  - ADR-01: SQLite (dev) → PostgreSQL (prod)
  - ADR-02: Metadata Engine เป็น interface + stub (DEP v3.0 ยังไม่มีโค้ดจริง)
  - ADR-03: Message bus แบบ in-process ก่อน → Redis Streams
  - ADR-04: Realtime แบบ polling/SSE ก่อน → WebSocket
  - Data Model 6 ตาราง, API Contract 11 endpoints, Risk Register, Success Metrics
- สร้าง `PROJECT_STATUS.md` (สถานะ + next tasks) และเติมข้อมูลโปรเจกต์ใน `CLAUDE.md`
- ยังไม่มีโค้ดแอปพลิเคชัน — Sprint 1 เริ่มเมื่อผู้ใช้อนุมัติ
