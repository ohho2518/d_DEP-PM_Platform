# AGENTS.md

> **Single source of truth for every AI coding agent working in this repository.**
> Claude Code, Gemini CLI, Codex, Cursor, and any other agent read this file.
> `CLAUDE.md` and `GEMINI.md` are pointers to this file — do not duplicate content there.

---

## 1. Role

You are an AI coding agent working inside this repository.

Your job: develop, maintain, debug, refactor, document, and improve this project — while **preserving existing behavior** unless the user explicitly asks for a change.

---

## 2. Read Before Every Task

| Order | File | When |
|---|---|---|
| 1 | `AGENTS.md` (this file) | Always |
| 2 | `PROJECT_STATUS.md` | Always — this is the continuity file |
| 3 | `_CANON\WORKING_RULES.md` (path below) | Before touching code, DB, or UI |
| 4 | `CHANGELOG.md` | Only for history, release notes, or debugging past decisions |

เอกสารเฉพาะทางตามงานที่ทำ:

- แตะ API → `docs/API.md` · แตะ schema/migration → `docs/DATABASE.md`
- แตะ orchestrator/state machine → `docs/SYSTEM_DOCUMENTATION.md` §9
- แตะ frontend → `docs/SYSTEM_DOCUMENTATION.md` §13 + `frontend/AGENTS.md`
- แตะการเชื่อมกับ d_CEO → `docs/INTEGRATION_CEO.md` (**contract — provider เป็นเจ้าของ**)
- แตะกติกา "แก้โค้ดยังไงไม่พัง" → `docs/AI_AGENT_GUIDE.md`
- แตะสถาปัตยกรรม/ADR → `docs/ARCHITECTURE.md` + `docs/DEVELOPMENT_PLAN.md` §2

**Do not scan the whole repository** unless the task genuinely requires it.

---

<!-- CANON-POINTER:START — สร้างโดย new-project-studio · แก้ต้นฉบับที่ 6_KM\d_InnoHub\_CANON\POINTER_BLOCK.md -->
## 📌 เอกสารกลาง (Canon) — อ่านจากต้นฉบับ ห้ามคัดลอกมาไว้ในโปรเจกต์นี้

ไฟล์ด้านล่างมี **ต้นฉบับเดียวของทั้ง Dev_Proj** อยู่ที่ `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\`
ถ้าต้องใช้ ให้เปิดอ่านจาก path นั้นตรงๆ — **ห้ามสร้างสำเนาไว้ในโปรเจกต์นี้**

| ต้องรู้เรื่อง | เปิดไฟล์นี้ |
|---|---|
| กฎความปลอดภัยตอนแก้โค้ด / ฐานข้อมูล / UI | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\WORKING_RULES.md` |
| สภาพแวดล้อมเครื่องที่ใช้พัฒนา | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\ENVIRONMENT.md` |
| ตัวเลข / ชื่อลูกค้า / อีเมล ที่ใช้ในเอกสารส่งออก | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\CANONICAL_FACTS.md` |
| พรอมป์ต์มาตรฐาน (สร้างเอกสาร / วิเคราะห์ระบบเดิม) | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\prompts\` |
| กติกาของคลังกลางเอง | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\README.md` |

**กฎเหล็ก 3 ข้อ**

1. ตัวเลข ชื่อลูกค้า อีเมล และวันที่ ที่จะปรากฏในเอกสารส่งออกภายนอก — ดึงจาก `CANONICAL_FACTS.md` เท่านั้น **ห้ามพิมพ์ใหม่จากความจำ**
2. เจอข้อมูลผิด → ไปแก้ที่ `_CANON/` **ห้ามแก้เฉพาะที่นี่**
3. **ห้ามก๊อบไฟล์ canon กลับเข้ามาในโปรเจกต์นี้** ไม่ว่าด้วยเหตุผลใด
<!-- CANON-POINTER:END -->

---

## 3. Project Overview

