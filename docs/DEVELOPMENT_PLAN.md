# DEP-PM Platform — Development Plan v1.0

> **สถานะ:** Approved Planning Document | **วันที่จัดทำ:** 2026-07-02
> **อ้างอิง:** `DEP-PM Platform Blueprint v1.0.html` (สเปกหลัก), `DEP v3.0 Master Plan.html` (แพลตฟอร์มแม่), `ai-dev-team-complete.html` (Agent Routing Rules + SOW)

---

## 1. สรุปโปรเจกต์และเป้าหมาย MVP

**DEP-PM** คือแพลตฟอร์มบริหารจัดการโปรเจกต์แบบ AI-Native ที่ให้ "มนุษย์และ AI Agent ทำงานอยู่บนบอร์ดเดียวกัน" ครอบคลุมตั้งแต่รับ requirement → แตกงาน → มอบหมายให้ Agent/คน → ติดตามสถานะบน Kanban → Deploy อัตโนมัติเมื่องานผ่าน review

### เป้าหมาย MVP (~8 สัปดาห์ / 4 สปรินต์)

- เริ่มด้วย **Solo Mode**: Claude ตัวเดียวสวมบทบาท PM / Developer / Reviewer ผ่าน system prompt คนละชุด (ใช้ API key เดียว) — Team Mode (Codex Dev + Gemini SR) เป็นของ Sprint 4
- รองรับ **New Project flow เต็มรูปแบบ** ก่อน ส่วน **Brownfield (Existing Project) ใช้ Stub** ไปก่อน (ดู ADR-02)
- ทุก task ไหลผ่าน **State Machine เดียวกัน** ไม่ว่ามอบให้คนหรือ Agent เพื่อให้ Dashboard ไม่มี blind spot

### Core Features และสปรินต์ที่รับผิดชอบ (จาก Blueprint §2)

| # | Feature | Priority | สปรินต์ |
|---|---------|----------|---------|
| 1 | Project Intake (New / Existing-stub) | P0 | Sprint 1 |
| 2 | AI Task Breakdown (PM Agent) | P0 | Sprint 1 |
| 3 | Agent Task Assignment (Routing Rules) | P0 | Sprint 2 |
| 4 | Kanban Status Board | P0 | Sprint 3 |
| 5 | Inter-Agent Communication Log | P0 | Sprint 2 (บันทึก) + Sprint 3 (แสดงผล) |
| 6 | Automated Deploy on Approval | P0 | Sprint 4 |
| 7 | Knowledge Graph Impact Preview | P1 | หลัง MVP (รอ DEP Engine จริง) |
| 8 | Multi-Project Portfolio View | P1 | Sprint 3 (แบบพื้นฐาน) |
| 9 | Agent Performance Analytics | P2 | หลัง MVP |

**Out of Scope MVP:** Billing/Invoicing, Agent marketplace ภายนอก, Mobile native app (ใช้ Responsive Web), Knowledge Graph จริง (รอ DEP v3.0 Phase 2+)

---

## 2. Architecture Decisions (mini-ADR)

การตัดสินใจที่เบี่ยงจาก Blueprint ฉบับเต็ม เพื่อให้เริ่มพัฒนาบนเครื่อง dev (Windows) ได้ทันทีโดยไม่เพิ่ม infrastructure ก่อนเวลา ทุกข้อมีเส้นทาง upgrade กลับสู่สเปกเต็มชัดเจน

### ADR-01: SQLite ก่อน → PostgreSQL ภายหลัง

