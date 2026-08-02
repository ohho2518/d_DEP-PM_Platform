# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-08-02 | สถานะโดยรวม: **Phase 0 + Phase 1 เสร็จ**
> — DEP-PM **ต่อสายรับงานจาก d_CEO ได้แล้ว** ในบทบาท Team Lead R&D
> (เหลือทดสอบกับงาน R&D จริง + `/run` async)

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (สำรองล่าสุด `BackUp/Phase0Cleanup_20260802_224442/`)
- **พอร์ตเปลี่ยนเป็น 8400 แล้ว** — `uvicorn app.main:app --reload --port 8400`
  · :8000 เป็นของ **d_CEO** ที่รันค้างตลอดผ่าน Task Scheduler และ d_Jarvis พึ่งพาอยู่ **ห้ามหยุด**
  · ยืนยันแล้ววันนี้ว่า DEP-PM :8400 กับ d_CEO :8000 รันคู่กันได้ ทั้งคู่ `/health` ตอบ ok
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO (`ohho2518/d_DEP-PM_Platform`)
- โปรเจกต์ในระบบ: "Demo: Booking API" (4 done), "d_ACC" (17 backlog), "Deploy UAT"
- DB migrate เป็น head `c7d4e2a9b1f3` แล้ว · servers ไม่ได้รันค้างไว้ (สตาร์ตเองตาม runbook)

## ตำแหน่งใน ecosystem (ยืนยันโดย Vinit 2026-08-02)

```
Vinit (CEO) → d_Jarvis (หน้า) → d_CEO (สมอง) → delegate → DEP-PM (Team Lead R&D)
                                                    ↑ รายงานผล → QC gate → Vinit เคาะ
```

- ผู้สั่งงานคือ Vinit เสมอ — d_CEO เป็นตัวแปลงคำสั่งเป็น task แล้วกระจายให้ทีม ไม่ใช่เจ้านายของรีโปนี้
- DEP-PM ไม่ซ้ำกับ d_CEO เพราะ orchestrator ของเขาเรียก LLM **แบบไม่มี tool** → ได้แค่ข้อความ
  ส่วนที่นี่แตกงาน เขียนงาน ตรวจงาน และ deploy ได้จริง
- ยึด **1 task ธุรกิจใน d_CEO = 1 project ที่นี่** (ไม่สร้างทะเบียนงานธุรกิจซ้อน)

## Completed Work

### Phase 1 — ต่อสายรับงานจาก d_CEO (2026-08-02)

- **`integrations/ceo_client.py`** — ไฟล์เดียวที่ยิง HTTP ไป d_CEO (ที่อื่นห้ามยิงเอง)
  · `health/list_teams/resolve_team_id/list_tasks/patch_task` · error → `CeoUnavailable`
  · **guardrail:** ส่ง `done`/`awaiting_approval`/`rejected` = ValueError ก่อนยิง HTTP
- **`services/ceo_sync.py`** — inbox (queued + ทีม R&D + ยังไม่ถูกดึง) · pull (project +
  breakdown + PATCH `in_progress`) · report (สรุป markdown → `qc_review`)
  · orchestrator **ไม่ถูกแก้แม้แต่บรรทัดเดียว** (เจตนาเดียวกับ Team Mode)
- **Endpoints:** `GET /api/projects/:id` · `GET /api/ceo/status|inbox` · `POST /api/ceo/pull` ·
  `POST /api/ceo/report/:id` · `/run` เพิ่ม `ceo_report` · `/health` เพิ่ม `ceo_enabled`
- **Schema:** `projects.ceo_task_id` unique — migration `e5a91c73b204` (apply กับ DB จริงแล้ว
  ข้อมูลครบ 3 projects / 21 tasks)
- **UI:** กล่อง "📥 งานจากเลขา" บน Portfolio (ซ่อนเองถ้าปิดการเชื่อม) + ป้าย/ปุ่ม
  "📤 ส่งผลกลับเลขา" บนหน้าบอร์ด · เวลาจาก d_CEO (UTC) แปลงเป็น Asia/Bangkok ตอนแสดง
- **เอกสาร:** `docs/INTEGRATION_CEO.md` (contract + §7 สิ่งที่ต้องขอจาก d_CEO) · API.md §1.1, §16-19 ·
  DATABASE.md · SYSTEM_DOCUMENTATION.md §5-7/§18 · runbook §4.1 · AGENTS.md
- **ตรวจกับ d_CEO ตัวจริง:** `/api/ceo/status` → `online:true`, resolve ทีม R&D ได้
  (`4406dde7-…`), `waiting: 0` — ยืนยันว่าถูกต้อง เพราะคิว queued 9 งานเป็นของ QC&KM 4 /
  ไม่ระบุทีม 4 / Marketing 1 **ไม่มีของ R&D**
- pytest 60 → **79 tests** ผ่านหมด · ruff clean · `npm run build` ผ่าน

### Phase 0 — จัดบ้านให้พร้อมต่อ ecosystem (2026-08-02)