- **Project name:** **DEP-PM Platform** — AI-Native Project Management Platform
- **Purpose:** แพลตฟอร์มบริหารโปรเจกต์ที่มนุษย์และ AI Agent ทำงานบนบอร์ดเดียวกัน — รับ requirement → AI แตกงาน → มอบหมาย Agent/คน → Kanban → auto-deploy เมื่อผ่าน review
- **Target users:** ทีมพัฒนา dPRO (dPRO AI Parking, MChat, Farm Lab และโปรเจกต์อนาคต) — MVP เป็น single-user (Vinit)
- **Main features:** Project Intake (New/Existing-stub) · AI Task Breakdown · Agent Task Assignment (Solo/Team Mode) · Kanban Board · Inter-Agent Communication Log · Automated Deploy — รายละเอียดใน `docs/DEVELOPMENT_PLAN.md` §1
- **Current status:** **MVP ครบ 4 สปรินต์** (pytest 60/60, ruff clean, UAT หลักผ่าน) — งานถัดไปคือ**ต่อสายรับงานจาก d_CEO** (§3.1) ดู `PROJECT_STATUS.md`

**เอกสารอ้างอิงต้นทาง (read-only — ห้ามแก้):**

| ไฟล์ | คืออะไร |
|---|---|
| `DEP-PM Platform Blueprint v1.0.html` | สเปกหลักของระบบนี้ |
| `DEP v3.0 Master Plan.html` | แพลตฟอร์มแม่ (ยังไม่มีโค้ดจริง — ใช้ stub, ADR-02) |
| `ai-dev-team-complete.html` | Agent Routing Rules + SOW ของแต่ละ persona |
| `docs/DEVELOPMENT_PLAN.md` | แผนพัฒนาที่อนุมัติแล้ว (สปรินต์, ADR-01..04, data model, API contract) |

### 3.1 ตำแหน่งใน ecosystem dPRO — **DEP-PM = Team Lead R&D**

สายบังคับบัญชาจริง (ยืนยันโดย Vinit, 2026-08-02):

```
Vinit (CEO) ──สั่ง──► d_Jarvis ──REST──► d_CEO ──delegate──► DEP-PM (repo นี้)
             เสียง/ข้อความ/ภาพ  "หน้า"      "สมอง"           "Team Lead R&D"
                                NLU+การ์ด  task+เลือกทีม     ลงมือทำงานพัฒนาจริง
                                                  ▲                │
                                                  └──── รายงานผล ───┘
                                                    → QC gate → Vinit เคาะ
```

- **ผู้สั่งงานคือ Vinit เสมอ** — d_CEO ไม่ใช่เจ้านายของ repo นี้ แต่เป็นตัวแปลงคำสั่งเป็น task แล้วกระจายให้ทีม
- **ทำไม DEP-PM ไม่ใช่ของซ้ำกับ d_CEO:** orchestrator ของ d_CEO เรียก Claude **แบบไม่มี tool** → ผลงานเป็นข้อความล้วน ไม่แตะไฟล์จริง ไม่ deploy (`d_CEO\docs\API.md`) — DEP-PM คือที่ที่งานพัฒนาเกิดขึ้นจริง
- **กติกา "ไม่ทำระบบ task ซ้อน":** ยึด **1 task ธุรกิจใน d_CEO = 1 project ใน DEP-PM** — task ย่อยบนบอร์ดเราเป็นรายละเอียดการทำงาน ไม่ใช่ทะเบียนงานธุรกิจชุดที่สอง
- ⚠️ เอกสาร 2 จุดในรีโปอื่นยังเขียนว่าให้ "merge DEP-PM เข้า Solo_CEO" (`d_Jarvis\docs\VISION.md` §5, `d_CEO\project_plan_solo_ceo.md` §9.1) — **ล้าสมัยแล้ว** ต้องให้ session ของรีโปนั้นแก้เอง **ห้ามแก้ข้ามรีโป**

**พอร์ตที่จองแล้วในเครื่อง (ห้ามชน):**

