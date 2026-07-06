# CHANGELOG — DEP-PM Platform

## 2026-07-06 — Sprint 1: Backend Foundation

- Scaffold `backend/` — FastAPI + SQLAlchemy 2.x + Alembic บน SQLite (รันได้จริง)
- ORM 6 ตารางครบ (projects, tasks, agents, agent_messages, deployments, audit_log) พร้อม
  portable types: `GUID` + `JSON` decorator เพื่อย้าย PostgreSQL ได้โดยไม่แก้ model (ADR-01)
- Alembic 2 migrations: สร้าง schema + seed "Claude Solo" agent (mode=solo)
- **PM Agent Task Breakdown** (persona PM, Claude API): requirement → Task Plan JSON →
  validate ด้วย Pydantic + retry 1 ครั้งเมื่อ parse ไม่ได้ (Risk #7); ไม่มี API key → fallback
  task เดียว ไม่ล้ม flow
- Intake endpoints: `POST /api/projects`, `GET/POST /api/projects/:id/tasks`,
  `POST .../breakdown`, `POST .../confirm` (backlog → planned), `POST .../scan`
- `MetadataProvider` interface + `StubMetadataProvider` → `POST /api/projects/:id/scan`
  คืน mock Baseline Report (ระบุ "(mock)" ชัด — Risk #1) แปลงเป็น backlog tasks ได้ (ADR-02)
- `PATCH /api/tasks/:id`, `GET /api/tasks/:id/messages`; audit_log บันทึกทุก state change
- pytest 15 เคสผ่านทั้งหมด; `/health` รายงาน `agent_enabled`

## 2026-07-02 — Planning Phase Complete

- อ่านและวิเคราะห์เอกสารตั้งต้น 3 ไฟล์ (Blueprint v1.0, DEP v3.0 Master Plan, AI Dev Team Guide)
- จัดทำ `docs/DEVELOPMENT_PLAN.md` — แผนพัฒนา MVP 4 สปรินต์ (~8 สัปดาห์) ประกอบด้วย:
  - ADR-01: SQLite (dev) → PostgreSQL (prod)
  - ADR-02: Metadata Engine เป็น interface + stub (DEP v3.0 ยังไม่มีโค้ดจริง)
  - ADR-03: Message bus แบบ in-process ก่อน → Redis Streams
  - ADR-04: Realtime แบบ polling/SSE ก่อน → WebSocket
  - Data Model 6 ตาราง, API Contract 11 endpoints, Risk Register, Success Metrics
- สร้าง `PROJECT_STATUS.md` (สถานะ + next tasks) และเติมข้อมูลโปรเจกต์ใน `CLAUDE.md`
- ยังไม่มีโค้ดแอปพลิเคชัน — Sprint 1 เริ่มเมื่อผู้ใช้อนุมัติ