- **commit งานค้าง ~1 เดือน** (`9cd76d6`) — debt #3/#5/#7 + หน้า `/deployments` + ruff
  ที่ค้างใน working tree ตั้งแต่ 2026-07-07 (สำรอง DB ก่อนตาม WORKING_RULES Rule 3)
- **ย้ายพอร์ต 8000 → 8400 ทุกจุด** (runbook, API.md, ARCHITECTURE, SECURITY, backend/README,
  `api.ts` fallback, `.env.local` + example) + จดตารางพอร์ตของ ecosystem ไว้กันชนซ้ำ
- **AGENTS.md เป็นต้นฉบับกติกา** ตามมติผู้ใช้ — ย้ายเนื้อหาจริงจาก CLAUDE.md เข้ามาครบ
  พร้อมเพิ่ม §3.1 ตำแหน่งใน ecosystem + ตารางพอร์ต · `CLAUDE.md`/`GEMINI.md` เหลือเป็น pointer
  (แก้ลิงก์ `WORKING_RULES.md` ที่เคยชี้ไฟล์ที่ไม่มีอยู่ → ชี้ `_CANON`)
- **README.md** เขียนใหม่เป็นของ DEP-PM (เดิมเป็น README ของ Project Starter Kit ที่หลงมา)
- **`docs/PROJECT_OVERVIEW.md` + `docs/RISK_REGISTER.md`** เติมของจริง (เดิมเป็นเทมเพลตเปล่า)
  — risk register รวม 14 ข้อ active + 6 ข้อที่ปิดแล้ว + security/performance checklist ตามสถานะจริง
- `.gitignore`: เพิ่ม `BackUp/` (สำเนามีข้อมูลจริง ห้ามขึ้น remote)

### ก่อนหน้า

- 2026-07-07: เคลียร์ debt #3 (reviewer fail-safe) / #5 (depends_on integrity) / #7 (token tracking)
  + หน้า Deployments + ruff — 48 → **60 tests**
- 2026-07-06: UAT กับของจริง (PM Agent 16 tasks, escalation ครบวงจร, deploy dispatch → GitHub Actions)
- Sprint 1-4 ครบ: Foundation → State Machine/Orchestrator/Bus → Kanban/Portfolio/Message Log →
  Deploy pipeline/Team Mode/PostgreSQL-ready (รายละเอียดใน `CHANGELOG.md`)

## Files Changed (2026-08-02)

**Phase 1**
- **ใหม่:** `backend/app/integrations/{__init__,ceo_client}.py`, `backend/app/services/ceo_sync.py`,
  `backend/app/api/ceo.py`, `backend/alembic/versions/e5a91c73b204_add_project_ceo_task_id.py`,
  `backend/tests/test_ceo_integration.py`, `frontend/src/components/CeoInbox.tsx`,
  `docs/INTEGRATION_CEO.md`
- **แก้:** `backend/app/{config,main}.py`, `app/models/project.py`, `app/schemas/project.py`,
  `app/api/{__init__,projects}.py`, `backend/.env.example`, `backend/tests/{conftest,test_projects}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/page.tsx`,
  `frontend/src/app/projects/[id]/page.tsx`, `docs/{API,DATABASE,SYSTEM_DOCUMENTATION,runbook}.md`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`

**Phase 0**
- **แก้:** `AGENTS.md` (เขียนใหม่ทั้งไฟล์), `CLAUDE.md` + `GEMINI.md` (เหลือ pointer), `README.md`,
  `.gitignore`, `docs/{PROJECT_OVERVIEW,RISK_REGISTER,API,runbook,ARCHITECTURE,SECURITY}.md`,
  `backend/README.md`, `frontend/src/lib/api.ts`, `frontend/.env.local{,.example}`
- คอมมิต `9cd76d6` = งานค้างของ 2026-07-07 ทั้งชุด (35 ไฟล์) · `5f43fa3` = Phase 0
- **สำรอง:** `BackUp/Phase0Cleanup_20260802_224442/` + `BackUp/Phase1CeoIntegration_20260802_230717/`
  (gitignored)

## Current State

- **pytest 79/79 ผ่าน · ruff clean · `npm run build` ผ่าน**
- ยืนยันด้วยการรันจริง: DEP-PM `:8400` กับ d_CEO `:8000` รันคู่กันได้ ·
  `/api/ceo/status` → `online:true` + resolve ทีม R&D ได้
- DB จริง migrate ถึง head `e5a91c73b204` แล้ว (3 projects / 21 tasks ครบ)
- git: main สะอาด · **ยังไม่ push** (ล้ำ origin อยู่ 4 commits รวม `902dbcb` ของ 25 ก.ค.)

## Next Tasks

1. **ทดสอบ Phase 1 กับงานจริง** — ต้องมีคนสั่งงานผ่าน Jarvis แล้วมอบให้ทีม
   **Research & Development** (ตอนนี้คิว d_CEO ไม่มีงานของทีมนี้เลย) → กดดึง → รัน → ดูว่า
   สถานะขยับเป็น `qc_review` พร้อม output ที่ฝั่ง d_CEO
   *(หมายเหตุ: สร้าง task ทดสอบใน d_CEO = เขียนข้อมูลจริงของผู้ใช้ — รอคำสั่งก่อน)*
2. **Phase 2 — `/run` เป็น background job (~1 วัน)** — 202 + `run_id` + lock ต่อโปรเจกต์ (409) +
   `GET /:id/run` progress · **จำเป็นก่อนใช้งานจริงเป็นประจำ** เพราะ 1 task ใช้เวลาระดับนาที
   และตอนนี้ `/run` block ทั้ง request
3. **ขอจากฝั่ง d_CEO** (ดู `docs/INTEGRATION_CEO.md` §7): ยืนยัน contract + ออก
   `INTEGRATION_DEPPM.md` · แก้เอกสารที่ยังเขียนว่า "merge DEP-PM เข้า Solo_CEO"
   (`d_Jarvis\docs\VISION.md` §5, `d_CEO\project_plan_solo_ceo.md` §9.1) — **ห้ามแก้ข้ามรีโป**
4. **Phase 3 — ปิด UAT/ความปลอดภัยที่ค้าง:** callback shared-secret · test suite บน PostgreSQL
   (DoD ADR-01) · Team Mode กับ OPENAI/GEMINI keys จริง
5. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` — ควรทำพร้อมทั้ง ecosystem