| พอร์ต | เจ้าของ |
|---|---|
| 8000 | **d_CEO / Solo_CEO API** — รันค้างตลอดผ่าน Task Scheduler, d_Jarvis พึ่งพาอยู่ **ห้ามหยุด** |
| 8100 | d_OCR_Engine · **8200** d_STT_Engine · **8300** d_InnoHub |
| 8400 | **d_Jarvis web channel** (`run_web.py`, `WEB_PORT` — รันค้างผ่าน Task Scheduler เช่นกัน) |
| **8500** | **DEP-PM backend (repo นี้)** |
| 3000 | DEP-PM frontend (`next dev`) |

> ⚠️ **ตรวจพอร์ตด้วยของจริงก่อนจอง อย่าเชื่อเอกสารอย่างเดียว** — 2026-08-02 เคยเลือก 8400
> เพราะอ่าน `.env.example` ของ Jarvis เฉพาะบรรทัด base URL ของ client แล้วพลาดบรรทัด `WEB_PORT=8400`
> ผลคือ Windows ยอมให้ bind ซ้อน (`127.0.0.1` ทับ `0.0.0.0`) แล้ว**บังหน้าเว็บ Jarvis เงียบ ๆ**
> — คำสั่งตรวจ: `Get-NetTCPConnection -LocalPort <port> -State Listen`

---

## 4. Tech Stack

**สถานะ: CONFIRMED ทั้ง backend และ frontend**

| Item | Value |
|---|---|
| Language | Python 3.12+ (backend) · TypeScript (frontend) |
| Framework | FastAPI 0.115 (backend) · **Next.js 16.2.10** App Router (frontend) |
| Runtime | uvicorn (dev, port **8500**) · node (next dev, port 3000) |
| Package manager | pip (backend) · npm (frontend) |
| Database | SQLite (dev) → PostgreSQL (staging/prod) — ADR-01 |
| ORM | SQLAlchemy 2.x + Alembic |
| Authentication | **ยังไม่มี** (single-user MVP) — ดู `docs/SECURITY.md` |
| UI library | Tailwind CSS 4 (มากับ scaffold) — **ตัดสินใจไม่ใช้ component library** เพื่อลด dependency |
| Testing | pytest (backend, 60 เคส) · frontend ยังไม่มี unit test (verify ด้วย `npm run build`) |
| Lint | ruff (`backend/ruff.toml` — E,F,I,B,UP; ignore E501,B008) |
| Deployment target | GitHub Actions → Vercel (FE) + Render/Railway (BE) — ยังไม่ทำจริง |

> ⚠️ **Next.js 16 ไม่ใช่ 15 ตามแผนเดิม** (create-next-app@latest) — dynamic route `params` เป็น `Promise` ต้อง unwrap ด้วย `React.use()` ดู `frontend/AGENTS.md`

---

## 5. Project Structure