- **ตัดสินใจ:** Dev environment ใช้ SQLite ผ่าน SQLAlchemy 2.x + Alembic migration; staging/production ใช้ PostgreSQL ตาม Blueprint
- **เหตุผล:** เริ่มรันได้ทันทีโดยไม่ต้องติดตั้ง Docker/PostgreSQL บนเครื่อง dev
- **ข้อกำหนดเพื่อให้ย้ายได้จริง:**
  - ฟิลด์ JSONB ทั้งหมด (`payload`, `diff`, `spec` structured) ใช้ SQLAlchemy `JSON` type (ทำงานได้ทั้ง SQLite และ PostgreSQL — ตอน deploy ค่อย map เป็น JSONB)
  - Primary key ใช้ UUID เก็บเป็น string (SQLite) / native UUID (PostgreSQL) ผ่าน custom type decorator
  - `depends_on (uuid[])` ใน SQLite เก็บเป็น JSON array — ห้ามใช้ PostgreSQL array type ตรงๆ ใน model
  - ห้ามเขียน raw SQL เฉพาะ dialect; query ทั้งหมดผ่าน SQLAlchemy ORM/Core
- **Upgrade path:** เปลี่ยน `DATABASE_URL` + รัน Alembic migration บน PostgreSQL (กำหนดไว้ใน Sprint 4)

### ADR-02: Metadata Engine เป็น Interface + Stub

- **ตัดสินใจ:** DEP v3.0 Metadata Platform Engine ยังไม่มีโค้ดจริง (อยู่ Phase 0-1) จึงกำหนด interface `MetadataProvider` ใน DEP-PM แล้ว implement `StubMetadataProvider` ที่คืน mock Baseline Report (tech debt / missing tests / doc coverage ตัวอย่าง) สำหรับ Brownfield flow
- **เหตุผล:** ไม่ block การพัฒนา New Project flow และไม่ต้องสร้าง DEP Engine ทั้งตัวก่อน
- **สัญญา interface (ร่าง):**
  ```python
  class MetadataProvider(Protocol):
      async def scan(self, repo_ref: str) -> ScanResult          # metadata records + confidence
      async def baseline_report(self, project_id: str) -> BaselineReport  # แปลงเป็น initial tasks ได้
  ```
- **Upgrade path:** เมื่อ DEP Engine จริงพร้อม เขียน `DepEngineMetadataProvider` ตัวใหม่มาเสียบแทน — Orchestrator และ intake flow ไม่ต้องแก้

### ADR-03: Message Bus เริ่มแบบ In-Process

- **ตัดสินใจ:** Inter-Agent Communication เริ่มเป็น in-process event dispatcher ที่ **เขียนทุกข้อความลงตาราง `agent_messages` เสมอ** (คงหลักการ auditable ของ Blueprint §10 ครบ) — ยังไม่ใช้ Redis Streams
- **เหตุผล:** Solo Mode รันใน process เดียว ไม่มีความจำเป็นต้อง cross-process messaging; ตาราง `agent_messages` คือ source of truth อยู่แล้ว
- **Upgrade path:** Sprint 4 เมื่อเพิ่ม Team Mode/multi-worker ค่อยเพิ่ม Redis Streams เป็น transport โดย schema ข้อความ (JSON: `from_agent`, `to_agent`, `message_type`, `payload`) คงเดิม

### ADR-04: Realtime เริ่มด้วย Polling/SSE

- **ตัดสินใจ:** Kanban Dashboard เริ่มด้วย polling (interval สั้น) หรือ Server-Sent Events — ยังไม่ทำ WebSocket + Redis Pub/Sub
- **เหตุผล:** ลดความซับซ้อนของ Sprint 3; ปริมาณผู้ใช้ช่วง MVP มีคนเดียว/ทีมเล็ก
- **Upgrade path:** เพิ่ม WebSocket endpoint ใน FastAPI + Redis Pub/Sub เมื่อย้ายเข้า PostgreSQL/Redis (Sprint 4 หรือหลัง MVP)

---

## 3. Repository Structure ที่จะ Scaffold (Sprint 1)

