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

## ประตูหน้าบ้าน (ตั้งแต่ 2026-08-14)

ตั้ง `API_TOKEN` ใน `backend/.env` แล้ว **ทุก `/api/*` ต้องแนบ header** `X-DEP-PM-Token`
ให้ตรง มิฉะนั้น **401** · ไม่ตั้งค่า = ไม่ตรวจ (โหมด dev บน localhost — พฤติกรรมเดิม)

- **ยกเว้น:** `/health` (probe) · `/docs` `/redoc` `/openapi.json` (ไม่มีข้อมูลผู้ใช้) ·
  `OPTIONS` (CORS preflight ไม่พก custom header) ·
  **`PATCH /api/deployments/:id`** ซึ่งมี `X-DEP-PM-Secret` ของตัวเองอยู่แล้ว
  (บังคับ token ด้วยจะทำให้ workflow ที่ติดตั้งไปแล้วทุกตัวพัง)
- ⚠️ **token ต้องเป็น ASCII** — HTTP header ส่งภาษาไทยไม่ได้ (client encode ไม่ผ่านตั้งแต่ต้นทาง)
  · มี validator กันไว้ตอนสตาร์ต ไม่ปล่อยให้ไปเจอตอนใช้
- `GET /health` บอก `api_auth_enabled` ว่าล็อกแล้วหรือยัง (ไม่ใช่ความลับ)

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
  "ceo_report": null, "error": null, "stopped_reason": null,
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
- `status` ∈ `running` | `succeeded` | `failed` | `cancelled` (คนละชุดกับ `TaskStatus`) · `failed` → ดู `error`
  (ผลงานที่ commit ไปแล้วก่อนพังยังอยู่ — engine commit ต่อ task)
- `processed` < `total` ตอนจบ = ปกติ: task ที่รอ dependency ซึ่ง escalated จะค้าง `planned` ทั้งรอบ
- `stopped_reason` ≠ null = รอบ**จบเรียบร้อย (`succeeded`) แต่หยุดก่อนงานหมด** — ตอนนี้มีเหตุเดียว
  คือถึงเพดานค่าใช้จ่ายและตั้งไว้ว่า `stop` (§19.1) · **คนละช่องกับ `error` โดยเจตนา**:
  ไม่ใช่ความล้มเหลว · เพดานถูกถามก่อนหยิบ task ใหม่เท่านั้น (ไม่ตัดกลาง task) ·
  งานที่เหลือยังค้าง `planned` — ขยับเพดานแล้วกด Run ใหม่ทำต่อได้ทันที
- `ceo_report` = `null` เมื่อโปรเจกต์ไม่ได้มาจาก d_CEO — ถ้ามาจาก d_CEO และงานจบครบ
  ระบบรายงานกลับเข้า QC gate ให้อัตโนมัติหลังรอบรันจบ (ล้มเหลว = บันทึกไว้ใน `ceo_report.detail`
  ไม่ทำให้รอบรัน `failed` · ยิง §19 ซ้ำเองได้)
- **404** = โปรเจกต์นี้ยังไม่เคยรันในโปรเซสนี้ — ทะเบียนรอบรันอยู่ในหน่วยความจำ
  (restart backend = ประวัติหาย แต่ผลงานจริงใน `tasks`/`audit_log` ไม่หาย) ·
  ส่ง `run_id` ของโปรเจกต์อื่นก็ 404

---

### 7.2) `POST /api/projects/:id/run/cancel` — ขอให้รอบรันหยุด
Query (optional): `run_id` — ไม่ส่ง = รอบล่าสุดของโปรเจกต์นี้
Response `200`: snapshot เดียวกับ §7.1 โดย `cancel_requested: true`
- **หยุดหลัง task ที่กำลังทำอยู่จบ ไม่ตัดกลางคัน** — ตัดกลางจะเหลือ task ค้างสถานะกลางทาง
  ให้มาแก้มือ และจ่ายค่า token ไปแล้วโดยไม่ได้ผลงาน
