# RUNBOOK — DEP-PM Platform

> Handover / Operations guide (Sprint 4 deliverable) | อัปเดต: 2026-07-06
> สำหรับ: ผู้ดูแลระบบ (Vinit) และ AI session ที่ต้อง operate ระบบ

---

## 1. รันระบบ (dev)

```bash
# Backend (terminal 1)
cd backend
.venv\Scripts\activate            # ครั้งแรก: python -m venv .venv && pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8500   # http://127.0.0.1:8500 (docs: /docs)

# Frontend (terminal 2)
cd frontend
npm run dev                       # http://localhost:3000 (ครั้งแรก: npm install + cp .env.local.example .env.local)
```

ตรวจสุขภาพ: `curl http://127.0.0.1:8500/health` → `{"status":"ok","agent_enabled":...}`

> **⚠️ ห้ามใช้พอร์ต 8000 และ 8400** — ทั้งคู่รันค้างตลอดผ่าน Task Scheduler (d_CEO / d_Jarvis web)
>
> 📌 **ทะเบียนพอร์ตฉบับจริงอยู่ที่ `D:\Dev_Proj_KM\d_InnoHub\_CANON\SERVICE_PORTS.md`**
> (ของทั้ง eco + กติกาก่อนจองพอร์ต + เกณฑ์ bind) — ไม่ก๊อบตารางมาไว้ที่นี่อีกแล้ว

## 2. เปิดความสามารถแต่ละส่วน (env ใน `backend/.env`)

| ต้องการ | ตั้งค่า | ตรวจว่าเปิดแล้ว |
|---------|--------|-----------------|
| PM Agent + Solo Mode จริง | `ANTHROPIC_API_KEY` | `/health` → `agent_enabled: true` |
| Team Mode (dev=OpenAI, SR=Gemini) | `AGENT_MODE=team` + `OPENAI_API_KEY` + `GEMINI_API_KEY` (ขาด key ไหน role นั้น fallback → Claude → deterministic) | breakdown/run แล้วดู payload ใน message log |
| Deploy dispatch จริง | `GITHUB_TOKEN` (fine-grained PAT, contents:write) + `GITHUB_REPO=owner/repo` | `POST /api/deployments` → `dispatched: true` |
| Auto-deploy staging เมื่อ task done | `AUTO_DEPLOY_ENABLED=true` | run orchestrator → deployment record เกิด |
| **รับงานจากเลขา (d_CEO)** | `CEO_API_BASE=http://127.0.0.1:8000` (+`CEO_TEAM_NAME` ถ้าเปลี่ยนชื่อทีม) | `curl 127.0.0.1:8500/api/ceo/status` → `online: true` + `team_id` ไม่ใช่ null |

**เปลี่ยน env แล้วต้อง restart uvicorn** (Settings cache ต่อ process)

## 3. Deploy pipeline — ติดตั้งฝั่ง repo เป้าหมาย