```text
docs/DEVELOPMENT_PLAN.md              แผนพัฒนาที่อนุมัติแล้ว (สปรินต์, ADR, schema, API)
docs/{ARCHITECTURE,SYSTEM_DOCUMENTATION,API,DATABASE,SECURITY,AI_AGENT_GUIDE}.md
docs/INTEGRATION_CEO.md               contract กับ d_CEO (เราเป็น consumer — provider เป็นเจ้าของ)
docs/{PROJECT_OVERVIEW,RISK_REGISTER}.md   ภาพรวมธุรกิจ + ทะเบียนความเสี่ยง
docs/runbook.md                       Operations/handover + UAT checklist
docs/github-workflow-example.yml      Workflow template สำหรับ repo เป้าหมาย
PROJECT_STATUS.md                     สถานะล่าสุด + next tasks (continuity file)
CHANGELOG.md                          ประวัติการเปลี่ยนแปลง
AGENTS.md                             ไฟล์นี้ (ต้นฉบับกติกา) · CLAUDE.md/GEMINI.md = pointer
*.html (3 ไฟล์)                       เอกสารอ้างอิงต้นทาง — read-only ห้ามแก้
BackUp/                               สำเนาก่อนแก้ตาม WORKING_RULES (gitignored)

backend/app/{main,config,constants}.py  FastAPI entry + settings + enums กลาง
backend/app/db/                       engine, session, GUID/JSON portable types (ADR-01)
backend/app/models/                   ORM 6 ตาราง
backend/app/schemas/                  Pydantic (project, task, scan)
backend/app/api/                      routers: projects, tasks, agent_messages, portfolio, deployments, ceo
backend/app/agents/                   personas 4 บทบาท, routing, runtime, providers, pm breakdown
backend/app/orchestrator/             State Machine (transition-only) + engine (Solo Mode loop)
backend/app/bus/                      In-process message bus (ADR-03)
backend/app/metadata/                 MetadataProvider interface + Stub (ADR-02)
backend/app/integrations/             client ของระบบข้างเคียง — ceo_client.py (d_CEO) §3.1
backend/app/services/                 audit + task-plan persistence + deploy dispatcher + ceo_sync + runs (Run Manager)
backend/alembic/                      migrations (schema, seed agent, token columns)
backend/tests/                        pytest 60 เคส
backend/ruff.toml                     lint config

frontend/src/lib/                     types.ts (mirror backend schema!), api.ts, usePolling.ts
frontend/src/app/page.tsx             Portfolio view
frontend/src/app/projects/new/        New Project flow (STEP 1-4)
frontend/src/app/projects/[id]/       Kanban Board + Task detail + Message Log
frontend/src/app/deployments/         Deployments view (ประวัติ deploy ทุกโปรเจกต์)
frontend/src/components/AgentOffice.tsx  แอนิเมชันสถานะ agent บนหน้าบอร์ด
```

---

## 6. Commands

รันจากโฟลเดอร์ `backend/` (มี `.venv` แล้ว)

```bash
# Install
cd backend
python -m venv .venv
.venv\Scripts\activate                       # *nix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                         # ใส่ ANTHROPIC_API_KEY เพื่อเปิด PM Agent จริง

# Development — Backend
cd backend
alembic upgrade head                         # สร้าง schema + seed Claude Solo agent (SQLite)
uvicorn app.main:app --reload --port 8500    # http://127.0.0.1:8500  (docs: /docs)

# Development — Frontend (อีก terminal; ครั้งแรก: npm install + cp .env.local.example .env.local)
cd frontend
npm run dev                                  # http://localhost:3000

# Build
cd frontend
npm run build                                # Next.js production build (รวม typecheck)

# Test
cd backend
pytest                                       # 60 tests

# Lint / Format
cd backend
ruff check app tests alembic                 # config ใน backend/ruff.toml
ruff check --fix app tests alembic           # auto-fix import order ฯลฯ
```

> **ห้ามใช้ `--port 8000`** — ชนกับ d_CEO ที่รันค้างอยู่ (§3.1)

---

## 7. Environment Variables

ชื่อและความหมายเท่านั้น — **ห้ามเขียนค่าจริงลงไฟล์ใดในรีโป** (`.env` gitignored)

**`backend/.env`** (ดู `backend/.env.example`)

```env
DATABASE_URL=          # connection string; dev = SQLite file, prod = PostgreSQL (ADR-01)
ANTHROPIC_API_KEY=     # เปิด PM Agent + Solo Mode จริง; ว่าง = fallback path
CLAUDE_MODEL=          # model id ของ Solo Mode
MAX_TOKENS_PER_TASK=   # เพดาน token ต่อ task (Risk #3)
AGENT_MODE=            # solo | team
OPENAI_API_KEY= OPENAI_MODEL= GEMINI_API_KEY= GEMINI_MODEL=   # Team Mode
GITHUB_TOKEN= GITHUB_REPO=    # deploy dispatch; ว่าง = stub mode
AUTO_DEPLOY_ENABLED=   # true = task done → staging deployment อัตโนมัติ
CEO_API_BASE=          # base URL ของ d_CEO (ปริยาย http://127.0.0.1:8000) — ว่าง = ปิดการเชื่อม
CEO_TEAM_NAME=         # ชื่อทีมใน d_CEO ที่เรารับงาน (ปริยาย "Research & Development")
CEO_TIMEOUT_SECONDS=   # timeout ต่อ request ไป d_CEO (ปริยาย 15)
FRONTEND_ORIGIN=       # CORS origin เดียว (ไม่ใช่ *)
```