- รอบที่หยุดแล้วมี `status: "cancelled"` · **ไม่รายงานกลับ d_CEO** (รอบยังไม่จบ)
  · งานที่เสร็จแล้วยังอยู่ครบ — กด Run ใหม่ทำต่อเฉพาะ `planned` ที่เหลือ
- **404** = ไม่มีรอบรันของโปรเจกต์นี้ · **409** = รอบนั้นจบไปแล้ว

---

### 8) `PATCH /api/tasks/:id` — อัปเดต task (State Machine enforced)
Request (ทุก field optional): `{ "status": "planned", "assignee_type": "human", "title": "…" }`
- `status` ต้องเป็น transition ที่ถูกต้อง ไม่งั้น **409** `{"detail": "invalid transition: backlog -> done"}`
- Transition ที่อนุญาต: ดู State Machine ใน `SYSTEM_DOCUMENTATION.md` §9
- `escalated` มี 2 ทางออก: → `in_progress` (คนลงมือต่อเอง) · → `planned` (**ตีกลับเข้าคิว**
  ให้ orchestrator ลองใหม่ — ใช้เมื่อแก้เหตุที่ทำให้ตันแล้ว · `revision_count` ไม่ถูกรีเซ็ต
  จึงได้โอกาสอีกรอบเดียว ไม่วนจ่ายค่า LLM)
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
Response:
```json
{ "status": "ok", "agent_enabled": true, "ceo_enabled": true,
  "llm_providers": ["anthropic", "openai"], "llm_chain": ["anthropic", "openai"] }
```
- `agent_enabled` = มีคีย์ของผู้ให้บริการ AI **อย่างน้อยหนึ่งเจ้า** (เดิมผูกกับ Anthropic ตัวเดียว
  — เปลี่ยน 2026-08-14 ตอนรองรับหลายเจ้า) · false = ระบบอยู่โหมด deterministic