```
d_DEP-PM Platform/
├── backend/                      # FastAPI (Python 3.12+)
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Settings (pydantic-settings, .env)
│   │   ├── db/                   # SQLAlchemy engine, session, UUID type decorator
│   │   ├── models/               # ORM models (6 ตาราง — ดู §4)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── api/                  # Routers ตาม API Contract (§5)
│   │   ├── orchestrator/         # Task Orchestration Engine + State Machine
│   │   ├── agents/               # Agent runtime: solo mode personas, routing rules
│   │   ├── metadata/             # MetadataProvider interface + StubMetadataProvider
│   │   └── bus/                  # In-process message dispatcher (ADR-03)
│   ├── alembic/                  # Migrations
│   ├── tests/                    # pytest
│   ├── requirements.txt
│   └── .env.example
├── frontend/                     # Next.js 15 + TypeScript (สร้างจริง Sprint 3)
├── docs/
│   ├── DEVELOPMENT_PLAN.md       # ไฟล์นี้
│   └── adr/                      # ADR เต็มรูปแบบเมื่อมีการตัดสินใจใหม่
├── CLAUDE.md
├── PROJECT_STATUS.md
├── CHANGELOG.md
└── *.html                        # เอกสารอ้างอิงต้นทาง 3 ไฟล์ (read-only)
```

---

## 4. Data Model (6 ตาราง — จาก Blueprint §4)

```
projects      id(uuid pk), name, type('new'|'existing'), repo_url,
              status('planning'|'active'|'paused'|'archived'),
              metadata_registry_ref(nullable — รอ DEP Engine จริง), created_at

tasks         id(uuid pk), project_id(fk), title, description,
              status('backlog'|'planned'|'assigned'|'in_progress'|'review'|'done'|'deployed'),
              assignee_type('human'|'agent'), assignee_id,
              agent_role('pm'|'dev'|'senior_architect'), priority('P0'..'P3'),
              depends_on(JSON array — ADR-01), spec(text),
              estimate_points(int), revision_count(int, default 0),
              created_at, updated_at

agents        id(uuid pk), name, role, provider('anthropic'|'openai'|'google'),
              mode('solo'|'team'), status('idle'|'working'|'error'), last_active_at

agent_messages id(uuid pk), project_id(fk), task_id(fk), from_agent_id, to_agent_id,
              message_type('handoff'|'question'|'result'|'review_comment'),
              payload(JSON), created_at

deployments   id(uuid pk), project_id(fk), task_id(fk), triggered_by('auto'|'manual'),
              status('queued'|'running'|'success'|'failed'), environment, commit_sha, created_at

audit_log     id(uuid pk), actor_type('human'|'agent'), actor_id, action,
              entity_type, entity_id, diff(JSON), created_at
```

หมายเหตุ: เพิ่ม `revision_count` ใน `tasks` (ไม่มีใน Blueprint) เพื่อรองรับ Escalation Rule "Max Revision = 2" ของ State Machine โดยตรง — สถานะ `escalated` จัดเก็บผ่าน field แยกหรือ status เพิ่มเติม ตัดสินใจตอน implement Sprint 2

### Task State Machine (Blueprint §5)

```
Backlog → Planned → Assigned → InProgress → Review → Done → Deployed
                                   ↑           │
                                   └─ Revision ┘  (สูงสุด 2 รอบ)
                                Review --fail 2 ครั้ง--> Escalated → InProgress (คน/Senior Agent รับช่วง)
```

---

## 5. API Contract (Blueprint §13 — 11 endpoints)

```
POST   /api/projects                  → สร้างโปรเจกต์ { id, name, type, status }
POST   /api/projects/:id/scan         → เริ่ม Metadata scan (Sprint 1: ตอบจาก Stub)
GET    /api/projects/:id/tasks        → { data: [Task], pagination }
POST   /api/projects/:id/tasks        → สร้าง task (มนุษย์เพิ่มเอง หรือ PM Agent เรียก)
PATCH  /api/tasks/:id                 → เปลี่ยนสถานะ / assignee
POST   /api/tasks/:id/assign          → { assignee_type, assignee_id, agent_role }
GET    /api/tasks/:id/messages        → ประวัติ Inter-Agent Communication ของ task
POST   /api/agent-messages            → Agent ส่งข้อความ/handoff เข้า Message Bus
POST   /api/deployments               → trigger deploy (manual หรือจาก Orchestrator)
GET    /api/deployments/:id           → สถานะ deploy
GET    /api/portfolio                 → ภาพรวมทุกโปรเจกต์สำหรับ Dashboard
```