**`frontend/.env.local`**

```env
NEXT_PUBLIC_API_URL=   # base URL ของ backend — ค่าปัจจุบัน http://127.0.0.1:8500
```

---

## 8. Architecture Notes

- **Pattern:** Layered Monolith + Pluggable Engine Interfaces — `api → services/orchestrator → models → db` โดยจุดที่คาดว่าจะเปลี่ยนเป็น Protocol/interface
- **Frontend flow:** ทุกหน้าเป็น client component + `usePolling` (4 วิ, หยุดเมื่อแท็บไม่ active) — ไม่มี global store
- **Backend flow:** router บาง ๆ (HTTP↔service) → orchestrator/services (business logic + เจ้าของ transaction) → ORM
- **API flow:** REST JSON, error format ของ FastAPI, **409 = ผิด State Machine transition** (เอกลักษณ์ของระบบนี้)
- **Database flow:** 6 ตาราง, UUID ผ่าน `GUID` type decorator, JSON ผ่าน SQLAlchemy `JSON` — portable ระหว่าง SQLite↔PostgreSQL
- **Auth flow:** ยังไม่มี — bind localhost เท่านั้น
- **External services:** Anthropic (Solo Mode) · OpenAI + Gemini (Team Mode) · GitHub `repository_dispatch` (deploy) · **d_CEO** (รับงาน/รายงานผล) — ทุกตัวมี fallback ไม่ล้มทั้งระบบเมื่อ key ขาดหรือปลายทางปิด
- **การเชื่อมกับ d_CEO:** ทุกการยิง HTTP อยู่ใน `integrations/ceo_client.py` **ไฟล์เดียว** (ที่อื่นห้ามยิงเอง) · business logic อยู่ใน `services/ceo_sync.py` · orchestrator ไม่รู้จักทั้งคู่ · **ส่งกลับได้แค่ `in_progress`/`qc_review`** ห้ามปิดงานเอง — ดู `docs/INTEGRATION_CEO.md`
- **รอบรัน orchestrator เป็นงานเบื้องหลัง (Phase 2):** `POST /:id/run` ตอบ **202 + `run_id`** ทันที · ความคืบหน้าที่ `GET /:id/run` · **1 โปรเจกต์ = 1 รอบรัน** (ซ้อน = 409) · ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียวเหมือน bus — วิธีรันทั้งหมดอยู่ใน `services/runs.py` **ไฟล์เดียว** (engine ไม่รู้ว่าตัวเองถูกรันใน thread)
- **จุดเสียบ 3 จุด (extensibility):** `PersonaExecutor` (provider ใหม่) · `MetadataProvider` (DEP Engine จริง) · bus transport (Redis)
- **ADR-01..04** อยู่ใน `docs/DEVELOPMENT_PLAN.md` §2 — SQLite ก่อน · Metadata stub · in-process bus · polling

---

## 9. Coding Rules

1. Read the relevant files **before** editing.
2. Make the **smallest safe change** — one unit of work at a time (WORKING_RULES Rule 2).
3. Do not rewrite whole files unless necessary.
4. Preserve existing behavior.
5. Match the existing code style (type hints ทุก signature, `from __future__ import annotations`, docstring ไทย+อังกฤษผสมตาม codebase เดิม).
6. Do not add dependencies without a stated reason.
7. Do not remove features without user approval.
8. Never hardcode secrets.
9. Prefer clear and maintainable over clever.
10. State your assumption **before** making any major change.

### 9.1 Project-specific rules (บังคับ — ฝ่าฝืน = bug)

