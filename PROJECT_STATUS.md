# PROJECT_STATUS.md — DEP-PM Platform

> อัปเดตล่าสุด: 2026-07-06 | สถานะโดยรวม: **Sprint 3 (Kanban Dashboard) เสร็จ — รอเริ่ม Sprint 4**

## Completed Work

### Engineering Documentation Set (2026-07-06 — หลัง Sprint 3)
- สร้าง `docs/` ชุดเต็มตาม MASTER PROMPT: `ARCHITECTURE.md`, `SYSTEM_DOCUMENTATION.md`,
  `API.md`, `DATABASE.md`, `SECURITY.md`, `AI_AGENT_GUIDE.md`
- **กติกาใหม่:** อัปเดตเอกสารชุดนี้ท้ายทุก sprint ตามตาราง Documentation Rules ใน
  `docs/AI_AGENT_GUIDE.md` (เฉพาะส่วนที่เปลี่ยน ไม่ regenerate ทั้งหมด)

### Sprint 3 — Kanban Dashboard + Message Log + Portfolio (2026-07-06)
- Backend: `GET /api/portfolio` (counts ต่อสถานะ, agents, deploy ล่าสุด)
- Frontend: Next.js 16.2.10 + TypeScript + Tailwind (`frontend/`)
- หน้า Portfolio, New Project (STEP 1-4 ครบ), Kanban Board (8 คอลัมน์ + ปุ่ม transition
  + Run Agents), Message Log Viewer, polling ทุก 4 วิ (ADR-04)
- E2E verified กับ backend จริงบน production build

### Sprint 2 — Orchestration Engine (2026-07-06)
- State Machine (409 on invalid), Routing Rules, Solo Mode Runtime, Message Bus, Escalation

### Sprint 1 — Backend Foundation (2026-07-06)
- FastAPI + SQLAlchemy + Alembic, ORM 6 ตาราง, PM Agent breakdown, Metadata Stub

## Files Changed (Sprint 3)

- Backend ใหม่: `backend/app/api/portfolio.py`, `backend/tests/test_portfolio.py`
- Backend แก้: `app/api/__init__.py`, `app/main.py` (wire router)
- Frontend ใหม่ทั้งโฟลเดอร์: `frontend/` — สำคัญ:
  - `src/lib/{types,api,usePolling}.ts` — types ตรง backend schema, API client, polling hook
  - `src/app/page.tsx` — Portfolio
  - `src/app/projects/new/page.tsx` — New Project flow
  - `src/app/projects/[id]/page.tsx` — Kanban + Task detail + Message Log
  - `src/app/layout.tsx` — nav shell
  - `.env.local.example` — `NEXT_PUBLIC_API_URL`

## Current State

- **รัน dev ครบระบบ:** backend `uvicorn app.main:app` (พอร์ต 8000) + frontend `npm run dev`
  (พอร์ต 3000, ตั้ง `.env.local` ชี้ backend)
- pytest 34/34 ผ่าน; `npm run build` ผ่าน (TypeScript + 4 routes)
- ผู้ใช้ทำครบวงจรผ่าน UI ได้: สร้างโปรเจกต์ → ยืนยัน scope → Run Agents → เห็น task เลื่อน
  ไป done + ดูบทสนทนา agent ย้อนหลัง (DoD Sprint 3)
- ยังไม่มี `ANTHROPIC_API_KEY` — agent วิ่ง fallback path (UI ระบุ source ชัด)
- git: Sprint 1 (`e512771`), Sprint 2 (`c1cef14`) — Sprint 3 รอ commit

## Next Tasks (= Sprint 4, ดู docs/DEVELOPMENT_PLAN.md §6)

1. **Automated Deploy** (Blueprint §12): task `done` → trigger GitHub Actions ผ่าน
   `repository_dispatch` (staging auto, production มี Manual Gate) + `POST/GET /api/deployments`
2. **ย้าย DB → PostgreSQL** (ADR-01) + รัน test suite เดิมบน PostgreSQL
3. เพิ่ม Redis (message transport + pub/sub ถ้าทัน — ADR-03/04)
4. **Team Mode**: mapping role → provider (Codex Dev = OpenAI, Gemini SR = Google) —
   ต้องมี `OPENAI_API_KEY` + `GEMINI_API_KEY`
5. Security ขั้นต่ำ (Blueprint §15) + UAT + `docs/runbook.md`

## Known Issues

- Frontend เป็น Next.js **16.2.10** ไม่ใช่ 15 ตามแผนเดิม (create-next-app@latest) — ทำงานปกติ,
  หมายเหตุ: dynamic route `params` เป็น Promise (ใช้ `React.use()`)
- `/run` synchronous — UI ปุ่ม "Run Agents" ค้างจนจบ (แสดงสถานะ "กำลังทำงาน…")
- ปุ่ม transition บน UI mirror state machine ฝั่ง frontend (`lib/types.ts`) — ถ้าแก้ backend
  ต้องแก้ `ALLOWED_TRANSITIONS` ใน frontend ให้ตรงกัน
- Deployments ยังเป็น null ทุกโปรเจกต์จนกว่า Sprint 4

## Decisions Made (เพิ่มจาก Sprint 3)

1. **ไม่ใช้ UI library หนัก** (shadcn/ui ฯลฯ) — Tailwind ล้วน ลด dependency ตามหลัก CLAUDE.md
2. **เปลี่ยนสถานะด้วยปุ่ม ไม่ใช้ drag-and-drop** — แผนระบุ "ลาก/ปุ่ม" เลือกปุ่มเพื่อเลี่ยง
   dnd library + robust กว่าบน state machine (ปุ่มแสดงเฉพาะ transition ที่ valid)
3. **Polling 4 วิ + หยุดเมื่อแท็บไม่ visible** (ADR-04) — SSE เลื่อนไปพิจารณา Sprint 4
4. รับ Next 16 แทน 15 (เวอร์ชัน stable ล่าสุดจาก create-next-app)

## Questions for the User

1. Commit Sprint 3 แล้ว — เริ่ม Sprint 4 (Deploy Pipeline + PostgreSQL + Team Mode) เลยไหม?
2. Sprint 4 ต้องการ: GitHub repo ทดสอบ deploy (`repository_dispatch`), PostgreSQL instance
   (local Docker ได้ไหม?), และ API keys (OpenAI + Gemini) สำหรับ Team Mode — เตรียมอันไหนได้บ้าง?
3. อยากลองเปิด UI ดูก่อนไหม? (`uvicorn` + `npm run dev` — ขั้นตอนใน backend/README.md + ด้านล่าง)