---

## 6. Sprint Plan (4 สปรินต์ / ~8 สัปดาห์)

### Sprint 1 (สัปดาห์ 1-2) — Foundation: Scaffold + Data Model + Intake

**Deliverables**

- โครง `backend/` รันได้จริง (FastAPI + SQLAlchemy + Alembic บน SQLite)
- Migration สร้าง 6 ตารางครบ + seed agent record (Claude solo)
- `POST /api/projects` (new + existing), `GET/POST tasks` endpoints
- **PM Agent Task Breakdown**: เรียก Claude API (persona: PM ตาม SOW) รับ requirement text → คืน Task Plan JSON → บันทึกเป็น tasks สถานะ `backlog` → ผู้ใช้ยืนยัน scope → เปลี่ยนเป็น `planned` (New Project Onboarding STEP 1-4 ของ Blueprint §6)
- `MetadataProvider` interface + `StubMetadataProvider` + `POST /api/projects/:id/scan` ตอบ mock Baseline Report ที่แปลงเป็น initial tasks ได้ (Blueprint §7 แบบ stub)

**Task Breakdown:** scaffold + config (1d), models + migrations (2d), project/task endpoints (2d), PM Agent breakdown + prompt (2d), stub metadata + scan endpoint (1d), tests (1d) — **รวม ~9 วัน**

**Definition of Done**

- `uvicorn` รันขึ้น, `pytest` ผ่านทั้งหมด
- สร้างโปรเจกต์ใหม่ + ส่ง requirement → ได้ task list ใน DB ที่มี id/title/spec/priority/depends_on ครบและ parse ได้ทุกครั้ง (Acceptance ตาม SOW PM)
- สร้างโปรเจกต์ existing → scan → ได้ mock baseline tasks ใน backlog

### Sprint 2 (สัปดาห์ 3-4) — Task Orchestration Engine + Solo Mode Runtime

**Deliverables**

- **State Machine** บังคับ transition ที่ถูกต้องเท่านั้น (ผิด transition → 409) + เขียน `audit_log` ทุกครั้ง
- **Routing Rules** ตาม Blueprint §9 (Solo Mode column): task type → Claude persona (PM / Architect / Developer / Reviewer)
- **Solo Mode Agent Runtime**: Orchestrator ดึง task `planned` → assign → เรียก Claude ด้วย system prompt ตาม persona → ผลงานเข้าสถานะ `review` → Reviewer persona ตรวจ → approve เป็น `done` หรือขอ revision (สูงสุด 2 → `escalated`)
- **Message Bus in-process** (ADR-03): ทุก handoff/result/review_comment ลง `agent_messages`
- Escalation: revision fail 2 ครั้ง → แจ้งผู้ใช้ + หยุด task ไว้ที่ `escalated`

**Task Breakdown:** state machine + audit (2d), routing rules + persona prompts (2d), agent runtime loop (3d), message bus + logging (1d), tests รวม state transition matrix (2d) — **รวม ~10 วัน**

**Definition of Done**

- E2E: requirement → task breakdown → orchestrator รันจนครบทุก task → สถานะ `done` โดยไม่มี manual intervention (happy path)
- Revision loop และ escalation ทำงานตามกติกา Max Revision = 2
- ทุก state change มี audit_log record และทุกการสื่อสารมี agent_messages record

### Sprint 3 (สัปดาห์ 5-6) — Kanban Dashboard + Message Log + Portfolio

**Deliverables**