1. **ห้าม set `task.status` ตรง ๆ** — ต้องผ่าน `app/orchestrator/state_machine.transition()` เท่านั้น (validate + เขียน audit อัตโนมัติ; ผิด transition → API ตอบ 409)
2. **ห้าม INSERT `agent_messages` ตรง ๆ** — ทุกข้อความระหว่าง agent ต้องผ่าน `app/bus.publish()` (ADR-03: persist เสมอ)
3. **`transition()` / `publish()` / `record_audit()` ไม่ commit เอง** — router commit ต่อ request, engine commit ต่อ task
4. **Dependency direction ห้ามย้อนศร:** `api → orchestrator/services → models → db` · orchestrator ห้าม import api · models ห้าม import schemas · `agents/runtime.py` ห้าม import orchestrator
5. **ADR-01 (portability):** ห้าม raw SQL เฉพาะ dialect · UUID ผ่าน `GUID` · JSON ผ่าน SQLAlchemy `JSON` · ห้าม PostgreSQL array type
6. **Frontend↔Backend sync:** แก้ status/transition/response shape ฝั่ง backend → แก้ `frontend/src/lib/types.ts` (`ALLOWED_TRANSITIONS`, `STATUS_ORDER`, สี) **ในคอมมิตเดียวกัน**
7. **จุดเสียบ อย่า bypass:** provider ใหม่ = implement `PersonaExecutor` · metadata จริง = implement `MetadataProvider` · อย่าแก้ orchestrator เพื่อ special-case provider ใดตัวหนึ่ง
   · `execute(task, role, feedback=None, **context=None**)` — **ต้องส่ง `context` ต่อให้โมเดลด้วย**
   (ผลงานจริงของงานก่อนหน้า) ไม่งั้นงานที่ต้องทำต่อจากของเดิมจะได้แค่โครงเปล่าแล้วโดนปฏิเสธ
8. **ห้ามลบ fallback path** (no-key → fallback) — เป็นคุณสมบัติเชิงสัญญา ไม่ใช่โค้ดชั่วคราว
9. Enums กลางอยู่ `constants.py` ที่เดียว — ห้าม string literal ของ status/role ในโค้ดใหม่
10. **สถานะของ d_CEO เป็นคนละชุดกับ `TaskStatus` ของเรา** — ใช้ค่าคงที่ `CEO_STATUS_*`
    ใน `integrations/ceo_client.py` อย่าเอา `TaskStatus` ไปส่งข้ามระบบ (บังเอิญชื่อซ้ำบางตัว)
11. **ห้ามปิดงานฝั่ง d_CEO เอง** — ส่งได้แค่ `in_progress`/`qc_review` ทุกงานต้องผ่าน QC gate
12. **งานเบื้องหลังห้ามใช้ session ของ request** — `get_db` ปิดมันพร้อม response · ขอ session ใหม่จาก
    `get_session_factory` (1 รอบรัน = 1 session) และห้ามส่ง ORM object ข้าม thread

---

## 10. Task Workflow

For **every** task:

1. Read `AGENTS.md` + `PROJECT_STATUS.md`.
2. Identify **only** the files needed for this task.
3. Inspect those files before editing.
4. Back up per `_CANON\WORKING_RULES.md` (Rule 1 ไฟล์ · Rule 3 ฐานข้อมูล) — `BackUp/<TaskName>_yyyyMMdd_HHmmss/`
5. Make minimal changes.
6. Run checks: `pytest` เต็มชุดเสมอ · แตะ frontend → `npm run build` · `ruff check app tests alembic`
7. Update `PROJECT_STATUS.md`.
8. Update `CHANGELOG.md` if user-facing behavior changed.
9. Update `AGENTS.md` if architecture, commands, structure, or rules changed.

---

## 11. Context Efficiency

- Do not scan the whole project by default · do not open unrelated files · prefer targeted reads.
- `PROJECT_STATUS.md` is the **main continuity file** — keep it current and concise.
- Move long history to `CHANGELOG.md`.
- Keep `AGENTS.md` about stable rules, **not** daily progress.

---

## 12. Domain Rules

### Database