- `llm_providers` = เจ้าที่ตั้งคีย์ไว้แล้ว · `llm_chain` = **ลำดับที่จะถูกเรียกจริง**
  (ตัวหลักก่อน แล้วตามด้วยตัวสำรอง) — ดูจากภายนอกได้ว่าตอนนี้ยังมีใครทำงานให้ได้บ้าง
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
Header: `X-DEP-PM-Secret: <DEPLOY_CALLBACK_SECRET>` — **บังคับเมื่อตั้งค่า secret แล้ว**
- ย้อนสถานะ / แก้ terminal (success/failed) → **409**
- `success` + มี task_id + task ยัง `done` → เลื่อน task → `deployed` อัตโนมัติ (สะท้อนบอร์ด)
- ผู้เรียกที่ตั้งใจ: GitHub workflow (ดู `docs/github-workflow-example.yml`)
- **401** = ไม่แนบ header หรือค่าไม่ตรง · **ไม่ตั้ง `DEPLOY_CALLBACK_SECRET` = ไม่ตรวจเลย**
  (ค่าปริยายสำหรับ dev บน localhost — 🔴 ต้องตั้งก่อนเปิดพอร์ตออกนอกเครื่อง, Risk #1)
- **endpoint เดียวในระบบที่มี auth** เพราะเป็นจุดเดียวที่ผู้เรียกอยู่นอกเครื่อง
  (§13/§13.1/§14 เป็นของ UI ในเครื่อง — MVP ยังไม่มี auth โดยเจตนา ดู `SECURITY.md`)

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

### 18.1) `POST /api/ceo/qc/:project_id` — สั่ง QC ตรวจซ้ำ (**ปุ่มฉุกเฉิน**)
เรียก `POST /tasks/{id}/qc` ของ d_CEO · Response `200`: `{ "ceo_task_id": "…", "status": "…", "detail": "สั่ง QC ตรวจแล้ว" }`
- **ปกติไม่ต้องใช้** — ตั้งแต่ contract v6 (2026-08-03) d_CEO ส่งเข้า QC ต่อเองเมื่อ PATCH
  เลื่อนสถานะ**เข้า** `qc_review` พร้อม `output` ซึ่ง §19 ทำอยู่แล้ว (ยิงครั้งเดียว ทั้ง status+output)
- ใช้เมื่อ QC ฝั่งเขาล่มตอนนั้นแล้วงานค้าง · **400** ไม่ใช่โปรเจกต์จาก d_CEO · **503** ต่อไม่ได้
- ⚠️ **1 รอบ QC มีราคา** (~ครึ่งของค่างานหนึ่งชิ้น) อย่ายิงซ้ำเล่น

---

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

## ตั้งค่าผู้ให้บริการ AI (ใบสั่งงาน 2026-08-06 "รองรับ AI หลายเจ้า")

> 🔒 **กลุ่ม endpoint ที่อ่อนไหวที่สุดในระบบ** — อ่าน/เขียนคีย์จริงลง `backend/.env`
> ระบบนี้ยังไม่มี authentication ⇒ **bind `127.0.0.1` เท่านั้น** (docs/SECURITY.md) ·
> ขาออก**ไม่มีคีย์เต็มเด็ดขาด** (mask อย่างเดียว)

### 1.2.1) `GET /api/projects/scaffold-options` — ตัวเลือกของฟอร์มเปิดโปรเจกต์ใหม่
```json
{ "allowed_root": "D:\\Dev_Proj",
  "teams": [ { "name": "0_CORE", "hint": "เลขา/Orchestrator + ระบบกลาง" },
             { "name": "4_RND", "hint": "วิจัยและพัฒนา" },
             { "name": "_INBOX", "hint": "ยังไม่จัดทีม — ต้องย้ายออกภายใน 7 วัน" } ],
  "inbox": "_INBOX" }
```
- อ่านอย่างเดียว ไม่แตะดิสก์ · รายชื่อทีม**อ่านจากโฟลเดอร์จริง**ใต้ `SCAFFOLD_ALLOWED_ROOT`
  (ขึ้นต้นด้วย `<เลข>_` + `_INBOX`) — เพิ่มทีมใหม่แล้วฟอร์มเห็นเองโดยไม่ต้องแก้โค้ด
- ฟอร์มใช้ประกอบ `target` = `<allowed_root>\<ทีม>\<ชื่อโปรเจกต์>` แทนให้คนพิมพ์ path เต็มเอง
  (พฤติกรรมเดิมของ `new-project-studio` · ราก **ห้าม hardcode ฝั่ง frontend**)
- รากไม่มีอยู่จริง/อ่านไม่ได้ → `teams: []` แล้วฟอร์มกลับไปพิมพ์เอง — ไม่ใช่ error
- ⚠️ ต้องประกาศ route นี้**ก่อน** `/{project_id}` เสมอ ไม่งั้นถูกจับเป็น project_id → 422

### 1.3) `POST /api/projects/bootstrap` — เปิดโปรเจกต์ใหม่ **ของจริง** (ADR-05)
Request:
```json
{ "name": "d_NewThing", "target": "D:\\Dev_Proj\\4_RND\\d_NewThing", "kind": "code",
  "purpose": "…", "stack": "Python 3.12 + FastAPI",
  "relation": "product", "is_python": true, "team": "", "dual_ps": false }
```
Response `201`: `{ project, target, created[], steps[], first_task_id }`
- สร้าง**โฟลเดอร์จริง** + เอกสารกำกับจาก kit + ตัวชี้ `_CANON` + `.gitignore` + `git init`
  แล้ว**ลงบอร์ดพร้อม task "Sign-off เอกสารกำกับก่อนเริ่มงาน"** ในคราวเดียว
- **ไม่เรียก AI เลย** (deterministic ล้วน — "AI ล่ม ระบบไม่ล่ม") · **ไม่ auto-commit** git
- `relation` กำหนดว่าจะได้เอกสารชุดไหน (`eco-core`/`eco-team` ได้ `INTEGRATION_CEO.md` เพิ่ม)
- `kind` (`code` ปริยาย · `doc`) กำหนด**เส้นทาง 6 ขั้น**ของโปรเจกต์ที่ลงบอร์ด (§1.3 stages)
- **400** เมื่อ target อยู่นอก `SCAFFOLD_ALLOWED_ROOT` หรือ `relation` ไม่รู้จัก
  — ตรวจก่อนแตะดิสก์ ไม่มีโฟลเดอร์/โปรเจกต์ค้าง
- **422** เมื่อ `kind: "idea"` — ไอเดียคือสิ่งที่ยังไม่ลงมือ จึงไม่ควรมีโฟลเดอร์จริง
  (จะเปิดโฟลเดอร์ให้ไอเดียต้องผ่าน `/promote` ซึ่งเปลี่ยนชนิดเป็น `code`/`doc` ไปพร้อมกัน)

### 1.3.1) `POST /api/projects/:id/commit` — commit แรกของโปรเจกต์ที่เพิ่งเปิด
Response `200`: `{ "detail": "git: commit แรกเรียบร้อย" }`
- `git add -A` + commit ข้อความ `chore: initial bootstrap (new-project-studio)` ในโฟลเดอร์
  ของโปรเจกต์นั้นเท่านั้น · ใช้ git identity ของเครื่อง
- **ไม่มีอะไรให้ commit = ไม่ใช่ error** — คืน `"git: ไม่มีอะไรให้ commit (clean อยู่แล้ว)"`
- 🔴 **คนเป็นคนกด** — `/bootstrap` ยัง**ไม่ commit ให้เอง** เพราะต้องได้ตรวจช่อง
  `Need confirmation` ก่อน (ปุ่มเดียวกับที่ `new-project-studio` เคยมี)
- **400** ถ้าโปรเจกต์ไม่มี `local_path` / โฟลเดอร์หาย / ยังไม่เป็น git repo

### 1.4) `POST /api/projects/:id/design-files` — อัปโหลดไฟล์ดีไซน์ (multipart)
Form: `files` (หลายไฟล์) + `note` (ไม่บังคับ) →
`{ "saved": ["โจทย์.md", …], "requirement": "…", "requirement_chars": 12345 }`
- เก็บไฟล์ที่ `<โฟลเดอร์โปรเจกต์>/_design_input/` (kit `.gitignore` กันไว้แล้ว)
- ดึงข้อความจาก `.md/.txt/.pdf/.docx` · **รูปภาพบอกตรง ๆ ว่าอ่านไม่ได้** ไม่เดาจากชื่อไฟล์
- เพดาน 20,000 ตัวอักษร/ไฟล์ · 60,000 รวม — เกินแล้วบอกว่าไฟล์ไหนถูกข้าม
- **ไม่เรียก AI** — คนอ่าน `requirement` ตรวจก่อน แล้วค่อยส่งต่อ `/breakdown` เอง
- **400** ถ้าโปรเจกต์ไม่มี `local_path` (ไม่ได้เปิดผ่าน `/bootstrap`)

### 1.5) `POST /api/projects/:id/deliverables` — เขียนผลงานของ task ลงไฟล์จริง
Request: `{ "task_id": "…", "path": "docs/PROJECT_OVERVIEW.md" }` →
`{ path, bytes, backup, task_id }`
- เอา **work product ฉบับล่าสุด** ของ task (จาก Message Bus) ไปเขียนเป็นไฟล์
- 🔒 เขียนได้เฉพาะ**ใต้โฟลเดอร์ของโปรเจกต์นั้น** (`..` ถูกปฏิเสธ) ·
  **สำรองไฟล์เดิมก่อนทับเสมอ** ลง `BackUp/Deliverable_<เวลา>/` (WORKING_RULES Rule 1) ·
  UTF-8 ไม่มี BOM · **ไม่ commit ให้**
- **เป็นขั้นที่คนสั่งเอง** — agent เขียนไฟล์เองไม่ได้ (LLM ทุกตัวผ่าน providers ที่ไม่มี tool)
- **400** ถ้า task ยังไม่มีผลงาน / path หลุดกรอบ / โปรเจกต์ไม่มีโฟลเดอร์

---

### 1.2) `DELETE /api/projects/:id` — ลบโปรเจกต์ (ล้างงานทดสอบออกจากบอร์ด)
- `204` = ลบแล้ว · ลบ tasks / agent_messages / deployments ของโปรเจกต์นั้นไปด้วย
- **409 ถ้าโปรเจกต์ผูกกับงานของ d_CEO** (`ceo_task_id`) — ฝั่งโน้นยังอ้างอยู่
  ต้องจงใจตัดสายก่อน ไม่ใช่ลบทิ้งแล้วให้เลขาชี้ไปที่ของที่ไม่มีอยู่
- 🔴 **กู้จาก API ไม่ได้** — ผลงาน agent ทั้งหมดของโปรเจกต์นั้นหายไปด้วย
  · สำรอง `backend/dep_pm.db` ก่อนเสมอ (WORKING_RULES Rule 3)
- ยังไม่มีปุ่มบน UI (ตั้งใจ — กันกดพลาด) เรียกผ่าน API เท่านั้น

---

### 1.3) `GET /api/projects/:id/stages` — เส้นทาง 6 ขั้นของโปรเจกต์
```json
{ "kind": "code", "current": "build",
  "stages": [
    { "stage": "idea", "label": "ไอเดีย", "state": "done" },
    { "stage": "structure", "label": "โครงสร้าง", "state": "done" },
    { "stage": "plan", "label": "แผนงาน", "state": "done" },
    { "stage": "build", "label": "ลงมือ", "state": "current" },
    { "stage": "ship", "label": "ส่งขึ้นระบบ", "state": "todo" },
    { "stage": "market", "label": "การตลาด", "state": "todo" } ],
  "next_action": "เหลืออีก 4 งาน — กด Run ให้ agent ทำต่อ",
  "ready_to_promote": false, "open_tasks": 4, "total_tasks": 7 }
```
- 🔴 **คำนวณสดทุกครั้ง ไม่ได้เก็บในฐานข้อมูล** — เกณฑ์เป็นสิ่งที่ปลอมไม่ได้: มีโฟลเดอร์จริงไหม ·
  มี task ที่พ้น `backlog` แล้วหรือยัง · เหลืองานค้างกี่ใบ · เคย deploy สำเร็จหรือยัง
- **ชนิดงานเปลี่ยนเส้นทาง:** `doc` ไม่มีขั้น `structure` และเรียกขั้น `ship` ว่า **"ส่งมอบ"** ·
  `idea` มีแค่ 3 ขั้นแรกแล้วจบที่ `ready_to_promote: true`
- `market` ยัง**ไม่ผ่านเสมอ** จนกว่าจะต่อ d_MOS (ก้อนที่ 4) — `next_action` บอกตรง ๆ ว่ายังไม่เปิดใช้
- `state` ∈ `done` | `current` | `todo` · `current: null` = เดินครบเส้นแล้ว

### 1.4) `POST /api/projects/:id/promote` — ยกระดับไอเดีย → โปรเจกต์จริง
Request: `{ "kind": "code" | "doc", "target": "D:\\Dev_Proj\\4_RND\\d_X", "purpose": "", "stack": "", "is_python": true, "relation": "general" }`
```json
{ "project": { "…": "…", "kind": "code" },
  "target": "D:\\Dev_Proj\\4_RND\\d_X", "created": ["AGENTS.md", "…"], "steps": ["…"] }
```
- **409** ถ้าโปรเจกต์ไม่ใช่ชนิด `idea` · **422** ถ้าขอยกระดับกลับเป็น `idea`
- ใส่ `target` = scaffold โฟลเดอร์จริงให้ในคราวเดียว (เหมือน §1.2) · ไม่ใส่ = เปลี่ยนชนิดงานอย่างเดียว
- **งานที่ศึกษาไว้ทั้งหมดอยู่ครบ** — ยกระดับไม่ใช่การเริ่มใหม่ · scaffold ล้ม (400) = **ไม่เปลี่ยนชนิด**
  (ไม่งั้นได้โปรเจกต์ `code` ที่ไม่มีบ้านอยู่)

### 1.5) `GET /api/projects/ideas/preview` · `POST /api/projects/ideas/import`
```json
{ "roots": ["D:\\Dev_Proj\\IDEAs", "D:\\Dev_Proj\\6_KM\\Ideas"],
  "found": 9, "already_on_board": 0,
  "items": [ { "name": "3D Cartoon Animation Workflow", "source_root": "D:\\Dev_Proj\\IDEAs",
               "files": ["…"], "is_folder": true, "updated": "2026-07-30" } ] }
```
- `preview` **ไม่เขียนอะไรเลย** · `import` (body `{"names": []}` = เอาทั้งหมดที่ยังไม่มี) คืน `201` + รายการโปรเจกต์ที่สร้าง
- **ยิงซ้ำได้** — เทียบด้วยชื่อในกลุ่มโปรเจกต์ชนิด `idea` · รอบสองคืน `[]`
- **ไฟล์ต้นทางไม่ถูกย้าย/แก้/ลบ** · ไฟล์ชื่อเดียวกันหลายนามสกุล (`.md` + `.html`) นับเป็นไอเดียเดียว
- ไอเดียที่เป็น**ไฟล์เดี่ยวไม่ได้ `local_path`** — โฟลเดอร์ต้นทางเป็นของรวม ผูกไว้ = เปิดสิทธิ์เขียนทับกัน
- โฟลเดอร์ที่ไปตามหาตั้งได้ที่ `IDEA_ROOTS` (คั่นด้วย `;`)

---

### 19.1) `GET /api/projects/:id/usage` — โทเคนแยกตามผู้ให้บริการ + ค่าใช้จ่ายเทียบเพดาน
```json
{ "project_id": "…",
  "totals": { "input": 3208, "output": 651, "calls": 2 },
  "by_provider": [
    { "provider": "anthropic", "model": "claude-sonnet-5",
      "input": 3208, "output": 651, "calls": 2, "tasks": 1, "cost_usd": 0.0194 } ],
  "untracked": { "input": 0, "output": 0, "calls": 0 },
  "budget": { "spent_usd": 0.0194, "limit_usd": 5.0, "action": "warn",
              "over": false, "excludes_untracked": false } }
```
- **ถังสำหรับเพดานค่าใช้จ่ายต่อเจ้า** (§5 ใบสั่งงาน 2026-08-06) — ราคาต่อโทเคนแต่ละเจ้าไม่เท่ากัน
  ยอดรวมก้อนเดียวจึงคุมไม่อยู่เมื่อระบบสลับเจ้าเอง
- `by_provider` เรียงจากตัวที่กินมากสุด · `tasks` = จำนวน task ที่เจ้านั้นมีส่วนร่วม
  (1 task มีได้หลายเจ้า — Team Mode: dev=openai, reviewer=anthropic)
- ⚠️ **`untracked` = โทเคนที่นับรวมไว้แต่ระบุเจ้าไม่ได้** — งานที่ทำก่อน 2026-08-14 ·
  จงใจแยกให้เห็นแทนการเดาย้อนหลังว่าเป็นของเจ้าไหน
- 🔴 **`cost_usd` / `spent_usd` เป็น "ประมาณการ"** — คิดจากราคาใน `.env` (`LLM_PRICE_*`)
  × โทเคนที่นับได้ **ไม่ใช่บิลจริง** (ส่วนลด/เครดิต/ราคาพิเศษของบัญชีไม่ถูกนับ)
  · `excludes_untracked: true` = มีโทเคนที่ระบุเจ้าไม่ได้ ⇒ ของจริง**สูงกว่า**ตัวเลขนี้
- `budget.limit_usd = 0` = ไม่ได้ตั้งเพดาน · `action` = `warn` (เตือน) | `stop` (ไม่เริ่ม task ใหม่)
  — ดู §12 `POST /:id/run` เรื่อง `stopped_reason`
- `TaskRead` ก็มี `token_usage` ของ task นั้นด้วย (`{"<provider>": {model, input, output, calls}}`)

---

### 20) `GET /api/settings/llm` — ค่าปัจจุบัน
```json
{ "provider": "anthropic", "fallbacks": ["openai"],
  "budget_usd": 0, "budget_action": "warn",
  "providers": [
    { "name": "anthropic", "model": "claude-sonnet-5", "key_set": true, "key_masked": "sk-…4f2a",
      "price_in": 3.0, "price_out": 15.0 },
    { "name": "openai", "model": "gpt-5.2", "key_set": false, "key_masked": "",
      "price_in": 1.25, "price_out": 10.0 }
  ] }
```
- `price_in`/`price_out` = ราคาต่อ **1 ล้านโทเคน** ที่ใช้ประมาณการค่าใช้จ่าย — **อ่านอย่างเดียว**
  (แก้ที่ `.env` เท่านั้น: เป็นตัวเลขที่ต้องยืนยันกับบิลจริงก่อน ไม่ใช่ค่าที่ควรกดเปลี่ยนจากหน้าเว็บ)

### 21) `PUT /api/settings/llm` — บันทึกคีย์/รุ่น/ลำดับ (**มีผลทันที ไม่ต้อง restart**)
Request (ทุก field เป็น optional):
```json
{ "provider": "anthropic", "fallbacks": ["openai", "google"],
  "keys": { "openai": "sk-…" }, "models": { "openai": "gpt-5.2" },
  "budget_usd": 5.0, "budget_action": "stop" }
```
- `budget_usd` ติดลบ → **422** · `budget_action` นอกเหนือ `warn`/`stop` → **400**
  (ไม่ปล่อยให้ค่าพิมพ์ผิดตกไปเป็น `warn` เงียบ ๆ แล้วเจ้าของนึกว่าตั้งเพดานไว้แล้ว)
- ⚠️ **ไม่ส่ง key ของเจ้าไหน = ไม่แตะของเดิม · ส่งสตริงว่าง = ตั้งใจลบ** (แค่เปิดหน้าเว็บแล้วกด
  บันทึกต้องไม่ล้างคีย์ทิ้ง)
- เขียนกลับ `.env` แบบ**แก้เฉพาะบรรทัดที่เกี่ยว** (คอมเมนต์/ตัวแปรอื่นอยู่ครบ) · UTF-8 **ไม่มี BOM**
  (WORKING_RULES §6.1ข) · สำรองไฟล์เดิมไว้ที่ `BackUp/EnvSettings_<ts>/` ทุกครั้ง
- ชื่อผู้ให้บริการที่ไม่รู้จัก → **400** · Response = เหมือน §20
- ค่าที่ตั้งจะไปอยู่ใน `Settings` ที่โหลดไว้แล้วทันที (ไม่ล้าง `lru_cache` เพราะมีโมดูลที่จับ
  instance ไว้ตั้งแต่ import)

### 22) `POST /api/settings/llm/test` — ยิงจริงหนึ่งครั้งเพื่อดูว่าคีย์ใช้ได้ไหม
Request: `{ "provider": "openai" }` (ไม่ระบุ = ทดสอบทุกเจ้า)
```json
{ "results": [
  { "provider": "openai", "ok": true, "model": "gpt-5.2", "latency_ms": 3396, "kind": null, "detail": "" },
  { "provider": "google", "ok": false, "model": "", "latency_ms": 412,
    "kind": "account", "detail": "401 UNAUTHENTICATED. …" } ] }
```
- `kind` ∈ `account` (เครดิตหมด/คีย์ผิด) · `temporary` (429/5xx) · `request` (ชื่อรุ่น/prompt ผิด) ·
  `unknown` — ใช้ `classify_error()` **ชุดเดียวกับตอนทำงานจริง** ⇒ ปุ่มนี้คือเครื่องมือตรวจ
  ตารางแยก error ในตัว
- ยิงเจ้านั้น **ตรง ๆ ไม่ผ่านลำดับสำรอง** (ต้องรู้ผลของเจ้านั้นจริง ไม่ใช่ผลของตัวสำรอง) ·
  prompt สั้นที่สุด ⇒ ค่าใช้จ่ายแทบเป็นศูนย์

---

## Endpoints ตามแผนที่ยังไม่มี
| Endpoint | หมายเหตุ |
|----------|---------|
| `POST /api/tasks/:id/assign` | contract ระบุไว้ — ปัจจุบัน PATCH ครอบคลุม; ทำเมื่อมี use case จริง |

## Contract-sync rule
Frontend types (`frontend/src/lib/types.ts`) เขียนมือ mirror schemas —
**แก้ response shape ฝั่ง backend ต้องแก้ types.ts ในคอมมิตเดียวกัน** (ดู AI_AGENT_GUIDE.md)
