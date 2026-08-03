# API.md — DEP-PM Platform

> API Documentation (MASTER PROMPT §12) | อัปเดต: 2026-07-06 (หลัง Sprint 4)
> Interactive docs: รัน backend แล้วเปิด `http://127.0.0.1:8500/docs` (OpenAPI อัตโนมัติ)

## ภาพรวม

| หัวข้อ | ค่า |
|--------|-----|
| Base URL (dev) | `http://127.0.0.1:8500` (**ไม่ใช่ 8000** — พอร์ตนั้นเป็นของ d_CEO) |
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

### 1.1) `GET /api/projects/:id` — รายละเอียดโปรเจกต์
Response `200`: Project object เดียวกับข้างบน (+ `ceo_task_id`)
- `ceo_task_id` = task ใน d_CEO ที่ถูก delegate ลงมาเป็นโปรเจกต์นี้ (`null` = สร้างเองในระบบ)
  — UI ใช้ตัดสินว่าจะโชว์ป้าย "งานจากเลขา" และปุ่ม "ส่งผลกลับเลขา" ไหม
- 404 ถ้าไม่พบ

---

### 2) `GET /api/projects/:id/tasks?limit=50&offset=0` — รายการ task
- `limit` clamp 1..200, `offset` ≥ 0, เรียง `created_at`
Response `200`:
```json
{ "data": [ { "id": "…", "title": "…", "status": "backlog", "priority": "P2",
              "assignee_type": null, "agent_role": null, "depends_on": [],
              "spec": null, "estimate_points": null, "revision_count": 0,
              "tokens_input": 0, "tokens_output": 0, "…": "…" } ],
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
- `depends_on` ทุก id ต้องเป็น task จริงในโปรเจกต์เดียวกัน ไม่งั้น **400** (referential check)

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

### 7) `POST /api/projects/:id/run` — สั่งรัน Solo-Mode Orchestrator (**เบื้องหลัง**)
**Asynchronous ตั้งแต่ Phase 2** — ตอบ `202` ทันที (วัดจริง ~10 ms) แล้วงานเดินต่อในเธรดเบื้องหลัง
Response `202`:
```json
{ "run_id": "…", "project_id": "…", "status": "running",
  "total": 6, "processed": 0, "counts": {}, "outcomes": [],
  "ceo_report": null, "error": null,
  "started_at": "2026-08-03T02:29:26.686806+00:00", "finished_at": null }
```
- **409** = โปรเจกต์นี้มีรอบรันค้างอยู่ (`{"detail": "โปรเจกต์นี้กำลังรันอยู่แล้ว (run_id=…)"}`) —
  lock เป็นราย**โปรเจกต์** คนละโปรเจกต์รันพร้อมกันได้
- `total` = จำนวน task `planned` ตอนเริ่มรอบ (เป้าของ progress) · 404 = ไม่มีโปรเจกต์นี้
- รันเฉพาะ task `planned` ที่ dependency (`depends_on`) เป็น done/deployed ครบ
- Side effects ต่อ task: routing audit, transitions, ข้อความ bus ≥3 (handoff/result/review_comment)
- **เหตุผลที่ต้องเป็น async:** UAT 2026-08-02 วัดได้ 6 tasks = 297 วินาที ขณะที่ผู้เรียกฝั่งบน
  (d_Jarvis) ตั้ง timeout 5 นาที

---

### 7.1) `GET /api/projects/:id/run` — ความคืบหน้าของรอบรัน
Query (optional): `run_id` — ไม่ส่ง = รอบล่าสุดของโปรเจกต์นี้
Response `200`: รูปเดียวกับ §7 แต่ค่าอัปเดตตามจริง
```json
{ "run_id": "…", "status": "succeeded", "total": 6, "processed": 5,
  "counts": { "done": 4, "escalated": 1 },
  "ceo_report": { "ready": true, "reported": true, "status_sent": "qc_review",
                  "detail": "ส่งผลงานเข้า QC gate ของ d_CEO แล้ว" },
  "error": null, "finished_at": "2026-08-03T02:29:48.268239+00:00",
  "outcomes": [ { "task_id": "…", "title": "…", "final_status": "done", "revisions": 1 } ] }