- Scaffold `frontend/` (Next.js 15 + TypeScript)
- **Kanban Board** ต่อโปรเจกต์: คอลัมน์ตาม status, การ์ดแสดง assignee (human/agent pill), ลาก/ปุ่มเปลี่ยนสถานะเรียก `PATCH /api/tasks/:id`
- **Message Log Viewer**: บทสนทนา Agent ต่อ task (จาก `GET /api/tasks/:id/messages`)
- **Portfolio View** (`GET /api/portfolio`): จำนวน task ต่อสถานะทุกโปรเจกต์, agent ที่กำลังทำงาน, deploy ล่าสุด
- Refresh แบบ polling/SSE (ADR-04)
- หน้า New Project (กรอก requirement → เห็น task plan → ยืนยัน scope)

**Task Breakdown:** scaffold + API client (1d), Kanban board (3d), message log + task detail (1.5d), portfolio + new project form (2d), polish + tests (1.5d) — **รวม ~9 วัน**

**Definition of Done**

- ผู้ใช้ทำครบวงจรผ่าน UI: สร้างโปรเจกต์ → ยืนยัน scope → เห็น agent ทำงาน real-time (polling) → task เลื่อนคอลัมน์จนถึง Done
- ดูบทสนทนา agent ย้อนหลังของทุก task ได้

### Sprint 4 (สัปดาห์ 7-8) — Deploy Pipeline + PostgreSQL/Redis + Team Mode + UAT

**Deliverables**

- **Automated Deploy** (Blueprint §12): task เข้า `done` → trigger GitHub Actions ผ่าน `repository_dispatch` (staging อัตโนมัติ, production มี Manual Approval Gate ต่อโปรเจกต์) + `deployments` endpoints ครบ
- **ย้าย DB → PostgreSQL** (ADR-01) + เพิ่ม Redis (message transport + pub/sub ถ้าทัน — ADR-03/04)
- **Team Mode**: config mapping role → provider (Codex Dev = OpenAI, Gemini SR = Google) โดย Orchestrator ไม่แก้ logic (เห็นแค่ agent_role ตาม Blueprint §8) — ต้องมี `OPENAI_API_KEY` + `GEMINI_API_KEY`
- Security ขั้นต่ำตาม Blueprint §15: secrets ผ่าน env เท่านั้น, agent เป็น Contributor เสมอ, audit ครบ
- UAT + Handover doc (`docs/runbook.md`)

**Task Breakdown:** deploy pipeline + dispatch (3d), PostgreSQL migration + Redis (2d), team mode providers (3d), UAT + fix (2d), handover (1d) — **รวม ~11 วัน**

**Definition of Done**

- Task ที่ approve แล้ว trigger workflow จริงบน repo ทดสอบ, สถานะ deploy สะท้อนกลับใน dashboard
- ระบบรันบน PostgreSQL โดย test suite เดิมผ่านทั้งหมด
- สลับ Solo ↔ Team Mode ได้ด้วย config โดยไม่แก้โค้ด orchestrator

**Estimation รวม:** 39 วันทำงาน + buffer ~20% ≈ **47-49 วัน (~8 สัปดาห์)** สอดคล้อง Blueprint §16

---

## 7. Risk Register