1. Inspect the schema before changing DB code.
2. Never change schema without a migration strategy — **สร้าง revision ใหม่เสมอ ห้ามแก้ migration ที่ apply แล้ว**
3. No destructive migrations or data deletion unless explicitly requested.
4. Keep schema, API, types, and UI aligned.
5. Update `docs/DATABASE.md` after schema changes.
6. **Back up before any DB change** — `backend/dep_pm.db` **คือข้อมูลจริงของผู้ใช้ ห้ามลบเด็ดขาด** (เคยลบพลาดมาแล้ว 2026-07-06)
7. Autogenerate migration ต้อง**ตรวจมือเสมอ** — เคยขาด `import app.db.types` (บทเรียนจริง Sprint 1)

### UI

1. Reuse existing components · keep design and responsive behavior consistent.
2. No redesign unless requested.
3. Log visible behavior changes in `CHANGELOG.md`.
4. TS types มาจาก `lib/types.ts` เท่านั้น — อย่านิยาม interface ซ้ำในหน้า

### API

1. Preserve existing request/response contracts unless asked.
2. Validate all input (Pydantic ทุก endpoint).
3. Handle errors safely; never leak internal errors to users.
4. Update related frontend calls **and** `docs/API.md` when an API changes.
5. เพิ่ม endpoint = router บาง + Pydantic schema + integration test ผ่าน TestClient + อัปเดต `docs/API.md`

### Testing

- ทุก endpoint ใหม่ → integration test (ดู `tests/conftest.py` pattern: in-memory SQLite ต่อ test)
- ทุกกติกา business ใหม่ → test เฉพาะ (ดู `test_state_machine.py` transition matrix เป็นแบบ)
- **ห้าม mock HTTP ของ anthropic** — inject executor ผ่าน `run_project(executor=…)` แทน

---

## 13. Common Tasks

**New feature:** understand current flow → locate related files → implement the smallest complete version → add validation + error handling → run checks → update status files.

**Bug fix:** reproduce or understand → find the root cause → fix only the related code → check for side effects → update status.

**Refactor:** preserve behavior → keep it small → never mix refactor with feature changes → run checks.

**เพิ่ม task status ใหม่:** 6 จุดต้องแก้พร้อมกัน — `constants.TaskStatus` → `ALLOWED_TRANSITIONS` (backend) → `frontend/src/lib/types.ts` (type + ALLOWED_TRANSITIONS + STATUS_ORDER + สี) → `test_state_machine` → `docs/SYSTEM_DOCUMENTATION.md` §9 → `docs/API.md`

---

## 14. Never Do

- Commit secrets, API keys, tokens, private keys, or customer data.
- ลบ `backend/dep_pm.db` หรือไฟล์สำคัญอื่น.
- แก้/ลบไฟล์ `*.html` 3 ไฟล์ (read-only spec) หรือ migration ที่ apply แล้ว.
- Rewrite the whole project · change business logic outside the requested task.
- Upgrade major dependencies without approval · format the entire repository unless requested.
- Guess a command that does not exist in the project.
- เปลี่ยน `MAX_REVISIONS` semantics โดยไม่อัปเดต `docs/SYSTEM_DOCUMENTATION.md` §9 + tests.
- Major architecture change โดยไม่ผ่านผู้ใช้ — ต้องเป็น ADR ใหม่ใน `docs/DEVELOPMENT_PLAN.md` §2.
- **แก้ไฟล์ในรีโปอื่น** (d_CEO, d_Jarvis, _CANON) — ส่งเป็นคำขอให้ session ของรีโปนั้นทำเอง.

---

## 15. End-of-Task Report

Always close with:

1. **Files changed**
2. **What changed**
3. **Why**
4. **Checks run** (test / lint / build) and results
5. **Not completed / known issues**
6. **Recommended next step**

`PROJECT_STATUS.md` ต้องมีครบ 7 หัวข้อ: งานที่เสร็จ · ไฟล์ที่เปลี่ยน · สถานะปัจจุบัน · งานถัดไป · ปัญหาที่รู้ · การตัดสินใจ · คำถามถึงผู้ใช้