```
- `status` ∈ `running` | `succeeded` | `failed` (คนละชุดกับ `TaskStatus`) · `failed` → ดู `error`
  (ผลงานที่ commit ไปแล้วก่อนพังยังอยู่ — engine commit ต่อ task)
- `processed` < `total` ตอนจบ = ปกติ: task ที่รอ dependency ซึ่ง escalated จะค้าง `planned` ทั้งรอบ
- `ceo_report` = `null` เมื่อโปรเจกต์ไม่ได้มาจาก d_CEO — ถ้ามาจาก d_CEO และงานจบครบ
  ระบบรายงานกลับเข้า QC gate ให้อัตโนมัติหลังรอบรันจบ (ล้มเหลว = บันทึกไว้ใน `ceo_report.detail`
  ไม่ทำให้รอบรัน `failed` · ยิง §19 ซ้ำเองได้)
- **404** = โปรเจกต์นี้ยังไม่เคยรันในโปรเซสนี้ — ทะเบียนรอบรันอยู่ในหน่วยความจำ
  (restart backend = ประวัติหาย แต่ผลงานจริงใน `tasks`/`audit_log` ไม่หาย) ·
  ส่ง `run_id` ของโปรเจกต์อื่นก็ 404

---

### 8) `PATCH /api/tasks/:id` — อัปเดต task (State Machine enforced)
Request (ทุก field optional): `{ "status": "planned", "assignee_type": "human", "title": "…" }`
- `status` ต้องเป็น transition ที่ถูกต้อง ไม่งั้น **409** `{"detail": "invalid transition: backlog -> done"}`
- Transition ที่อนุญาต: ดู State Machine ใน `SYSTEM_DOCUMENTATION.md` §9
Response `200`: Task | Side effects: audit `task.transition` และ/หรือ `task.updated`

---

### 8.1) `DELETE /api/tasks/:id` — ลบ task
Response `204` (no body) | Side effects: audit `task.deleted`,
ลบ agent_messages ของ task (CASCADE), deployments ที่อ้าง task → `task_id: null` (SET NULL)
- มี task อื่นอ้างใน `depends_on` → **409** พร้อมรายชื่อ task ที่อ้าง (กัน dangling id — ต้องแก้/ลบตัวอ้างก่อน)

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
Response: `{ "status": "ok", "agent_enabled": false, "ceo_enabled": true }`
- `agent_enabled` = มี `ANTHROPIC_API_KEY` จริงหรือไม่ (UI ใช้บอกผู้ใช้ว่าอยู่โหมด fallback)
- `ceo_enabled` = ตั้ง `CEO_API_BASE` ไว้ไหม (**ออนไลน์จริงหรือไม่** ดูที่ §16)

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

### 13.1) `GET /api/deployments?project_id=…&limit=50&offset=0` — รายการ deployments
- เรียงใหม่ล่าสุดก่อน | `project_id` optional (ไม่ใส่ = ทุกโปรเจกต์) | `limit` clamp 1..200
Response `200`:
```json
{ "data": [ { "id": "…", "status": "queued", "environment": "staging",
              "triggered_by": "manual", "commit_sha": null, "created_at": "…",
              "project_name": "Demo", "task_title": "ship" } ],
  "pagination": { "total": 1, "limit": 50, "offset": 0 } }
```
ใช้กับหน้า `/deployments` ใน UI (เติม `project_name`/`task_title` ให้แล้ว)

### 14) `GET /api/deployments/:id` — สถานะ deploy
Response `200`: deployment object (id, status, environment, commit_sha, …)

### 15) `PATCH /api/deployments/:id` — callback จาก CI workflow
Request: `{ "status": "success|failed|running", "commit_sha": "…"(optional) }`
- ย้อนสถานะ / แก้ terminal (success/failed) → **409**
- `success` + มี task_id + task ยัง `done` → เลื่อน task → `deployed` อัตโนมัติ (สะท้อนบอร์ด)
- ผู้เรียกที่ตั้งใจ: GitHub workflow (ดู `docs/github-workflow-example.yml`)

---

## d_CEO integration (Phase 1) — DEP-PM รับงานในฐานะ Team Lead R&D

> contract เต็ม + กติกา: [`INTEGRATION_CEO.md`](./INTEGRATION_CEO.md)
> ทั้งหมดเป็น **manual** โดยตั้งใจ — ผู้ใช้กดเอง (หลัก "ยืนยันก่อนทำ" ของ ecosystem)

### 16) `GET /api/ceo/status` — สมองออนไลน์ไหม
```json
{ "enabled": true, "online": true, "base_url": "http://127.0.0.1:8000",
  "team_name": "Research & Development", "team_id": "4406dde7-…", "waiting": 2 }