## Known Issues

- **CI callback `PATCH /api/deployments/:id` ยังไม่มี auth** — ห้าม expose พอร์ตสาธารณะ (Risk #1)
- **`/run` synchronous + ไม่ thread-safe ต่อโปรเจกต์** — ห้ามยิงซ้อนโปรเจกต์เดียวกัน (Risk #3)
- OpenAI/Gemini executors ยังไม่เคยรันกับ service จริง → token accounting 2 provider นี้ยังไม่ verify
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอ — พฤติกรรมถูกต้อง
  แต่ต้องเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียน UAT ใน runbook §7)
- test suite ยังไม่เคยรันบน PostgreSQL (DoD ของ ADR-01 ยังไม่ปิด)
- uvicorn `--reload` บน Windows บางครั้งไม่จับไฟล์ที่แก้ — endpoint ใหม่ 404/405 ให้ restart

## Decisions Made (2026-08-02)

1. **DEP-PM ไม่ยุบรวมกับ Solo_CEO** — เป็น **Team Lead R&D** ปลายสาย Vinit→Jarvis→d_CEO→DEP-PM
   เอกสาร "merge" ในรีโปอื่นถือว่าล้าสมัย · กติกา "ไม่ทำระบบ task ซ้อน" ยึดด้วย 1 task = 1 project
1.1 **รับงานแบบกดปุ่มเอง (manual pull) ก่อน** ไม่ทำ poller อัตโนมัติ — เห็นพฤติกรรมจริงก่อน
   และตรงหลัก "ยืนยันก่อนทำ" ของ ecosystem (เปลี่ยนเป็นอัตโนมัติภายหลังได้ ไม่ต้องแก้ contract)
1.2 **การเชื่อมต่ออยู่ใน `services/` ไม่ใช่ `orchestrator/`** — engine ไม่ถูกแก้เลย
   (เจตนาเดียวกับ Team Mode Sprint 4) · `api/projects.py` เป็นคนเรียกหลัง `/run`
1.3 **`ceo_task_id` เก็บเป็น `VARCHAR(36)` ไม่ใช่ `GUID`** — id ของระบบอื่น เราไม่ตีความรูปแบบ
   ถ้า d_CEO เปลี่ยนรูปแบบ id เราไม่พัง
2. **AGENTS.md เป็น single source of truth** ของกติกา AI agent · CLAUDE.md/GEMINI.md เป็น pointer
   (ตรงกับ convention ของ d_Jarvis / d_CEO / d_InnoHub)
3. **พอร์ต DEP-PM = 8400** ถาวร — เอกสารทุกไฟล์อัปเดตแล้ว ห้ามย้ายกลับ 8000
4. **การเชื่อมกับ d_CEO ใช้รูปแบบ consumer** — DEP-PM poll/patch เอง **ไม่ขอให้ d_CEO แก้โค้ด**
   (ตรวจแล้วว่า API ปัจจุบันของเขาพอครบ: `GET /teams`, `GET /tasks`, `PATCH /tasks/{id}`)
5. **สำรองก่อนแตะทุกครั้งตาม `_CANON\WORKING_RULES.md`** — โฟลเดอร์ `BackUp/` ถูก gitignore

## Questions for the User

1. **push 4 commits ขึ้น GitHub เลยไหม** (ยังไม่เคย push งานตั้งแต่ 6 ก.ค.)
2. **สร้าง task ทดสอบใน d_CEO ให้ทีม R&D ได้ไหม** เพื่อปิดวงจร Phase 1 ให้ครบ —
   เป็นการเขียนข้อมูลจริงในระบบเลขา จึงยังไม่ทำเอง
3. Phase 2 (`/run` async) ต่อเลยไหม — จำเป็นก่อนใช้งานประจำ
4. PostgreSQL / OPENAI+GEMINI keys — อันไหนพร้อมก่อน (กระทบลำดับ Phase 3)
