# CHANGELOG — DEP-PM Platform

## 2026-08-02 — Fix: ย้ายพอร์ตอีกครั้ง 8400 → **8500** (8400 เป็นของ d_Jarvis)

- **⚠️ Breaking (dev) ทับของเมื่อเช้า:** พอร์ต backend ที่ถูกต้องคือ **8500**
  `uvicorn app.main:app --reload --port 8500` · ต้องแก้ `NEXT_PUBLIC_API_URL` ตาม
- **เหตุ:** ตอนเลือก 8400 อ่าน `.env.example` ของ Jarvis เฉพาะบรรทัด base URL ของ client
  (8000/8100/8200/8300) แล้ว**พลาดบรรทัด `WEB_PORT=8400`** ซึ่งเป็น web channel ของ Jarvis
  ที่รันค้างผ่าน Task Scheduler · Windows ยอมให้ bind `127.0.0.1:8400` ซ้อน `0.0.0.0:8400`
  ได้โดยไม่ error → ระหว่างทดสอบ **DEP-PM บังหน้าเว็บ Jarvis บน localhost เงียบ ๆ**
  (ไม่กระทบข้อมูล และหยุด process ของเราแล้ว Jarvis กลับมาปกติทันที)
- **ทะเบียนพอร์ตฉบับถูกต้อง:** `8000` d_CEO API · `8100` d_OCR · `8200` d_STT ·
  `8300` d_InnoHub · `8400` **d_Jarvis web** · **`8500` DEP-PM**
- **กติกาใหม่ใน AGENTS.md + runbook:** ตรวจพอร์ตด้วย
  `Get-NetTCPConnection -LocalPort <port> -State Listen` ก่อนจองเสมอ **อย่าเชื่อเอกสารอย่างเดียว**

## 2026-08-02 — Fix: งานที่ escalate แล้วเคยเงียบหาย ไม่ถูกรายงานกลับเลขา

- **บั๊กที่พบจาก UAT จริง:** เกณฑ์ "รายงานเมื่องานจบครบ" นับ task สถานะ `planned` เป็น
  "ยังเดินอยู่" — แต่ task ที่ dependency ติด `escalated` จะค้าง `planned` **ถาวร**
  (พฤติกรรมถูกต้องของ orchestrator: หยุดเดินเอง ไม่ deadlock) ผลคือเงื่อนไขไม่มีวันเป็นจริง
  → **เคสที่ต้องรีบบอกคนที่สุด (มีงาน escalate) กลับเป็นเคสเดียวที่ไม่เคยรายงาน** และ
  task ฝั่ง d_CEO ค้าง `in_progress` ตลอดกาล
- **แก้:** เกณฑ์ใหม่ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง — พร้อมรายงานเมื่อ
  ไม่มี task ที่ agent ถืออยู่ **และ** ไม่มี `planned` ที่ dependency จบครบแล้ว (รันต่อได้)
  **และ** ไม่มี `backlog` ค้าง (ยังไม่ยืนยัน scope) · แต่ละกรณีบอกเหตุผลต่างกันชัดเจน
- **รายงานบอกความจริงครบขึ้น:** เพิ่มหัวข้อ "งานที่ค้างเพราะรองานข้างบน" (ระบุว่าติดเพราะ
  task ไหน) + แถบเตือน "⚠️ งานรอบนี้ยังไม่จบสมบูรณ์ ต้องให้คนเข้ามาตัดสิน" ท้ายหัวเรื่อง
- pytest 79 → **82 tests** (เพิ่มเคส escalated-บล็อก-dependent, runnable-ยังไม่รายงาน, backlog)

## 2026-08-02 — Phase 1: รับงานจากเลขา (d_CEO) ในฐานะ Team Lead R&D

- **📥 กล่อง "งานจากเลขา" บนหน้า Portfolio** — เห็นงานที่ d_CEO มอบให้ทีม R&D พร้อมปุ่ม
  "ดึงงานทั้งหมด" / "รับงานนี้" · กล่องนี้ซ่อนเองถ้ายังไม่ตั้ง `CEO_API_BASE`
  · d_CEO ปิดอยู่ = แสดง "🧠 สมองออฟไลน์" ระบบส่วนอื่นใช้ได้ปกติ