```
- **ไม่เคยตอบ 503** — UI ใช้ตัดสินว่าจะโชว์ปุ่มไหม | ปิดอยู่ → `{"enabled": false, "online": false, "team_name": "…"}`
- `waiting` = จำนวนงานใน d_CEO ที่รอเราดึง

### 17) `GET /api/ceo/inbox` — งานที่รออยู่
```json
{ "data": [ { "id": "56d3319d-…", "input_text": "แก้บั๊ก login…",
              "status": "queued", "created_at": "2026-08-02T10:00:00Z" } ], "total": 1 }
```
- เฉพาะงาน `queued` ที่ `assigned_team_id` = ทีม R&D **และยังไม่เคยถูกดึง**
- `created_at` เป็น **UTC** — frontend แปลงเป็น Asia/Bangkok เอง
- **503** ถ้า d_CEO ปิดอยู่หรือยังไม่ตั้ง `CEO_API_BASE`

### 18) `POST /api/ceo/pull` — รับงานมาทำ
Request (ทุก field optional): `{ "task_ids": ["…"], "breakdown": true }`
— `task_ids` ว่าง/ไม่ส่ง = รับทุกงานที่รออยู่
```json
{ "count": 1,
  "pulled": [ { "ceo_task_id": "56d3319d-…", "project_id": "…", "name": "แก้บั๊ก login",
                "task_count": 5, "breakdown_source": "agent", "acknowledged": true,
                "detail": "รับงานแล้ว + แจ้ง d_CEO เป็น in_progress" } ] }
```
Side effects ต่องาน: สร้าง project (`ceo_task_id` ผูกไว้) → PM Agent แตกงานเป็น backlog →
`PATCH /tasks/{id}` ที่ d_CEO เป็น `in_progress` → audit `project.created` (actor `ceo-sync`)
- ดึงซ้ำงานเดิมไม่ได้ (unique) — ได้ `count: 0`
- `acknowledged: false` = สร้างโปรเจกต์แล้วแต่แจ้ง d_CEO ไม่สำเร็จ (retry ได้ด้วย §19)
- **ผู้ใช้ยังต้อง confirm scope + กด Run เอง** — ระบบไม่รันให้อัตโนมัติ

### 19) `POST /api/ceo/report/:project_id` — ส่งผลงานกลับ
```json
{ "ready": true, "reported": true, "status_sent": "qc_review",
  "detail": "ส่งผลงานเข้า QC gate ของ d_CEO แล้ว",
  "counts": { "done": 4, "escalated": 1 }, "output": "# ผลงานจากทีม R&D — …" }
```
- 🔴 **ส่งได้แค่ `qc_review`** — ห้ามปิดงานเอง ต้องผ่าน QC gate ของ d_CEO
  (มติ Vinit 2026-08-02 · guardrail อยู่ใน `ceo_client.py` ValueError ก่อนยิง HTTP)
- `ready: false` = ยังมี task เดินอยู่ → **ไม่แตะ d_CEO เลย**
- **400** ถ้าโปรเจกต์ไม่มี `ceo_task_id` · **404** ไม่พบโปรเจกต์ · **503** ยังไม่ตั้งค่า/ปิดอยู่
- เรียกอัตโนมัติให้แล้วเมื่อรอบรัน §7 จบ (ผลอยู่ใน `ceo_report` ของ §7.1) —
  endpoint นี้ไว้ยิงซ้ำเมื่อรอบอัตโนมัติล้มเหลว

---

## Endpoints ตามแผนที่ยังไม่มี
| Endpoint | หมายเหตุ |
|----------|---------|
| `POST /api/tasks/:id/assign` | contract ระบุไว้ — ปัจจุบัน PATCH ครอบคลุม; ทำเมื่อมี use case จริง |

## Contract-sync rule
Frontend types (`frontend/src/lib/types.ts`) เขียนมือ mirror schemas —
**แก้ response shape ฝั่ง backend ต้องแก้ types.ts ในคอมมิตเดียวกัน** (ดู AI_AGENT_GUIDE.md)
