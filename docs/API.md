# API.md — DEP-PM Platform

> API Documentation (MASTER PROMPT §12) | อัปเดต: 2026-07-06 (หลัง Sprint 4)
> Interactive docs: รัน backend แล้วเปิด `http://127.0.0.1:8000/docs` (OpenAPI อัตโนมัติ)

## ภาพรวม

| หัวข้อ | ค่า |
|--------|-----|
| Base URL (dev) | `http://127.0.0.1:8000` |
| Content-Type | `application/json` ทุก endpoint |
| **Authentication** | **ไม่มี** (single-user MVP — ดู SECURITY.md) |
| Rate limit | ไม่มี (MVP) |
| CORS | อนุญาต origin เดียว: `FRONTEND_ORIGIN` (default `http://localhost:3000`) |
| Error format | FastAPI มาตรฐาน: `{"detail": "..."}` |

### Error codes ที่ใช้ทั่วระบบ
| Code | ความหมายในระบบนี้ |
|------|--------------------|
| 400 | ผิดเงื่อนไข domain (เช่น scan โปรเจกต์ type=new) |
| 404 | ไม่พบ project/task |
| **409** | **ผิด State Machine transition** (เอกลักษณ์ของระบบนี้) |
| 422 | Pydantic validation (เช่น existing ไม่มี repo_url, enum ผิด) |

---

## Endpoints

### 1) `POST /api/projects` — สร้างโปรเจกต์
Request:
```json
{ "name": "dPRO Parking v2", "type": "new" }
```
`type: "existing"` **ต้องมี** `repo_url` (ไม่งั้น 422 — validator ใน `ProjectCreate`)

Response `201`:
```json
{ "id": "2847c80a-…", "name": "dPRO Parking v2", "type": "new",
  "repo_url": null, "status": "planning", "metadata_registry_ref": null,
  "created_at": "2026-07-06T05:00:00Z" }
```
Side effects: audit `project.created`

---

### 2) `GET /api/projects/:id/tasks?limit=50&offset=0` — รายการ task
- `limit` clamp 1..200, `offset` ≥ 0, เรียง `created_at`
Response `200`:
```json
{ "data": [ { "id": "…", "title": "…", "status": "backlog", "priority": "P2",
              "assignee_type": null, "agent_role": null, "depends_on": [],
              "spec": null, "estimate_points": null, "revision_count": 0, "…": "…" } ],
  "pagination": { "total": 1, "limit": 50, "offset": 0 } }
```

---

### 3) `POST /api/projects/:id/tasks` — สร้าง task มือ
Request (บังคับแค่ `title`):
```json
{ "title": "Set up CI", "priority": "P1", "estimate_points": 3,
  "description": "…", "spec": "…", "depends_on": ["<task-uuid>"] }
```
Response `201`: Task (status เริ่ม `backlog` เสมอ) | Side effects: audit `task.created`

---

### 4) `POST /api/projects/:id/breakdown` — PM Agent แตกงาน
Request: `{ "requirement": "อยากได้ระบบจองคิว…" }`

Response `200`:
```json
{ "source": "agent",   // "fallback" เมื่อไม่มี ANTHROPIC_API_KEY หรือ parse fail
  "tasks": [ /* Task[] สถานะ backlog พร้อม depends_on resolve เป็น UUID แล้ว */ ] }
```
Behavior สำคัญ:
- มี key → เรียก Claude (persona PM) → validate JSON → retry 1 ครั้งถ้า parse fail → ถ้ายัง fail ใช้ fallback
- fallback = task เดียวจาก requirement (**ไม่ 500 เด็ดขาด** — graceful degradation)
- Side effects: tasks + audit `task_plan.created` (actor `pm-agent`)

---

### 5) `POST /api/projects/:id/confirm` — ยืนยัน scope (backlog → planned)
Request: `{ "task_ids": [] }` — **ว่าง = ยืนยันทุก backlog task**
Response `200`: TaskList เฉพาะ task ที่เปลี่ยน | ทุกตัวผ่าน `transition()` → audit `task.transition`

---