- **ดึงงาน 1 ครั้ง = 1 โปรเจกต์** — สร้างโปรเจกต์ผูก `ceo_task_id` (unique) → PM Agent แตกงาน
  ให้เลย → แจ้ง d_CEO เป็น `in_progress` · ดึงงานเดิมซ้ำไม่ได้ · **ผู้ใช้ยืนยัน scope + กด Run เอง**
- **รายงานผลกลับอัตโนมัติ** เมื่องานในโปรเจกต์จบครบ (หลัง Run Agents) — ส่งสรุป markdown
  (งานที่เสร็จ / งานที่ต้อง escalate พร้อมเหตุผล / token ที่ใช้) เข้า **QC gate** ของ d_CEO
  · ปุ่ม "📤 ส่งผลกลับเลขา" บนหน้าบอร์ดไว้ยิงซ้ำเมื่อรอบอัตโนมัติล้มเหลว
- 🔴 **ระบบปิดงานฝั่ง d_CEO เองไม่ได้** — ส่งได้แค่ `in_progress`/`qc_review` เท่านั้น
  (`done`/`awaiting_approval`/`rejected` = ValueError ก่อนยิง HTTP) ตามมติ Vinit 2026-08-02
  ว่าทุกงานต้องผ่าน QC gate — QC ของ d_CEO เป็นคนเคาะ
- **Endpoints ใหม่:** `GET /api/projects/:id` · `GET /api/ceo/status` · `GET /api/ceo/inbox` ·
  `POST /api/ceo/pull` · `POST /api/ceo/report/:project_id` — `/api/projects/:id/run` เพิ่ม
  field `ceo_report` · `/health` เพิ่ม `ceo_enabled`
- **Schema:** `projects.ceo_task_id` (VARCHAR(36), nullable, **unique**) — migration `e5a91c73b204`
- **เอกสารใหม่:** `docs/INTEGRATION_CEO.md` (contract ฝั่ง consumer + สิ่งที่ต้องขอจาก d_CEO)
  · runbook §4.1 วิธีใช้งานประจำวัน
- pytest 60 → **79 tests** · ตรวจกับ d_CEO ตัวจริงแล้ว: resolve ทีม R&D ได้, `online: true`

## 2026-08-02 — Phase 0: ย้ายพอร์ตเป็น 8400 + AGENTS.md เป็นต้นฉบับ + จัดเอกสาร

- **⚠️ Breaking (dev):** backend ย้ายจากพอร์ต **8000 → 8400** — `uvicorn app.main:app --reload --port 8400`
  เหตุผล: `:8000` เป็นของ **d_CEO / Solo_CEO API** ที่รันค้างตลอดผ่าน Task Scheduler และ d_Jarvis
  พึ่งพาอยู่ (ห้ามหยุด) — เดิมเอกสารบอกให้รันที่ 8000 ซึ่ง**รันไม่ขึ้นจริง** · ต้อง `cp .env.local.example
  .env.local` ใหม่ หรือแก้ `NEXT_PUBLIC_API_URL` เป็น `http://127.0.0.1:8400`
  · ตารางพอร์ตของ ecosystem จดไว้ใน `AGENTS.md` §3.1 และ `docs/runbook.md` §1
- **`AGENTS.md` = single source of truth** ของกติกา AI agent (ตรงกับ convention ของ d_Jarvis/d_CEO/d_InnoHub)
  — ย้ายเนื้อหาจริงจาก `CLAUDE.md` เข้ามาครบ + เพิ่ม **§3.1 ตำแหน่งใน ecosystem** (สายบังคับบัญชา
  Vinit→Jarvis→d_CEO→DEP-PM = Team Lead R&D) · `CLAUDE.md`/`GEMINI.md` เหลือเป็น pointer
  · แก้ลิงก์ `WORKING_RULES.md` ที่เคยชี้ไฟล์ที่ไม่มีอยู่จริง → ชี้ `_CANON`