1. copy `docs/github-workflow-example.yml` → `.github/workflows/dep-pm-deploy.yml` ใน repo เป้าหมาย
2. ตั้ง secret `DEP_PM_API_URL` ใน repo (URL backend ที่ runner เข้าถึงได้ — dev local ใช้ tunnel เช่น cloudflared)
2.1 ตั้ง `DEPLOY_CALLBACK_SECRET` ใน `backend/.env` **และ** secret `DEP_PM_CALLBACK_SECRET`
   ในรีโปเป้าหมายให้ตรงกัน (สร้างค่า: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   · ไม่ตั้ง = callback ไม่ถูกตรวจ (โหมด dev) **🔴 ต้องตั้งก่อน expose พอร์ตออกนอกเครื่อง**
3. (production gate ชั้น GitHub) ตั้ง environment `production` + required reviewers ใน repo settings
4. ทดสอบ: `POST /api/deployments {"project_id": "...", "environment": "staging"}` → ดู Actions tab

**กติกา Manual Gate:** เส้นทาง auto (orchestrator) ยิงได้เฉพาะ **staging**; `production` ต้องสั่งผ่าน `POST /api/deployments` โดยมนุษย์เท่านั้น

## 4. ย้าย PostgreSQL (เมื่อ infra พร้อม)

```bash
# 1) มี PostgreSQL (เช่น Docker):
docker run -d --name dep-pm-pg -e POSTGRES_PASSWORD=<pass> -e POSTGRES_DB=dep_pm -p 5432:5432 postgres:17
# 2) ชี้ DATABASE_URL ใน .env:
#    DATABASE_URL=postgresql+psycopg://postgres:<pass>@localhost:5432/dep_pm
# 3) สร้าง schema + seed:
alembic upgrade head
# 4) DoD: รัน test suite เดิมทั้งชุดบน PG (ใช้ TEST_DATABASE_URL ไม่ใช่ DATABASE_URL):
TEST_DATABASE_URL=postgresql+psycopg://postgres:<pass>@127.0.0.1:5432/dep_pm_pytest pytest
```
driver (`psycopg[binary]`) อยู่ใน requirements แล้ว; โค้ด portable ตาม ADR-01 (GUID/JSON decorators)

> ✅ **ทำจริงแล้ว 2026-08-03 บน PostgreSQL 17.10** — migration ครบ 4 ตัว + **pytest 107/107 ผ่าน**
> (ชุดเดียวกับที่รันบน SQLite) · `tasks.id`/`project_id` เป็น native `uuid`, `depends_on` เป็น `json`
>
> 🐛 **บั๊กที่ DoD นี้จับได้:** migration `b2f1c0d3e4a5` (seed agent) ประกาศ `id` เป็น `sa.String`
> ทำให้ `alembic upgrade head` **ตายทั้งชุดบน PostgreSQL** ("column id is of type uuid but
> expression is of type character varying") — แก้เป็น `GUID` แล้ว ผลบน SQLite เหมือนเดิมทุกประการ
>
> `TEST_DATABASE_URL` ว่าง = SQLite ในหน่วยความจำเหมือนเดิม (ไม่ต้องมี service ตอนพัฒนาปกติ)

## 4.1 รับงานจากเลขา (d_CEO) — ใช้งานประจำวัน

1. ต้องมี **d_CEO รันอยู่ที่ `:8000`** (Task Scheduler "d_CEO API" — ปกติรันค้างอยู่แล้ว)
2. งานต้องถูกมอบให้ทีม **Research & Development** ตอนสร้างใน d_CEO
   (`POST /tasks` ต้องมี `assigned_team_id` ของทีมนี้ ไม่งั้นเราไม่เห็นในคิว)
3. หน้า Portfolio (`/`) จะมีกล่อง **📥 งานจากเลขา** โผล่เอง → กด "ดึงงานทั้งหมด" หรือ "รับงานนี้"
4. ระบบสร้างโปรเจกต์ + ให้ PM Agent แตกงาน + แจ้ง d_CEO เป็น `in_progress` ให้อัตโนมัติ
5. **ผู้ใช้ยืนยัน scope + กด Run Agents เอง** (ระบบไม่รันให้อัตโนมัติ)
   · ตั้งแต่ Phase 2 การรันเป็น**งานเบื้องหลัง** — ปุ่มตอบกลับทันที แถบความคืบหน้าเดินเอง
   **ปิดแท็บ/รีเฟรชหน้าได้ งานไม่หยุด** (เปิดหน้าบอร์ดใหม่แล้วเห็นความคืบหน้าต่อ)
   · **ห้ามปิด uvicorn ระหว่างรอบรัน** — งานอยู่ในโปรเซสนั้น (task ที่จบแล้วยังอยู่ใน DB)
   · อยากหยุดกลางทาง กด **⏹ หยุดรอบรัน** — หยุดหลัง task ปัจจุบันจบ (ไม่ตัดกลางคัน)
     แล้วกด Run ใหม่ทำต่อได้ · รอบที่ถูกยกเลิก **ไม่ถูกรายงานกลับเลขา**
6. งานจบครบ → รายงานกลับเข้า **QC gate** ของ d_CEO ให้อัตโนมัติ (สถานะ `qc_review`)
   · รอบอัตโนมัติล้มเหลว → กดปุ่ม **📤 ส่งผลกลับเลขา** บนหน้าบอร์ดซ้ำได้

> 🔴 **ระบบเราปิดงานฝั่ง d_CEO เองไม่ได้** — ส่งได้แค่ `in_progress`/`qc_review`
> QC ของ d_CEO เป็นคนเคาะว่า `done` / `awaiting_approval` / `rejected` (มติ Vinit 2026-08-02)

## 5. อาการผิดปกติที่พบบ่อย

| อาการ | สาเหตุ/วิธีแก้ |
|-------|----------------|
| UI ขึ้น "เชื่อมต่อ backend ไม่ได้" | uvicorn ไม่ได้รัน หรือ `NEXT_PUBLIC_API_URL` ผิด (แก้แล้ว restart `npm run dev`) |
| breakdown ได้ task เดียว source=fallback | ไม่มี `ANTHROPIC_API_KEY` หรือ key ใช้ไม่ได้ — เช็ค `/health` |
| PATCH task ตอบ 409 | ผิดลำดับ State Machine — ดูลำดับใน `docs/SYSTEM_DOCUMENTATION.md` §9 |
| `POST /deployments` ตอบ `dispatched: false` + stub | ยังไม่ตั้ง GITHUB_TOKEN/GITHUB_REPO (ตั้งใจ), หรือ github ตอบ error — ดู `detail` |
| callback ตอบ 401 | secret ไม่ตรง — เทียบ `DEPLOY_CALLBACK_SECRET` ใน `backend/.env` กับ `DEP_PM_CALLBACK_SECRET` ในรีโปเป้าหมาย (restart uvicorn หลังแก้ `.env`) |
| deployment ค้าง `running` | workflow ฝั่ง repo ไม่ได้ callback — เช็ค Actions log + secret `DEP_PM_API_URL`; แก้มือ: `PATCH /api/deployments/:id {"status": "failed"}` |
| task ค้าง `in_progress` (orchestrator ตายกลางทาง) | `PATCH /api/tasks/:id {"status": "review"}` แล้วให้คน review หรือ rerun |
| Run Agents ไม่ทำอะไร (processed: 0) | ไม่มี task `planned` — ยัง confirm scope ไม่ได้ทำ หรือ dependency ค้าง (ดู task escalated) |
| กด Run แล้วขึ้น "กำลังรันอยู่แล้ว" (409) | มีรอบรันของโปรเจกต์นี้ค้างอยู่ (อาจเปิดไว้อีกแท็บ) — หน้าจะสลับไปแสดงรอบนั้นให้เอง · เช็กเองได้ที่ `GET /api/projects/:id/run` |
| แถบความคืบหน้าหายหลัง restart uvicorn | ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซส (`GET /run` → 404) — **ผลงานที่ commit แล้วยังอยู่ครบ** กด Run ใหม่ทำต่อเฉพาะ `planned` ที่เหลือ |
| รอบรันขึ้น `failed` | ดูเหตุใน `error` ของ `GET /api/projects/:id/run` + traceback ใน log ของ uvicorn — lock ถูกปลดแล้ว กดรันใหม่ได้เลย |
| กล่อง "งานจากเลขา" ไม่โผล่ | ยังไม่ตั้ง `CEO_API_BASE` (restart uvicorn หลังแก้ `.env`) |
| "🧠 สมองออฟไลน์" | d_CEO ไม่ได้รัน — เช็ก `curl 127.0.0.1:8000/health` และ Task Scheduler "d_CEO API" |
| งานรอ 0 ทั้งที่เพิ่งสั่งงาน | งานถูก assign ให้ทีมอื่น — ต้องเป็นทีม `CEO_TEAM_NAME` (Research & Development) |
| ดึงงานแล้ว `acknowledged: false` | สร้างโปรเจกต์สำเร็จแต่ PATCH กลับ d_CEO ล้ม — ไม่ต้องดึงใหม่ (จะซ้ำไม่ได้อยู่แล้ว) กดส่งผลกลับทีหลังได้ |

## 6. ข้อมูล & การกู้คืน
- **DB (dev):** ไฟล์ `backend/dep_pm.db` — backup = copy ไฟล์; ลบ = เริ่มใหม่ด้วย `alembic upgrade head`
- **Audit trail:** ตาราง `audit_log` (append-only) + `agent_messages` — คำตอบของ "ใครทำอะไรเมื่อไหร่" ทั้งหมด
- **Escalated tasks:** ดูเหตุที่ escalate ใน message ประเภท `question` ของ task นั้น → คนแก้แล้ว PATCH → `in_progress`

## 7. UAT checklist (ผ่านแล้ว = ระบบพร้อมใช้)
- [x] สร้างโปรเจกต์ใหม่ + breakdown + confirm ผ่าน UI
- [x] Run Agents → task ไหลถึง done + บทสนทนาดูย้อนหลังได้
- [x] Brownfield scan (mock) → baseline tasks
- [x] PATCH ผิดลำดับ → 409
- [x] Deployment stub: POST → record + GET สถานะ + PATCH callback → task done→deployed
- [x] **PM Agent จริง** (2026-07-06): requirement ไทย → 16 tasks พร้อม priority/points/deps
- [x] **Solo Mode จริง** (2026-07-06): escalation ครบวงจร (reviewer เข้ม ปฏิเสธ 2 → escalated
      → human takeover → done) + happy path งานเชิงเอกสาร done รอบเดียว
- [x] **Deploy dispatch จริง** (2026-07-06): POST → `dispatched: true` → workflow รันบน
      GitHub Actions, Build & Deploy step ผ่าน (callback fail ตามคาด — ดูหมายเหตุด้านล่าง)
- [ ] Callback ครบวงจร: ต้องมี tunnel (cloudflared) + secret `DEP_PM_API_URL` ใน repo (§3)
- [ ] Solo↔Team Mode กับ key จริง (รอ OPENAI/GEMINI keys)
- [ ] Test suite บน PostgreSQL (รอ infra)

**บทเรียนจาก UAT จริง (2026-07-06):**
1. `claude-sonnet-5` เปิด adaptive thinking default — `MAX_TOKENS_PER_TASK` ต่ำเกิน (4096)
   ทำให้รอบ revision ได้ text ว่าง → ปรับ default เป็น 16000 + มี marker เมื่อ text ว่าง
2. Windows: ตั้ง env var เป็นค่าว่าง = ตัวแปรถูกลบ → tests ต้อง monkeypatch Settings
   (ทำใน conftest แล้ว — suite hermetic ไม่แตะ .env)
3. Reviewer จริงเข้มกว่า fallback มาก — task ที่ acceptance criteria ต้องการ artifact จริง
   (repo, CI รันจริง) จะ escalate เสมอใน MVP เพราะ agent ผลิตได้แค่ข้อความ → เขียน spec
   ให้ deliverable เป็นเอกสาร/โค้ด หรือให้คนรับ task ประเภท infra เอง

**ทบทวน escalation จากข้อมูลจริงทั้งหมดใน `dep_pm.db` (2026-08-03):**

| โปรเจกต์ | ผล | revision เฉลี่ย |
|---|---|---|
| Demo: Booking API | done 4 | 0.00 |
| งานเลขา 2 ส.ค. | done 4 · **escalated 1** · ค้าง 1 | 0.40 |
| งานเลขา 3 ส.ค. รอบ 1 | done 5 · **escalated 1** | 0.67 |
| งานเลขา 3 ส.ค. รอบ 2 (หลัง Phase 3a) | **done 8 · escalated 0** | **0.12** |

รวมงานที่จบแล้ว 23 รายการ · escalated 2 = **8.7%** (เป้า < 10% → ผ่าน)

- **escalation ทั้ง 2 ครั้งในประวัติมีสาเหตุเดียวกัน: task ต้องใช้ผลงานของงานก่อนหน้า
  แต่ไม่ได้รับมา** — reviewer เขียนไว้ตรง ๆ ทั้งสองครั้ง ("มีเพียงข้อความขอข้อมูลเพิ่มเติม
  จาก T2/T3/T4", "ไม่มีเอกสารต้นฉบับให้ตรวจจริง ผู้ทำงานเลือกสร้างเอกสารขึ้นมาเองแล้วรีวิว
  เอกสารที่ตัวเองแต่งขึ้น")
- ⇒ **ข้อสรุปเดิมที่ว่า "reviewer เข้มเกินไป" ผิด** — reviewer ถูกทั้งสองครั้ง ปัญหาอยู่ที่
  input ของ agent · หลังแก้ที่ต้นเหตุ (Phase 3a ส่ง context ทั้งกราฟ) escalation เป็น 0
  และ revision เฉลี่ยลดจาก 0.67 → 0.12 ในโจทย์เดียวกัน
- **ยังไม่ต้องปรับ prompt reviewer** — ให้เก็บข้อมูลอีก 2-3 รอบก่อน ถ้า escalation ยังต่ำ
  ถือว่าปิดประเด็นนี้ได้
- 📌 reviewer จับ "แต่งชิ้นงานขึ้นมาเองทั้งชิ้น" ได้ (เคส 3 ส.ค. รอบ 1) แต่ **จับ "แต่งหลักฐาน
  ประกอบในชิ้นงานที่ดูสมบูรณ์" ไม่ได้** (เคสอ้างชื่อคน/quote/timestamp ในรอบ 2 — QC ของเลขา
  เป็นคนจับ) → เป็นเหตุผลว่าทำไมต้องเติมกติกาห้ามกุหลักฐานที่ persona prompt ไม่ใช่แค่ที่ reviewer

**รอบ 3 (2026-08-03) — วัดผลกติกาห้ามกุหลักฐานกับงานที่ "ล่อให้กุ" โดยตรง:**

โจทย์บังคับให้อ้างข้อมูลจริงที่ระบบนี้ไม่มี (วัน-เวลาทำงานจริง · ชื่อผู้รับผิดชอบ · คำพูดของคนในทีม)

- ✅ **ไม่มีการกุแม้แต่จุดเดียว** — PM แตกงานโดยขึ้นต้น spec ว่า "ต้องการข้อมูลจากคน:" เอง ·
  dev ทั้ง 3 ตัวรายงานตรง ๆ ว่าทำไม่ได้ · ตัวอย่างในตารางติดป้าย `[ตัวอย่างสมมติ]` ครบ
- ✅ **QC ของ d_CEO ยืนยันจากภายนอก:** "ทีมปฏิเสธที่จะแต่งตัวเลข/คำพูดสมมติอย่างถูกต้อง …
  นี่คือพฤติกรรมที่ถูก ไม่ใช่ความบกพร่องของทีม" (verdict `FIX (escalate)` → `awaiting_approval`
  รอ Vinit ตัดสิน — d_CEO task `4eb918bd`)
- 🔴 **แต่เจอบั๊กใหม่ของฝั่งเรา 2 ข้อ ในงานที่ "ติดเพราะไม่มีข้อมูลจากคน" เหมือนกันเป๊ะ:**
  1. reviewer สั่ง revision ว่า *"ยืนยันว่าได้ escalate คำขอข้อมูลไปยังผู้เกี่ยวข้องแล้วจริง"* —
     ซึ่ง agent **ทำไม่ได้** (พิมพ์ข้อความได้อย่างเดียว) รอบถัดมา agent จึงเขียนว่า "ได้ escalate แล้ว"
     แล้ว reviewer ก็จับได้เองว่าไม่มีหลักฐาน → **reviewer เป็นคนบีบให้เกิดการกุเสียเอง**
     · เสียไป 2 รอบ (~15k token) แล้วจบที่ escalated อยู่ดี · งานปลายน้ำ 3 ตัวค้างถาวร
  2. task ที่สถานการณ์เดียวกันอีกตัวกลับถูก **approve เป็น `done`** → รายงานขึ้นว่า "เสร็จ 2"
     ทั้งที่เนื้อในเป็นเอกสารแจ้งว่าทำไม่ได้ (QC จับได้: *"ผลงาน 2 ชิ้นที่ 'เสร็จ' จริง ๆ แล้วเป็น
     เอกสารแจ้งว่าทำไม่ได้เพราะไม่มีข้อมูลต้นทาง"*)
- ⇒ **แก้ด้วย verdict ที่ 3 ของ reviewer: `needs_human`** (ดู SYSTEM_DOCUMENTATION §9) —
  งานที่ติดเพราะขาดข้อมูล/สิทธิ์ที่ agent หาเองไม่ได้ → escalate **ตั้งแต่รีวิวแรก ไม่นับ revision**
  ไม่ approve ว่าเสร็จ · reviewer ถูกห้ามสั่ง revision ที่ agent ทำตามไม่ได้
- ✅ **ตรวจกับโมเดลจริงแล้ว** (project `bc3a43b7`, 1 task): reviewer ตอบ `needs_human: true`
  ตั้งแต่รอบแรก → `escalated` ที่ `revision_count = 0` · เหตุผลในรายงานขึ้นต้นว่า
  "ต้องการข้อมูล/การตัดสินใจจากคน — …" แยกจากเคส "review ไม่ผ่าน 2 ครั้ง" ชัดเจน

## 8. Security notes (ก่อน expose ออกนอกเครื่อง)
ดู `docs/SECURITY.md` — สำคัญสุด: **ยังไม่มี authentication** ห้าม expose พอร์ต 8500
สู่เครือข่ายสาธารณะจนกว่าจะทำ auth (security gate ใน SECURITY.md)
