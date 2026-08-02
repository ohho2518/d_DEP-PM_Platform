# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-07 | สถานะโดยรวม: **ระบบใช้งานจริงได้แล้ว** — MVP ครบ + UAT หลักผ่าน
> + เคลียร์ technical debt #3/#5/#7 + หน้า Deployments + ruff (เหลือ debt #1 `/run` sync
> และ callback auth — จะทำคู่กันตามที่คุยไว้)

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (มีบันทึกใน memory แล้ว)
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO
  (`ohho2518/d_DEP-PM_Platform`) — deploy dispatch ใช้ได้จริง
- โปรเจกต์ในระบบ: "Demo: Booking API" (4 done), "d_ACC" (17 backlog), "Deploy UAT"
- Servers **รันอยู่** (เปิด 2026-07-07 เช้า): uvicorn :8000 + next dev :3000
- DB migrate เป็น head `c7d4e2a9b1f3` แล้ว (เพิ่ม token columns)

## Completed Work

### เคลียร์ technical debt (2026-07-07)

- **debt #3** Reviewer parse-fail: retry 1 → reject → revision/escalation (เดิม auto-approve)
  — helper กลาง `runtime._review_with_retry` ใช้ทั้ง Solo/Team
- **debt #7** Token tracking: `tasks.tokens_input/tokens_output` (migration `c7d4e2a9b1f3`)
  สะสมทุก LLM call ทุก provider (`LLMReply` ใน providers.py) + โชว์ใน task detail
- **debt #5** depends_on: create validate (400) + `DELETE /api/tasks/:id` (409 ถ้ามีตัวอ้าง;
  ลบแล้ว messages CASCADE / deployments SET NULL ที่ API layer — SQLite ไม่ enforce FK)
- **หน้า Deployments** `/deployments` + `GET /api/deployments` (list, newest-first,
  filter project_id, เติม project_name/task_title)
- **ruff** ตั้งแล้ว (`backend/ruff.toml`) — โค้ดเดิมแก้ครบ, suite สะอาด
- pytest **60/60** | `npm run build` ผ่าน | ทดสอบ endpoint ใหม่กับ server จริงแล้ว

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

## Files Changed (2026-07-07)

- ใหม่: `backend/ruff.toml`, `alembic/versions/c7d4e2a9b1f3_add_task_token_usage.py`,
  `frontend/src/app/deployments/page.tsx`
- แก้ backend: `app/agents/providers.py` (LLMReply + usage ทุก provider),
  `app/agents/runtime.py` (review retry/reject + `_add_usage` + prompt helpers),
  `app/models/task.py` + `app/schemas/task.py` (token columns),
  `app/api/tasks.py` (DELETE), `app/api/projects.py` (validate depends_on),
  `app/api/deployments.py` (GET list), `requirements.txt` (+ruff)
  — และไฟล์จำนวนมากโดน ruff --fix (import order เท่านั้น)
- แก้ frontend: `lib/types.ts` (+tokens, Deployment types), `lib/api.ts` (+listDeployments),
  `app/layout.tsx` (nav), `app/projects/[id]/page.tsx` (แสดง tokens)
- เทสต์: `test_tasks.py` (+6), `test_team_mode.py` (+4), `test_deployments.py` (+2)
- เอกสาร: API.md (8.1, 13.1, tokens), DATABASE.md, SYSTEM_DOCUMENTATION.md §22, CLAUDE.md

## Current State

- pytest 60/60 + ruff clean | โค้ด MVP ครบ + debt #3/#5/#7 ปิดแล้ว
- `backend/.env` มี ANTHROPIC + GITHUB keys แล้ว (gitignored) — `/health` → `agent_enabled: true`
- git: ยังไม่ commit งานวันนี้ | remote `github.com/ohho2518/d_DEP-PM_Platform`

## Next Tasks

1. **แก้ `/run` synchronous (debt #1) + callback auth (shared secret)** — คู่ที่ผู้ใช้เลือกไว้
   ให้ทำถัดไป (2026-07-07)
2. **Callback ครบวงจร**: tunnel (cloudflared) + secret `DEP_PM_API_URL` ใน repo (runbook §3)
3. **PostgreSQL** (Docker หรือ managed) → `DATABASE_URL` → รัน test suite เต็มบน PG (DoD ADR-01)
4. **`OPENAI_API_KEY` + `GEMINI_API_KEY`** → ทดสอบ Team Mode จริง (ยืนยันรุ่น model ใน .env ด้วย)
5. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` (auth, HTTPS, rate limit)

## Known Issues

- CI callback (`PATCH /api/deployments/:id`) ยังไม่มี auth — ห้าม expose backend สาธารณะ
  (จะแก้ใน Next Task #1)
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอใน MVP —
  พฤติกรรมถูกต้อง แต่ควรเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียนใน runbook §7)
- OpenAI/Gemini executors ยังไม่เคยรันกับ service จริง (รอ keys) — token usage ของ
  สอง provider นี้จึงยังไม่ถูก verify กับ response จริงด้วย
- `/run` synchronous + ไม่ thread-safe ต่อโปรเจกต์ (technical debt #1 ใน SYSTEM_DOCUMENTATION §22)
- uvicorn `--reload` บน Windows บางครั้งไม่จับไฟล์ที่แก้ (เจอวันนี้) — ถ้า endpoint ใหม่ 405/404
  ให้ restart backend

## Decisions Made (2026-07-07)

1. **Unparseable review = reject ไม่ใช่ approve** — ความเสี่ยง "งานไม่ถูกตรวจหลุดเป็น done"
   แย่กว่า revision รอบเพิ่ม; loop ถูก bound ด้วย MAX_REVISIONS → escalate ให้คนอยู่แล้ว
2. **Token usage เก็บเป็น counter สะสมบน tasks** (ไม่แยกตาราง per-call) — พอสำหรับคุมงบ
   ต่อ task; รายละเอียด per-call มีใน agent_messages อยู่แล้วถ้าต้องการย้อนดู
3. **depends_on integrity บังคับที่ API layer** (สอดคล้อง ADR-01 ที่เลือก JSON array) —
   ไม่เพิ่ม join table
4. **ruff: ignore E501 + B008** — ข้อความไทย/prompt ยาวเป็นปกติ; `Depends()` เป็น idiom FastAPI

## Decisions Made (Sprint 4)

1. **ข้าม Redis** — ADR-03 "ถ้าทัน"; ไม่มีเหตุ cross-process ใน single-user; upgrade path คงเดิม
2. **Manual Approval Gate = enforce ที่ API layer** — auto path hardcode staging;
   production มาจาก POST มือเท่านั้น (+ แนะนำ GitHub environment protection อีกชั้นใน template)
3. **Deployment status callback แยกจาก task State Machine** — deployments มี flow เล็กของตัวเอง
   (queued→running→success|failed) แล้วสะท้อนเข้า task ผ่าน transition ปกติ (done→deployed)
4. **Team Mode fallback chain ต่อ role** — key ขาดตัวไหน role นั้นไหลไป Claude → deterministic
   (ระบบไม่ล้มกลางงาน)

## Questions for the User

1. เตรียมได้ก่อน: PostgreSQL / OpenAI+Gemini keys — อันไหน? (ANTHROPIC + GitHub มีแล้ว)
2. Model defaults ใน .env.example (`gpt-5.2`, `gemini-3-pro`) — ยืนยันรุ่นที่จะใช้จริงตอน UAT
3. ~~หน้า Deployments~~ — ทำแล้ว (2026-07-07)