- **`README.md`** เขียนใหม่เป็นของ DEP-PM (เดิมเป็น README ของ Project Starter Kit ที่หลงเข้ามา)
- **`docs/PROJECT_OVERVIEW.md` + `docs/RISK_REGISTER.md`** เติมเนื้อหาจริง (เดิมเป็นเทมเพลตเปล่า)
  — 14 active risks + 6 closed + security/performance checklist ตามสถานะจริง
- commit งานค้างของ 2026-07-07 ที่ตกค้างใน working tree มา ~1 เดือน (`9cd76d6`)
- `.gitignore`: เพิ่ม `BackUp/` (สำเนาก่อนแก้ตาม WORKING_RULES — มีข้อมูลจริง ห้ามขึ้น remote)
- ตรวจแล้ว: pytest 60/60 · ruff clean · `npm run build` ผ่าน · DEP-PM `:8400` กับ d_CEO `:8000`
  รันคู่กันได้จริง (health ตอบทั้งคู่)

## 2026-07-07 — เคลียร์ technical debt #3/#5/#7 + หน้า Deployments + ruff

- **Reviewer fail-safe (debt #3):** review ที่ parse ไม่ได้ → retry 1 ครั้ง → ยังไม่ได้ =
  **reject** (เดิม auto-approve — งานไม่ถูกตรวจจริงอาจหลุดเป็น done) → เข้า revision loop
  ปกติ ครบ MAX_REVISIONS แล้ว escalate ให้คน; logic รวมที่ `runtime._review_with_retry`
  ใช้ทั้ง Solo และ Team Mode
- **Token-usage tracking (debt #7):** คอลัมน์ใหม่ `tasks.tokens_input/tokens_output`
  (migration `c7d4e2a9b1f3`) สะสมจากทุก execute/review call ทุก provider
  (Anthropic/OpenAI/Gemini คืน `LLMReply` พร้อม usage) — โชว์ใน task detail panel
- **depends_on referential integrity (debt #5):** สร้าง task ที่อ้าง id นอกโปรเจกต์/ไม่มีจริง
  → 400 | endpoint ใหม่ `DELETE /api/tasks/:id` — มีตัวอ้างค้าง → 409; ลบสำเร็จเก็บ audit
  + ลบ messages (CASCADE) + deployments.task_id → NULL (ทำที่ API layer เพราะ SQLite
  dev ไม่ enforce FK)
- **หน้า Deployments ใหม่** (`/deployments` + ลิงก์ nav): ตารางประวัติ deploy ทุกโปรเจกต์
  ใหม่ล่าสุดก่อน พร้อมสถานะสี/environment/trigger/commit — ใช้ endpoint ใหม่
  `GET /api/deployments` (filter `project_id` ได้, เติม project_name/task_title ให้)
- **ruff:** config `backend/ruff.toml` (E,F,I,B,UP; ignore E501,B008) + แก้ของเดิมทั้งหมด
  (ส่วนใหญ่ import order) — suite สะอาด
- pytest 48 → **60 tests** (review fail-safe, token accumulation, depends_on guards,
  deployments list)

## 2026-07-06 — UI: ai-dev-team theme + Agent Office + Run progress

- **Restyle ทั้งระบบตาม `ai-dev-team-complete.html`**: โทนสว่าง #f4f5fb + dot grid,
  การ์ดขาว r14, สีทีม Claude ม่วง / Codex เขียว / Gemini ฟ้า (utilities ใน globals.css)
- **🏢 Agent Office** (หน้าบอร์ด): ตัวการ์ตูน PM/Dev/SR/Reviewer เดินไปมาเมื่อ role นั้น
  มีงาน active (พร้อมป้ายชื่องาน) / ยืนจิบกาแฟเมื่อว่าง — สถานะจริงจาก task ที่ poll
- **Run progress bar**: ตัวนับงานเสร็จ/ทั้งหมด, สถานะเฟสงานปัจจุบัน (มอบหมาย/เขียน/ตรวจ
  + รอบแก้), เวลาที่ใช้ (เดินสดทุกวิ), ETA จากค่าเฉลี่ยต่องานที่จบ; poll ถี่ขึ้นเป็น 2 วิระหว่างรัน
- Fix ระหว่างใช้งานจริง: เผลอลบ dep_pm.db ระหว่าง cleanup ทำให้โปรเจกต์ผู้ใช้หาย —
  กู้ด้วยโปรเจกต์เดโมใหม่ + บันทึกกติกาถาวร "ห้ามลบ dep_pm.db" (memory + runbook)


## 2026-07-06 — UAT กับของจริง (Anthropic API + GitHub) + bugfixes

- **UAT ผ่าน 3 รายการ:** (1) PM Agent จริง — requirement ไทย → 16 tasks มี priority/points/deps
  (2) Solo Mode จริง — escalation ครบวงจร (reviewer ปฏิเสธ 2 → escalated → human takeover →
  done) + happy path งานออกแบบ schema → done รอบเดียว (3) Deploy dispatch จริง —
  `repository_dispatch` → workflow รันบน GitHub Actions, Build & Deploy step ผ่าน
- **Fix:** `MAX_TOKENS_PER_TASK` default 4096 → 16000 — adaptive thinking ของ claude-sonnet-5
  กินโควตาจนได้ text ว่างในรอบ revision (พบจริงใน UAT); `_call` คืน marker ชัดเจนเมื่อ text ว่าง
- **Fix:** test suite ไม่ hermetic เมื่อ `.env` มี key จริง — Windows ลบ env var ที่ตั้งเป็นค่าว่าง
  ทำให้ override ไม่ทำงาน → conftest เพิ่ม autouse fixture monkeypatch Settings (48/48, 0.96s)
- Push repo ขึ้น GitHub: `ohho2518/d_DEP-PM_Platform` (branch main) + workflow receiver
- บทเรียน UAT บันทึกใน `docs/runbook.md` §7

## 2026-07-06 — Sprint 4: Deploy Pipeline + Team Mode + PostgreSQL-ready

- **Deploy pipeline (Blueprint §12):** `services/deploy.py` ยิง GitHub `repository_dispatch`
  (event `dep-pm-deploy`) เมื่อตั้ง `GITHUB_TOKEN`+`GITHUB_REPO`; ไม่ตั้ง = stub mode
  (record `queued`, ไม่ error) | endpoints: `POST /api/deployments` (manual — production
  มาทางนี้เท่านั้น = Manual Approval Gate), `GET /:id`, `PATCH /:id` (CI callback —
  success เลื่อน task done→deployed อัตโนมัติ, terminal status ห้ามแก้ → 409)
- **Auto-deploy:** task done ระหว่าง orchestrator run + `AUTO_DEPLOY_ENABLED=true` →
  staging deployment อัตโนมัติ (auto path hardcode staging)
- **Team Mode (Blueprint §8-9):** `AGENT_MODE=team` → `TeamExecutor` map role→provider
  (Dev=OpenAI/Codex, SR=Gemini, PM+Reviewer=Claude) + fallback chain ต่อ role
  (provider→anthropic→deterministic); orchestrator ไม่แก้แม้แต่บรรทัดเดียว (DoD)
- **PostgreSQL-ready:** `psycopg[binary]` ใน requirements + ขั้นตอนย้ายใน `docs/runbook.md`
  (การรัน test จริงบน PG รอ infrastructure — ไม่มี Docker/PG บนเครื่องนี้)
- **ตัดสินใจ: ข้าม Redis** — ADR-03 ระบุ "ถ้าทัน"; single-user ยังไม่มีเหตุ cross-process
- **Handover:** `docs/runbook.md` (รัน/เปิด features/troubleshooting/UAT checklist) +
  `docs/github-workflow-example.yml` (template สำหรับ repo เป้าหมาย)
- pytest 48 เคสผ่าน (เพิ่ม 14: deployments + team mode)

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
