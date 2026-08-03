# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-08-03 | สถานะโดยรวม: **Phase 0 + 1 + 2 เสร็จ · UAT รอบใหม่ผ่านกลไก
> แต่ QC ของเลขาปฏิเสธผลงาน**
> — `/run` ไม่ block ผู้เรียกแล้ว (202 + `run_id`) · **งานถัดไปคือคุณภาพของสิ่งที่ส่งออก:
> ส่งผลงานให้ task ที่ depend อยู่ + แนบตัวชิ้นงานในรายงาน** (Next Tasks #1-2)

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (สำรอง DB ล่าสุด `BackUp/Phase0Cleanup_20260802_224442/`
  · Phase 2 ไม่แตะ schema จึงสำรองเฉพาะไฟล์โค้ด: `BackUp/Phase2AsyncRun_20260803_091552/`)
- **พอร์ตของ DEP-PM = 8500** — `uvicorn app.main:app --reload --port 8500`
  · ทะเบียนพอร์ต: `8000` d_CEO API · `8100` d_OCR · `8200` d_STT · `8300` d_InnoHub ·
  `8400` **d_Jarvis web** · `8500` DEP-PM — สองตัวแรกและ 8400 รันค้างผ่าน Task Scheduler **ห้ามหยุด**
  · ⚠️ เมื่อเช้าเคยตั้งเป็น 8400 ผิด (ชน Jarvis web) — แก้แล้วตอนปิดงาน ดู CHANGELOG
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO (`ohho2518/d_DEP-PM_Platform`)
- โปรเจกต์ในระบบ: "Demo: Booking API" (4 done), "d_ACC" (17 backlog), "Deploy UAT",
  + งานทดสอบจากเลขา 2 ตัว (`a07f1fb2` ของ 2 ส.ค., `7ffa2d4f` ของ 3 ส.ค. — เก็บไว้เป็นหลักฐาน UAT)
- DB migrate เป็น head `e5a91c73b204` แล้ว · servers ไม่ได้รันค้างไว้ (สตาร์ตเองตาม runbook)

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

### Phase 2 — `/run` เป็นงานเบื้องหลัง (2026-08-03)

- **`services/runs.py` (ใหม่) — Run Manager:** ทะเบียนรอบรันในหน่วยความจำ + **lock ต่อโปรเจกต์**
  · `start_run` สตาร์ต daemon thread แล้วคืน `RunRecord` ทันที · `RunStatus` = running/succeeded/failed
  · เก็บประวัติล่าสุด 50 รอบ · **ไม่ใช่ job queue** (ไม่มี retry/priority/worker ข้ามโปรเซส)
- **API:** `POST /:id/run` → **202 + `run_id`** (วัดจริง ~10 ms) · ยิงซ้อนโปรเจกต์เดิม → **409**
  · endpoint ใหม่ `GET /:id/run[?run_id=]` → `status/total/processed/counts/outcomes/ceo_report/error`
- **engine แตะน้อยที่สุด:** เพิ่ม `on_outcome` callback (เรียกหลัง commit ของแต่ละ task) +
  `planned_task_count` — engine **ไม่รู้ว่าตัวเองถูกรันใน thread** (เจตนาเดียวกับ Team Mode/Phase 1)
- **session ของงานเบื้องหลัง:** `get_session_factory` เป็น dependency ใหม่ (1 รอบรัน = 1 session)
  — ใช้ session ของ request ไม่ได้เพราะถูกปิดพร้อม response
- **UI:** ปุ่ม Run ตอบทันที · progress ใช้ตัวเลขจริงจาก backend · **ปิดแท็บ/รีเฟรชได้ งานไม่หยุด**
  (ถาม `GET /run` ตอน mount) · 409 → สลับไปแสดงรอบที่ค้างแทน error ดิบ
- **รายงานกลับ d_CEO** ย้ายไปท้ายรอบรันเบื้องหลัง — ปลายทางล่มไม่ทำให้รอบรัน `failed`
- pytest 82 → **90** · ruff clean · `npm run build` ผ่าน
- **smoke test กับ uvicorn จริง** (DB ชั่วคราวใน temp, ไม่แตะ `dep_pm.db`, ไม่มี key = fallback):
  20 tasks รันเบื้องหลังจบครบ `done` · `POST /run` = 202 ใน 7-14 ms · ยิงซ้อน = **409 จริง** ·
  `GET /run` ระหว่างรันเห็น `19/20` · เขียนลง SQLite ไฟล์จากเธรดเบื้องหลังได้ไม่มี lock error

### UAT Phase 2 กับงานจริงจาก d_CEO (2026-08-03) — กลไกผ่าน แต่ **QC ปฏิเสธผลงาน**

งานทดสอบ d_CEO `80dd3ff9` ("เขียนคู่มือสั้น 1 หน้า") → ทีม R&D → DEP-PM project `7ffa2d4f`

**สิ่งที่พิสูจน์ว่าใช้ได้จริง**

| จุด | ผล |
|---|---|
| สร้าง task ไทยผ่าน HTTP | ข้อความตรงตัวต่อตัว 356 ตัวอักษร ไม่มี `?` (ตรวจที่ปลายทาง) |
| pull + PM Agent จริง | 6 tasks กราฟพึ่งพา 3 ชั้น · แจ้ง d_CEO `in_progress` สำเร็จ |
| **`POST /run`** | **202 ใน 10.6 ms** (งานรูปเดียวกันเมื่อวาน block 297 วิ) |
| **ยิงซ้อนขณะรันจริง** | **409** พร้อม `run_id` ที่ค้างอยู่ |
| รอบรันเบื้องหลัง | **507 วินาที** · `succeeded` · 6/6 (done 5 · escalated 1) · error `None` |
| progress ระหว่างรัน | เดินจริง 0→1→2→…→6 ทุกช่วง poll |
| รายงานกลับอัตโนมัติ | `reported: true` `status_sent: qc_review` — token 29,514 in / 33,850 out |

**QC ของ d_CEO ตอบกลับ `rejected`** — เหตุผลที่เขาให้เป็นข้อบกพร่องจริงของฝั่งเรา 2 ข้อ:

1. **รายงานส่งแต่ "สรุปสถานะ task" ไม่ส่งตัวชิ้นงาน** — QC เขียนตรง ๆ ว่า "ไม่มี artifact
   ให้ตรวจ = ไม่ผ่านตามกฎด่านตรวจ" และเสนอเข้า SOP ว่า *ผลงานที่ส่ง QC ต้องแนบตัวชิ้นงานจริง*
   → `ceo_sync.build_report` ต้องแนบผลงาน (result payload) ไม่ใช่แค่ชื่อ task + จำนวน
2. **orchestrator ไม่ส่งผลงานของ dependency ให้ task ที่ depend อยู่** — agent ของ task
   "รวมและจัดรูปแบบเอกสาร" เขียนไว้เองว่า *"ในบทสนทนานี้ไม่มีเนื้อหาต้นฉบับของ T2, T3, T4
   แนบมาด้วย"* จึงผลิตได้แค่ **โครงเอกสารที่มี `[[placeholder]]`** → task รีวิวจับได้ ปฏิเสธ
   2 รอบ → escalated · **นี่คือ root cause ของปัญหา "งานรวมเล่มถูกปฏิเสธ" ที่จดไว้เมื่อวาน**
   (ไม่ใช่เพราะ reviewer เข้มเกินไป — agent ไม่มี input ให้ทำงานจริง ๆ)

> บทเรียนซ้ำรอยเดิม: unit test + smoke test บอกได้แค่ "กลไกเดิน" · **คุณภาพงานที่ส่งออก
> ต้องมีคนนอก (QC ของเลขา) ตรวจถึงจะเห็น**

### UAT วงจรเต็มกับ d_CEO ตัวจริง + fix ที่พบ (2026-08-02)

**เดินครบวงจรจริงแล้ว** — task ทดสอบ `d89c03a8` (ทีม R&D) → DEP-PM ดึง → PM Agent จริง
แตกเป็น **6 tasks พร้อมกราฟพึ่งพา 4 ชั้น** → รัน orchestrator จริง **297 วินาที**
→ ผล: done 4 · escalated 1 · ค้าง 1 → **รายงานกลับเข้า `qc_review` ที่ d_CEO พร้อม output
1,040 ตัวอักษร** · token รวม 19,150 in / 18,512 out

**บั๊กที่ UAT จับได้ (แก้แล้ว):** เกณฑ์ readiness นับ `planned` เป็น "ยังเดินอยู่" แต่ task ที่
dependency ติด escalated ค้าง `planned` ถาวร → เงื่อนไขไม่มีวันเป็นจริง → **เคสที่ต้องรีบ
บอกคนที่สุดกลับเงียบหาย** และ d_CEO ค้าง `in_progress` ตลอด
→ เปลี่ยนเกณฑ์ให้ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง + รายงานเพิ่มหัวข้อ
"งานที่ค้างเพราะรองานข้างบน" และแถบเตือนว่ายังไม่จบสมบูรณ์ (pytest 79 → **82**)

> บทเรียน: unit test ครอบแค่ "จบครบ" กับ "ยังเดินอยู่" — ไม่มีเคส "ตันถาวร" เพราะคิดไม่ถึง
> **การรันกับงานจริงคือสิ่งเดียวที่จับได้**

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
- **ย้ายพอร์ต 8000 → 8400 ทุกจุด** *(ภายหลังแก้เป็น 8500 — ดูหมายเหตุท้ายวัน)* (runbook, API.md, ARCHITECTURE, SECURITY, backend/README,
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

## Files Changed

**Phase 2 (2026-08-03)**
- **ใหม่:** `backend/app/services/runs.py`, `backend/tests/test_runs.py`
- **แก้:** `backend/app/api/{projects,ceo}.py`, `backend/app/constants.py` (+`RunStatus`),
  `backend/app/db/session.py` (+`get_session_factory`), `backend/app/orchestrator/engine.py`
  (+`on_outcome`, `planned_task_count`), `backend/tests/{conftest,test_orchestrator,test_portfolio,test_ceo_integration}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/projects/[id]/page.tsx`,
  `docs/{API,SYSTEM_DOCUMENTATION,ARCHITECTURE,INTEGRATION_CEO,RISK_REGISTER,runbook}.md`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`
- **สำรอง:** `BackUp/Phase2AsyncRun_20260803_091552/` (gitignored)

**Phase 1 (2026-08-02)**
- **ใหม่:** `backend/app/integrations/{__init__,ceo_client}.py`, `backend/app/services/ceo_sync.py`,
  `backend/app/api/ceo.py`, `backend/alembic/versions/e5a91c73b204_add_project_ceo_task_id.py`,
  `backend/tests/test_ceo_integration.py`, `frontend/src/components/CeoInbox.tsx`,
  `docs/INTEGRATION_CEO.md`
- **แก้:** `backend/app/{config,main}.py`, `app/models/project.py`, `app/schemas/project.py`,
  `app/api/{__init__,projects}.py`, `backend/.env.example`, `backend/tests/{conftest,test_projects}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/page.tsx`,
  `frontend/src/app/projects/[id]/page.tsx`, `docs/{API,DATABASE,SYSTEM_DOCUMENTATION,runbook}.md`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`

**Phase 0 (2026-08-02)**
- **แก้:** `AGENTS.md` (เขียนใหม่ทั้งไฟล์), `CLAUDE.md` + `GEMINI.md` (เหลือ pointer), `README.md`,
  `.gitignore`, `docs/{PROJECT_OVERVIEW,RISK_REGISTER,API,runbook,ARCHITECTURE,SECURITY}.md`,
  `backend/README.md`, `frontend/src/lib/api.ts`, `frontend/.env.local{,.example}`
- คอมมิต `9cd76d6` = งานค้างของ 2026-07-07 ทั้งชุด (35 ไฟล์) · `5f43fa3` = Phase 0
- **สำรอง:** `BackUp/Phase0Cleanup_20260802_224442/` + `BackUp/Phase1CeoIntegration_20260802_230717/`
  (gitignored)

## Current State

- **pytest 90/90 ผ่าน · ruff clean · `npm run build` ผ่าน**
- **วงจร d_CEO ↔ DEP-PM ใช้งานได้จริงแล้ว** (ยืนยันด้วยงานจริง ไม่ใช่แค่ mock)
- **`/run` เป็นงานเบื้องหลังแล้ว** (202 + `run_id` · lock ต่อโปรเจกต์ · `GET /:id/run`)
  — ปิด Risk #3 ที่เคยบล็อกการใช้งานประจำ
- DB จริง migrate ถึง head `e5a91c73b204` (4 projects / 27 tasks — รวมของทดสอบ)
  · **Phase 2 ไม่มี migration** (ทะเบียนรอบรันอยู่ในหน่วยความจำ ไม่แตะ schema)
- **ของทดสอบที่ยังค้างในระบบ:** d_CEO task `d89c03a8` (สถานะ `qc_review` รอ QC ของเขาตรวจ)
  + DEP-PM project `a07f1fb2` — จะเก็บไว้เป็นตัวอย่างหรือลบก็ได้
- git: main สะอาด (Phase 2 = commit `f8848f0`) · **push ขึ้น GitHub แล้ว 2026-08-03**
  (`ohho2518/d_DEP-PM_Platform` — ยกงานที่ค้างมาตั้งแต่ 25 ก.ค. ขึ้นครบ 7 commits ในรอบนี้)

## Next Tasks

1. **ส่งผลงานจริงให้ task ที่ depend อยู่ (Phase 3a)** ← สำคัญสุด · root cause ของงาน
   "รวมเล่ม" ที่ถูกปฏิเสธทุกครั้ง — ตอนนี้ agent ได้แค่ title/spec ของตัวเอง ไม่ได้เห็น
   ผลงานของ dependency · แก้ที่จุดประกอบ context ก่อนเรียก executor (ต้องคุมขนาด: ตัด/
   ย่อเมื่อยาวเกิน `MAX_TOKENS_PER_TASK`) — **ไม่ต้องแตะ state machine**
2. **รายงานกลับเลขาต้องแนบตัวชิ้นงาน (Phase 3a)** — `ceo_sync.build_report` เพิ่มผลงานจริง
   ของ task ปลายทาง (result payload ล่าสุด) · ต้องตัดสินใจ: แนบทุก task หรือเฉพาะ task
   ที่ไม่มีใคร depend ต่อ (= deliverable ตัวจริง) และเพดานความยาวเท่าไร
3. **ทบทวนกติกา escalation กับงานเอกสาร** — หลังแก้ข้อ 1 แล้วค่อยประเมินซ้ำ
   ว่ายังต้องปรับ prompt reviewer อีกไหม (บทเรียนเดิมใน runbook §7)
4. **ขอจากฝั่ง d_CEO** (ดู `docs/INTEGRATION_CEO.md` §7): ยืนยัน contract + ออก
   `INTEGRATION_DEPPM.md` · แก้เอกสารที่ยังเขียนว่า "merge DEP-PM เข้า Solo_CEO"
   (`d_Jarvis\docs\VISION.md` §5, `d_CEO\project_plan_solo_ceo.md` §9.1) — **ห้ามแก้ข้ามรีโป**
5. **Phase 3b — ปิด UAT/ความปลอดภัยที่ค้าง:** callback shared-secret · test suite บน PostgreSQL
   (DoD ADR-01) · Team Mode กับ OPENAI/GEMINI keys จริง
6. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` — ควรทำพร้อมทั้ง ecosystem

## Known Issues

- **CI callback `PATCH /api/deployments/:id` ยังไม่มี auth** — ห้าม expose พอร์ตสาธารณะ (Risk #1)
- **ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียว** — restart uvicorn ระหว่างรอบรัน = งานหยุด
  และประวัติรอบรันหาย (`GET /run` → 404) **ผลงานที่ commit แล้วไม่หาย** กด Run ใหม่ทำต่อได้
  · ยังไม่มีปุ่ม "ยกเลิกรอบรัน"
- 🔴 **task ที่ depend อยู่ไม่ได้รับผลงานของ dependency** — agent เห็นแค่ title/spec ของตัวเอง
  → งานประเภท "รวมเนื้อหา/ต่อยอดจากงานก่อนหน้า" ทำจริงไม่ได้ ผลิตได้แค่โครงว่าง แล้วถูก
  reviewer ปฏิเสธจนเข้า escalated (ยืนยันจาก UAT 3 ส.ค. — agent บอกเองว่าไม่มีเนื้อหาต้นฉบับ)
- 🔴 **รายงานที่ส่งเลขาไม่มีตัวชิ้นงาน** มีแต่สรุปสถานะ task → **QC ปฏิเสธ** (`rejected` 3 ส.ค.)
  · ผลงานจริงอยู่ครบใน `agent_messages` แล้ว แค่ไม่ถูกหยิบมาใส่รายงาน
- OpenAI/Gemini executors ยังไม่เคยรันกับ service จริง → token accounting 2 provider นี้ยังไม่ verify
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอ — พฤติกรรมถูกต้อง
  แต่ต้องเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียน UAT ใน runbook §7)
- test suite ยังไม่เคยรันบน PostgreSQL (DoD ของ ADR-01 ยังไม่ปิด)
- uvicorn `--reload` บน Windows บางครั้งไม่จับไฟล์ที่แก้ — endpoint ใหม่ 404/405 ให้ restart

## Decisions Made

### 2026-08-03 (Phase 2)

6. **ใช้ thread ในโปรเซสเดียว ไม่เอา Celery/Redis** — single-user, งานผูกกับ SQLite ไฟล์เดียว
   การเพิ่ม broker คือ dependency + ของที่ต้องดูแลโดยยังไม่มีปัญหาที่มันแก้ · ทางหนีเขียนไว้แล้ว:
   เปลี่ยนแค่ `services/runs.py` ไฟล์เดียว (endpoint กับ engine ไม่รู้จักวิธีรัน)
6.1 **ทะเบียนรอบรันอยู่ในหน่วยความจำ ไม่ทำตาราง `runs` ใน DB** — รอบรันเป็นสถานะชั่วคราว
   ของโปรเซส ส่วน**ผลงานจริงอยู่ใน `tasks`/`audit_log`/`agent_messages` อยู่แล้ว**
   (เจตนาเดียวกับ bus ADR-03) · ไม่มี migration = ไม่มีความเสี่ยงกับ `dep_pm.db`
6.2 **lock เป็นราย project ไม่ใช่ global** — คนละโปรเจกต์รันพร้อมกันได้ · ซ้อนโปรเจกต์เดิม = 409
   (ตรงกับข้อจำกัดจริงของ engine: ไม่ thread-safe **ต่อโปรเจกต์**)
6.3 **`POST /run` เปลี่ยน response shape (breaking)** ไม่ทำ endpoint ใหม่แยก — ผู้ใช้ contract นี้
   มีแค่ frontend ของเราเอง (แก้ในคอมมิตเดียวกันตามกติกา §9.1.6) การมี 2 เส้นทางถาวรแพงกว่า
6.4 **d_CEO ล่มตอนรายงาน ≠ รอบรันล้ม** — งานพัฒนาเสร็จจริงไปแล้ว บันทึกเหตุไว้ใน
   `ceo_report.detail` แล้วให้ผู้ใช้กดส่งซ้ำ (`status: "failed"` สงวนไว้ให้ engine พังจริง ๆ)

### 2026-08-02 (Phase 0-1)

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
3. **พอร์ต DEP-PM = 8500** ถาวร (แก้จาก 8400 ที่ชน d_Jarvis web) — เอกสารทุกไฟล์อัปเดตแล้ว
   · กติกาใหม่: **ตรวจพอร์ตด้วย `Get-NetTCPConnection` ก่อนจองเสมอ อย่าเชื่อเอกสารอย่างเดียว**
4. **การเชื่อมกับ d_CEO ใช้รูปแบบ consumer** — DEP-PM poll/patch เอง **ไม่ขอให้ d_CEO แก้โค้ด**
   (ตรวจแล้วว่า API ปัจจุบันของเขาพอครบ: `GET /teams`, `GET /tasks`, `PATCH /tasks/{id}`)
5. **สำรองก่อนแตะทุกครั้งตาม `_CANON\WORKING_RULES.md`** — โฟลเดอร์ `BackUp/` ถูก gitignore

## Questions for the User

1. **สร้าง task ทดสอบใน d_CEO ให้ทีม R&D ได้ไหม** เพื่อทดสอบวงจรเต็มรอบใหม่บน `/run` แบบ async —
   เป็นการเขียนข้อมูลจริงในระบบเลขา จึงยังไม่ทำเอง
2. อยากได้ **ปุ่มยกเลิกรอบรัน** ไหม (ตอนนี้ยกเลิกไม่ได้ ต้องรอจบหรือ restart backend)
3. PostgreSQL / OPENAI+GEMINI keys — อันไหนพร้อมก่อน (กระทบลำดับ Phase 3)
