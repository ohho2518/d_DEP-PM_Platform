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
uvicorn app.main:app --reload     # http://127.0.0.1:8000 (docs: /docs)

# Frontend (terminal 2)
cd frontend
npm run dev                       # http://localhost:3000 (ครั้งแรก: npm install + cp .env.local.example .env.local)
```

ตรวจสุขภาพ: `curl http://127.0.0.1:8000/health` → `{"status":"ok","agent_enabled":...}`

## 2. เปิดความสามารถแต่ละส่วน (env ใน `backend/.env`)

| ต้องการ | ตั้งค่า | ตรวจว่าเปิดแล้ว |
|---------|--------|-----------------|
| PM Agent + Solo Mode จริง | `ANTHROPIC_API_KEY` | `/health` → `agent_enabled: true` |
| Team Mode (dev=OpenAI, SR=Gemini) | `AGENT_MODE=team` + `OPENAI_API_KEY` + `GEMINI_API_KEY` (ขาด key ไหน role นั้น fallback → Claude → deterministic) | breakdown/run แล้วดู payload ใน message log |
| Deploy dispatch จริง | `GITHUB_TOKEN` (fine-grained PAT, contents:write) + `GITHUB_REPO=owner/repo` | `POST /api/deployments` → `dispatched: true` |
| Auto-deploy staging เมื่อ task done | `AUTO_DEPLOY_ENABLED=true` | run orchestrator → deployment record เกิด |

**เปลี่ยน env แล้วต้อง restart uvicorn** (Settings cache ต่อ process)

## 3. Deploy pipeline — ติดตั้งฝั่ง repo เป้าหมาย

1. copy `docs/github-workflow-example.yml` → `.github/workflows/dep-pm-deploy.yml` ใน repo เป้าหมาย
2. ตั้ง secret `DEP_PM_API_URL` ใน repo (URL backend ที่ runner เข้าถึงได้ — dev local ใช้ tunnel เช่น cloudflared)
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
# 4) DoD: รัน test suite เดิมทั้งชุดบน PG:
DATABASE_URL=postgresql+psycopg://... pytest
```
driver (`psycopg[binary]`) อยู่ใน requirements แล้ว; โค้ด portable ตาม ADR-01 (GUID/JSON decorators)

## 5. อาการผิดปกติที่พบบ่อย

| อาการ | สาเหตุ/วิธีแก้ |
|-------|----------------|
| UI ขึ้น "เชื่อมต่อ backend ไม่ได้" | uvicorn ไม่ได้รัน หรือ `NEXT_PUBLIC_API_URL` ผิด (แก้แล้ว restart `npm run dev`) |
| breakdown ได้ task เดียว source=fallback | ไม่มี `ANTHROPIC_API_KEY` หรือ key ใช้ไม่ได้ — เช็ค `/health` |
| PATCH task ตอบ 409 | ผิดลำดับ State Machine — ดูลำดับใน `docs/SYSTEM_DOCUMENTATION.md` §9 |
| `POST /deployments` ตอบ `dispatched: false` + stub | ยังไม่ตั้ง GITHUB_TOKEN/GITHUB_REPO (ตั้งใจ), หรือ github ตอบ error — ดู `detail` |
| deployment ค้าง `running` | workflow ฝั่ง repo ไม่ได้ callback — เช็ค Actions log + secret `DEP_PM_API_URL`; แก้มือ: `PATCH /api/deployments/:id {"status": "failed"}` |
| task ค้าง `in_progress` (orchestrator ตายกลางทาง) | `PATCH /api/tasks/:id {"status": "review"}` แล้วให้คน review หรือ rerun |
| Run Agents ไม่ทำอะไร (processed: 0) | ไม่มี task `planned` — ยัง confirm scope ไม่ได้ทำ หรือ dependency ค้าง (ดู task escalated) |

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

## 8. Security notes (ก่อน expose ออกนอกเครื่อง)
ดู `docs/SECURITY.md` — สำคัญสุด: **ยังไม่มี authentication** ห้าม expose พอร์ต 8000
สู่เครือข่ายสาธารณะจนกว่าจะทำ auth (security gate ใน SECURITY.md)