### 6) `POST /api/projects/:id/scan` — Brownfield scan (**mock — ADR-02**)
เงื่อนไข: โปรเจกต์ต้อง `type: "existing"` ไม่งั้น **400**
Response `200`:
```json
{ "report": { "project_id": "…", "provider": "stub", "is_mock": true,
              "summary": "(mock) Baseline Report จาก StubMetadataProvider …",
              "findings": [ { "category": "tech_debt", "title": "[mock] …",
                              "suggested_priority": "P2", "confidence": 0.5 } ] },
  "created_task_ids": ["…", "…", "…"] }
```
ทุก finding กลายเป็น backlog task | `is_mock: true` + prefix `[mock]` เสมอ (Risk #1)

---

### 7) `POST /api/projects/:id/run` — รัน Solo-Mode Orchestrator
**Synchronous** — ตอบเมื่อทุก task จบ (LLM จริงอาจใช้เวลานาน)
Response `200`:
```json
{ "project_id": "…", "processed": 3, "counts": { "done": 2, "escalated": 1 },
  "outcomes": [ { "task_id": "…", "title": "…", "final_status": "done", "revisions": 1 } ] }
```
- รันเฉพาะ task `planned` ที่ dependency (`depends_on`) เป็น done/deployed ครบ
- `processed: 0` = ไม่มี task ให้รัน (ยังไม่ confirm scope)
- Side effects ต่อ task: routing audit, transitions, ข้อความ bus ≥3 (handoff/result/review_comment)

---

### 8) `PATCH /api/tasks/:id` — อัปเดต task (State Machine enforced)
Request (ทุก field optional): `{ "status": "planned", "assignee_type": "human", "title": "…" }`
- `status` ต้องเป็น transition ที่ถูกต้อง ไม่งั้น **409** `{"detail": "invalid transition: backlog -> done"}`
- Transition ที่อนุญาต: ดู State Machine ใน `SYSTEM_DOCUMENTATION.md` §9
Response `200`: Task | Side effects: audit `task.transition` และ/หรือ `task.updated`

---

### 9) `GET /api/tasks/:id/messages` — บทสนทนา agent ของ task
Response `200`:
```json
{ "data": [ { "id": "…", "from_agent_id": "orchestrator", "to_agent_id": "dev",
              "message_type": "handoff", "payload": { "title": "…", "spec": "…" },
              "created_at": "…" } ] }
```
เรียงเวลา | `to_agent_id: null` = broadcast (เช่น escalation question)

---

### 10) `POST /api/agent-messages` — ส่งข้อความเข้า Message Bus
Request:
```json
{ "project_id": "…", "task_id": "…", "from_agent_id": "pm",
  "to_agent_id": "dev", "message_type": "handoff", "payload": {"note": "เริ่มได้"} }
```
`message_type` ∈ handoff|question|result|review_comment (อื่น → 422)
Response `201`: `{ "id": "…", "created_at": "…" }` | 404 ถ้า project ไม่มีจริง

---

### 11) `GET /api/portfolio` — ภาพรวมทุกโปรเจกต์
Response `200`:
```json
{ "projects": [ { "id": "…", "name": "…", "type": "new", "status": "planning",
                  "task_counts": { "done": 5, "escalated": 1 }, "total_tasks": 6,
                  "last_deployment": null } ],
  "agents": [ { "id": "…0001", "name": "Claude Solo", "role": "pm",
                "mode": "solo", "status": "idle" } ] }
```
`last_deployment` = deployment ล่าสุดของโปรเจกต์ (null ถ้ายังไม่เคย deploy)

---

### 12) `GET /health` — liveness
Response: `{ "status": "ok", "agent_enabled": false }`
`agent_enabled` = มี `ANTHROPIC_API_KEY` จริงหรือไม่ (UI ใช้บอกผู้ใช้ว่าอยู่โหมด fallback)

---

### 13) `POST /api/deployments` — trigger deploy (manual)
Request: `{ "project_id": "…", "task_id": "…"(optional), "environment": "staging|production" }`
- environment อื่น → 400 | **production trigger ได้จาก endpoint นี้เท่านั้น** (Manual Gate — เส้นทาง auto ของ orchestrator ยิงได้แค่ staging)
Response `201`:
```json
{ "id": "…", "status": "running", "environment": "staging", "triggered_by": "manual",
  "dispatched": true, "detail": "repository_dispatch sent", "…": "…" }
```
- ไม่ตั้ง `GITHUB_TOKEN`/`GITHUB_REPO` → **stub mode**: `status: "queued"`, `dispatched: false`, detail บอกเหตุ (ไม่ error)

### 14) `GET /api/deployments/:id` — สถานะ deploy
Response `200`: deployment object (id, status, environment, commit_sha, …)

### 15) `PATCH /api/deployments/:id` — callback จาก CI workflow
Request: `{ "status": "success|failed|running", "commit_sha": "…"(optional) }`
- ย้อนสถานะ / แก้ terminal (success/failed) → **409**
- `success` + มี task_id + task ยัง `done` → เลื่อน task → `deployed` อัตโนมัติ (สะท้อนบอร์ด)
- ผู้เรียกที่ตั้งใจ: GitHub workflow (ดู `docs/github-workflow-example.yml`)

---

## Endpoints ตามแผนที่ยังไม่มี
| Endpoint | หมายเหตุ |
|----------|---------|
| `POST /api/tasks/:id/assign` | contract ระบุไว้ — ปัจจุบัน PATCH ครอบคลุม; ทำเมื่อมี use case จริง |

## Contract-sync rule
Frontend types (`frontend/src/lib/types.ts`) เขียนมือ mirror schemas —
**แก้ response shape ฝั่ง backend ต้องแก้ types.ts ในคอมมิตเดียวกัน** (ดู AI_AGENT_GUIDE.md)
