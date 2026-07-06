# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-06 | สถานะโดยรวม: **MVP ครบ 4 สปรินต์ (โค้ด) — เหลือ UAT 3 ข้อที่รอ
> ทรัพยากรภายนอกจากผู้ใช้ (API keys, GitHub repo, PostgreSQL)**

## Completed Work

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

- pytest 48/48 | ทุกอย่างรันบน SQLite + stub/fallback ครบวงจร
- **โค้ด MVP ครบตามแผน 4 สปรินต์** — ที่เหลือเป็นการเปิดใช้กับของจริง (ดู UAT ค้าง)
- git: e512771 → c1cef14 → e3d323a → 986c092 — Sprint 4 รอ commit นี้

## Next Tasks (= UAT ที่ค้าง — รอทรัพยากรจากผู้ใช้)

1. **`ANTHROPIC_API_KEY`** → ทดสอบ PM breakdown + Solo Mode จริง (+ ทบทวน reviewer auto-approve)
2. **GitHub repo ทดสอบ + `GITHUB_TOKEN`** → วาง workflow template → deploy จริง end-to-end
3. **PostgreSQL** (Docker หรือ managed) → `DATABASE_URL` → รัน test suite เต็มบน PG (DoD ADR-01)
4. **`OPENAI_API_KEY` + `GEMINI_API_KEY`** → ทดสอบ Team Mode จริง
5. หลัง UAT ผ่าน: security gate ใน `docs/SECURITY.md` ก่อน deploy สาธารณะ (auth, HTTPS,
   callback secret, rate limit)

## Known Issues

- CI callback (`PATCH /api/deployments/:id`) ยังไม่มี auth — ห้าม expose backend สาธารณะ
  (อยู่ใน security gate)
- Executors ของจริง (Claude/OpenAI/Gemini) + GitHub dispatch ยังไม่เคยรันกับ service จริง
- `/run` synchronous + ไม่ thread-safe ต่อโปรเจกต์ (technical debt #1 ใน SYSTEM_DOCUMENTATION §22)
- Frontend ยังไม่มีหน้า deployments แยก (portfolio แสดง last_deployment แล้ว — พอสำหรับ MVP)

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