| # | ความเสี่ยง | โอกาส | ผลกระทบ | ระดับ | แผนรับมือ |
|---|-----------|-------|---------|-------|-----------|
| 1 | **DEP v3.0 Engine จริงยังไม่มี** — Brownfield ใช้ stub นานเกินไปจนผู้ใช้เข้าใจผิดว่า scan ได้จริง | สูง | กลาง | 🔴 | ระบุ "(mock)" ชัดใน UI/response; interface ล็อกไว้แล้ว (ADR-02); วางแผน DEP Engine เป็นโปรเจกต์แยกหลัง MVP |
| 2 | **SQLite → PostgreSQL migration มีพฤติกรรมต่างกัน** (JSON query, concurrency) | กลาง | กลาง | 🟡 | คุมผ่านกติกา ADR-01 (ORM-only, JSON type กลาง); รัน test suite บน PostgreSQL ใน CI ตั้งแต่ Sprint 2 ถ้าเป็นไปได้ |
| 3 | ต้นทุน API เกินงบเมื่อเปิด Team Mode | กลาง | สูง | 🔴 | Budget threshold + auto-switch กลับ Solo Mode; `MAX_TOKENS_PER_TASK` ต่อ task |
| 4 | Auto-deploy พังหน้า production | ต่ำ | สูง | 🔴 | บังคับผ่าน staging + smoke test เสมอ; production ตั้ง Manual Gate เป็น default ช่วง MVP |
| 5 | Agent มอบหมายงานผิดประเภท | กลาง | กลาง | 🟡 | Log routing decision ทุกครั้ง; ปรับ Routing Rules จากข้อมูลจริงรายสัปดาห์ |
| 6 | ข้อมูลอ่อนไหวหลุดเข้า prompt ของ Agent (PDPA) | ต่ำ | สูง | 🔴 | Field masking ก่อนส่งเข้า prompt/message bus; ห้าม secrets ใน task spec |
| 7 | PM Agent คืน JSON parse ไม่ได้ | กลาง | ต่ำ | 🟡 | ใช้ structured output/validation + retry; มี fallback plan ตามตัวอย่างใน AI Dev Team Guide |

---

## 8. Success Metrics (Blueprint §17)

| KPI | เป้าหมาย |
|-----|----------|
| Time from Requirement → First Deploy | ลดลง 50% เทียบ workflow เดิม |
| Task Auto-routing Accuracy | > 90% ไม่ต้อง reassign มือ |
| Escalation Rate (revision fail 2 ครั้ง) | < 10% ของ task ทั้งหมด |
| Deploy Success Rate (staging → prod) | > 95% |

---

## 9. Open Questions (ต้องการคำตอบก่อน/ระหว่าง Sprint 1)

1. **Claude API key + budget:** ใช้ key ไหนสำหรับ PM Agent (Anthropic API โดยตรง) และมี budget/เดือนเท่าไร — กระทบการตั้ง `MAX_TOKENS_PER_TASK`
2. **Target repo สำหรับทดสอบ Deploy Pipeline (Sprint 4):** ใช้ repo ไหนเป็น guinea pig สำหรับ `repository_dispatch` (ต้องเป็น GitHub repo ที่มีสิทธิ์ตั้ง workflow)
3. **`git init` โปรเจกต์นี้:** โฟลเดอร์ยังไม่เป็น git repo — ควร init ก่อนเริ่ม Sprint 1 (แนะนำ: ทำ)
4. **Human assignee ช่วง MVP:** มีผู้ใช้คนเดียว (Vinit) หรือหลายคน — กระทบว่าต้องทำ user/auth ตั้งแต่ Sprint ไหน (Blueprint กำหนด RBAC Owner/Contributor/Viewer แต่ MVP อาจใช้ single-user ไปก่อน)
5. **ชื่อ model ที่จะใช้จริง:** เอกสารเก่าอ้าง `claude-sonnet-4-6` / `gpt-4o` / `gemini-2.5-pro` — ควรกำหนดผ่าน env (`CLAUDE_MODEL` ฯลฯ) และอัปเดตเป็นรุ่นล่าสุดตอน implement

---

## 10. ขั้นตอนถัดไป

1. ผู้ใช้รีวิวเอกสารนี้ + ตอบ Open Questions ข้อ 1, 3
2. อนุมัติเริ่ม **Sprint 1** → scaffold backend ตาม §3 และทำ Deliverables ตาม §6
3. เมื่อจบแต่ละสปรินต์: อัปเดต `PROJECT_STATUS.md` + `CHANGELOG.md` ตามกติกาใน `CLAUDE.md`
