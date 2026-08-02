# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-08-02 | สถานะโดยรวม: **MVP ใช้งานได้ + Phase 0 (จัดบ้าน) เสร็จ**
> — งานถัดไปคือ **ต่อสายรับงานจาก d_CEO** (บทบาท Team Lead R&D)

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

- **แก้:** `AGENTS.md` (เขียนใหม่ทั้งไฟล์), `CLAUDE.md` + `GEMINI.md` (เหลือ pointer), `README.md`,
  `.gitignore`, `PROJECT_STATUS.md`, `docs/{PROJECT_OVERVIEW,RISK_REGISTER,API,runbook,ARCHITECTURE,SECURITY}.md`,
  `backend/README.md`, `frontend/src/lib/api.ts`, `frontend/.env.local{,.example}`
- **ใหม่:** `BackUp/Phase0Cleanup_20260802_224442/` (สำเนา DB ก่อนแตะ — gitignored)
- คอมมิตก่อนหน้าในวันเดียวกัน `9cd76d6` = งานค้างของ 2026-07-07 ทั้งชุด (35 ไฟล์)

## Current State

- **pytest 60/60 ผ่าน · ruff clean · `npm run build` ผ่าน** (ตรวจหลังแก้พอร์ตแล้ว)
- ยืนยันด้วยการรันจริง: DEP-PM `:8400/health` → `{"status":"ok","agent_enabled":true}`
  และ d_CEO `:8000/health` ยังตอบปกติพร้อมกัน
- git: main สะอาด (มี 1 commit ของงานค้าง + Phase 0 รอ commit) · remote `github.com/ohho2518/d_DEP-PM_Platform`
  **ยังไม่ push**

## Next Tasks

1. **Phase 1 — ต่อสายรับงานจาก d_CEO (~2-3 วัน)** ← งานหลักถัดไป
   - migration: `projects.ceo_task_id` (nullable, unique) + schema + `types.ts` คอมมิตเดียวกัน
   - `backend/app/integrations/ceo_client.py` (httpx ไฟล์เดียว + degrade เงียบเมื่อสมองออฟไลน์) + mock test
   - "ดึงงานจากเลขา": `GET /tasks?status=queued` → กรอง `assigned_team_id` = Research & Development
     (resolve จาก `GET /teams` ตอน runtime ห้าม hardcode) → สร้าง project + breakdown → `PATCH` เป็น `in_progress`
   - รายงานกลับ: งานในโปรเจกต์จบครบ → `PATCH /tasks/{id}` เป็น **`qc_review`** + `output` สรุปผล
     **ห้ามส่ง `done` เอง** (มติ Vinit 2026-08-02 เคส d_MOS — ทุกงานต้องผ่าน QC gate)
   - `docs/INTEGRATION_CEO.md` (consumer view) + ขอ ticket/ยืนยันจากฝั่ง d_CEO
2. **Phase 2 — `/run` เป็น background job (~1 วัน)** — 202 + `run_id` + lock ต่อโปรเจกต์ (409) +
   `GET /:id/run` progress · จำเป็นเพราะสายบังคับบัญชารอ synchronous ไม่ไหว (d_CEO วัดจริง 1 task = 192 วิ)
3. **Phase 3 — ปิด UAT/ความปลอดภัยที่ค้าง:** callback shared-secret · test suite บน PostgreSQL (DoD ADR-01) ·
   Team Mode กับ OPENAI/GEMINI keys จริง
4. **แจ้งรีโปอื่นแก้เอกสารที่ล้าสมัย** (ห้ามแก้ข้ามรีโป): `d_Jarvis\docs\VISION.md` §5 และ
   `d_CEO\project_plan_solo_ceo.md` §9.1 ยังเขียนว่า "merge DEP-PM เข้า Solo_CEO"
5. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` (auth, HTTPS, rate limit) — ควรทำพร้อมทั้ง ecosystem

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
2. **AGENTS.md เป็น single source of truth** ของกติกา AI agent · CLAUDE.md/GEMINI.md เป็น pointer
   (ตรงกับ convention ของ d_Jarvis / d_CEO / d_InnoHub)
3. **พอร์ต DEP-PM = 8400** ถาวร — เอกสารทุกไฟล์อัปเดตแล้ว ห้ามย้ายกลับ 8000
4. **การเชื่อมกับ d_CEO ใช้รูปแบบ consumer** — DEP-PM poll/patch เอง **ไม่ขอให้ d_CEO แก้โค้ด**
   (ตรวจแล้วว่า API ปัจจุบันของเขาพอครบ: `GET /teams`, `GET /tasks`, `PATCH /tasks/{id}`)
5. **สำรองก่อนแตะทุกครั้งตาม `_CANON\WORKING_RULES.md`** — โฟลเดอร์ `BackUp/` ถูก gitignore

## Questions for the User

1. **Phase 1 เริ่มได้เลยไหม** หรืออยากให้ push commit ขึ้น GitHub ก่อน (ตอนนี้ยังไม่ push)
2. งานจาก d_CEO ที่จะให้ DEP-PM รับ — ให้ **ดึงเองอัตโนมัติ (poller)** หรือ **กดปุ่มดึง (manual pull)**
   ก่อนในเฟสแรก? (แนะนำ manual pull — ปลอดภัยกว่าและเห็นพฤติกรรมจริงก่อนปล่อยอัตโนมัติ)
3. PostgreSQL / OPENAI+GEMINI keys — อันไหนพร้อมก่อน (กระทบลำดับ Phase 3)
