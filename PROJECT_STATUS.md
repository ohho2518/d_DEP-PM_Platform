# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-06 (ปิดวัน) | สถานะโดยรวม: **ระบบใช้งานจริงได้แล้ว** — MVP ครบ +
> UAT หลักผ่าน + UI ธีม ai-dev-team พร้อม Agent Office และ progress bar
> ผู้ใช้ทดลองใช้ผ่าน UI แล้ววันนี้

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (มีบันทึกใน memory แล้ว)
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO
  (`ohho2518/d_DEP-PM_Platform`) — deploy dispatch ใช้ได้จริง
- โปรเจกต์เดโมในระบบ: "Demo: Booking API" (4 tasks) — ผู้ใช้กด Run Agents เล่นแล้ว
- Servers ปิดแล้วตอนจบวัน — เปิดใหม่: ดู CLAUDE.md §Run Dev Server

## Completed Work

### UAT กับของจริง (2026-07-06 ค่ำ)
- ANTHROPIC_API_KEY + GITHUB_TOKEN/REPO ใช้งานจริง; push repo ขึ้น
  `github.com/ohho2518/d_DEP-PM_Platform` (main) พร้อม workflow receiver
- UAT ผ่าน: PM breakdown จริง (16 tasks) / escalation→takeover→done + happy path /
  deploy dispatch → GitHub Actions รันจริง (Build & Deploy ผ่าน; callback รอ tunnel)
- Fix 2 bugs ที่พบจาก UAT: token cap (4096→16000 + empty-text marker),
  test hermeticity บน Windows (conftest monkeypatch Settings)


### Sprint 4 — Deploy Pipeline + Team Mode + PostgreSQL-ready (2026-07-06)
- Deploy pipeline: dispatcher (`repository_dispatch` + stub mode), endpoints
  POST/GET/PATCH `/api/deployments`, Manual Approval Gate (production = มือเท่านั้น),
  CI callback → task done→deployed
- Auto-deploy staging เมื่อ task done (config `AUTO_DEPLOY_ENABLED`)
- Team Mode: `AGENT_MODE=team` → TeamExecutor (Dev=OpenAI, SR=Gemini, PM/Reviewer=Claude)
  + fallback chain ต่อ role — orchestrator ไม่แก้ (DoD ผ่าน)
- PostgreSQL-ready (psycopg + ขั้นตอนใน runbook) | ตัดสินใจข้าม Redis
- Handover: `docs/runbook.md` + `docs/github-workflow-example.yml`
- pytest 48/48

### ก่อนหน้า (2026-07-06 ทั้งหมด)
- Engineering docs set 6 ไฟล์ตาม MASTER PROMPT | Sprint 3: Kanban + Portfolio + Message Log
- Sprint 2: State Machine + Orchestrator + Bus | Sprint 1: Foundation + PM Agent + Stub scan

## Files Changed (Sprint 4)

- ใหม่: `app/services/deploy.py`, `app/api/deployments.py`, `app/agents/providers.py`,
  `tests/test_deployments.py`, `tests/test_team_mode.py`,
  `docs/runbook.md`, `docs/github-workflow-example.yml`
- แก้: `app/config.py` (+8 env), `app/agents/runtime.py` (TeamExecutor + get_executor),
  `app/orchestrator/engine.py` (auto-deploy hook), `app/api/__init__.py`, `app/main.py`,
  `requirements.txt` (openai, google-genai, psycopg), `.env.example`
- เอกสารอัปเดต: API.md (endpoints 13-15), SYSTEM_DOCUMENTATION.md, DATABASE.md, SECURITY.md

## Current State

- pytest 48/48 (hermetic — ไม่แตะ .env/network) | โค้ด MVP ครบ 4 สปรินต์ + UAT หลักผ่านกับของจริง
- `backend/.env` มี ANTHROPIC + GITHUB keys แล้ว (gitignored) — `/health` → `agent_enabled: true`
- git: main push ขึ้น `github.com/ohho2518/d_DEP-PM_Platform` แล้ว (ล่าสุด d5fddaa)

## Next Tasks (optional ที่เหลือ)

1. **Callback ครบวงจร**: tunnel (cloudflared) + secret `DEP_PM_API_URL` ใน repo → deployment
   สถานะ success อัตโนมัติ + task done→deployed (ขั้นตอน runbook §3)
2. **PostgreSQL** (Docker หรือ managed) → `DATABASE_URL` → รัน test suite เต็มบน PG (DoD ADR-01)
3. **`OPENAI_API_KEY` + `GEMINI_API_KEY`** → ทดสอบ Team Mode จริง (ยืนยันรุ่น model ใน .env ด้วย)
4. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` (auth, HTTPS, callback secret, rate limit)

## Known Issues

- CI callback (`PATCH /api/deployments/:id`) ยังไม่มี auth — ห้าม expose backend สาธารณะ
  (อยู่ใน security gate)
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอใน MVP —
  พฤติกรรมถูกต้อง แต่ควรเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียนใน runbook §7)
- OpenAI/Gemini executors ยังไม่เคยรันกับ service จริง (รอ keys)
- `/run` synchronous + ไม่ thread-safe ต่อโปรเจกต์ (technical debt #1 ใน SYSTEM_DOCUMENTATION §22)

## Decisions Made (Sprint 4)

1. **ข้าม Redis** — ADR-03 "ถ้าทัน"; ไม่มีเหตุ cross-process ใน single-user; upgrade path คงเดิม
2. **Manual Approval Gate = enforce ที่ API layer** — auto path hardcode staging;
   production มาจาก POST มือเท่านั้น (+ แนะนำ GitHub environment protection อีกชั้นใน template)
3. **Deployment status callback แยกจาก task State Machine** — deployments มี flow เล็กของตัวเอง
   (queued→running→success|failed) แล้วสะท้อนเข้า task ผ่าน transition ปกติ (done→deployed)
4. **Team Mode fallback chain ต่อ role** — key ขาดตัวไหน role นั้นไหลไป Claude → deterministic
   (ระบบไม่ล้มกลางงาน)

## Questions for the User

1. เตรียมได้ก่อน: ANTHROPIC key / GitHub repo+token / PostgreSQL / OpenAI+Gemini keys — อันไหน?
2. Model defaults ใน .env.example (`gpt-5.2`, `gemini-3-pro`) — ยืนยันรุ่นที่จะใช้จริงตอน UAT
3. ต้องการหน้า Deployments แยกใน UI ไหม หรือ portfolio พอ (ตอนนี้พอ — เพิ่มได้ถ้าต้องการ)
