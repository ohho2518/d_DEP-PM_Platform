# DEP-PM Platform

**AI-Native Project Management Platform** — บอร์ดเดียวที่มนุษย์และ AI Agent ทำงานร่วมกัน
รับ requirement → AI แตกงาน → มอบหมาย Agent/คน → ติดตามบน Kanban → deploy อัตโนมัติเมื่อผ่าน review

**สถานะ:** MVP ครบ 4 สปรินต์ · pytest 60/60 · ruff clean · ใช้งานจริงบนเครื่อง dev แล้ว
รายละเอียดล่าสุดอยู่ใน [`PROJECT_STATUS.md`](./PROJECT_STATUS.md)

---

## ทำอะไรได้บ้าง

| ความสามารถ | สรุป |
|---|---|
| **AI Task Breakdown** | PM Agent (Claude) แปลง requirement ภาษาคน → Task Plan พร้อม priority / estimate / ผังพึ่งพา |
| **Agent Orchestration** | Routing rules เลือก persona (Dev / Senior Architect) → agent ทำงาน → Reviewer ตรวจ → approve หรือขอแก้ (สูงสุด 2 รอบ → escalate ให้คน) |
| **Solo / Team Mode** | Solo = Claude ทุกบทบาท · Team = Dev→OpenAI, SR→Gemini, PM/Reviewer→Claude — **สลับด้วย env ไม่แก้โค้ด** |
| **Kanban + Message Log** | บอร์ด 8 คอลัมน์ตาม State Machine · ดูบทสนทนา agent ย้อนหลังได้ทุก task |
| **Automated Deploy** | task ผ่าน review → GitHub `repository_dispatch` → staging อัตโนมัติ, production ต้องคนสั่ง (Manual Approval Gate) |
| **Auditable by default** | ทุก state change ลง `audit_log` · ทุกข้อความ agent ลง `agent_messages` |

---

## Quick start

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv && .venv\Scripts\activate     # *nix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                                # ใส่ ANTHROPIC_API_KEY เพื่อเปิด agent จริง
alembic upgrade head
uvicorn app.main:app --reload --port 8400           # http://127.0.0.1:8400/docs

# Frontend (terminal 2)
cd frontend
npm install && cp .env.local.example .env.local
npm run dev                                         # http://localhost:3000
```

> **พอร์ต 8400 ไม่ใช่ 8000** — :8000 เป็นของ d_CEO ที่รันค้างตลอดในเครื่องนี้
> ไม่ใส่ `ANTHROPIC_API_KEY` ระบบยังเดินครบวงจรด้วย fallback executor (deterministic, ไม่ต่อเน็ต)

---

## ตำแหน่งใน ecosystem dPRO

```
Vinit (CEO) → d_Jarvis (หน้า) → d_CEO (สมอง) → delegate → DEP-PM (Team Lead R&D)
                                                              ↑ รายงานผล → QC gate ↑
```

DEP-PM คือแพลตฟอร์มที่**ทีม R&D ใช้ลงมือทำงานพัฒนาจริง** — d_CEO สั่งงานทีมได้แต่ผลิตได้แค่ข้อความ
(orchestrator ของเขาเรียก LLM แบบไม่มี tool) ส่วนที่นี่แตกงาน เขียนงาน ตรวจงาน และ deploy ได้จริง
รายละเอียด + กติกา "ไม่ทำระบบ task ซ้อน" อยู่ใน [`AGENTS.md`](./AGENTS.md) §3.1

---

## เอกสาร

| ไฟล์ | เนื้อหา |
|---|---|
| [`AGENTS.md`](./AGENTS.md) | **ต้นฉบับกติกาสำหรับ AI agent ทุกตัว** (CLAUDE.md / GEMINI.md เป็นแค่ pointer) |
| [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) | สถานะล่าสุด + งานถัดไป — อ่านก่อนเริ่มงานเสมอ |
| [`CHANGELOG.md`](./CHANGELOG.md) | ประวัติการเปลี่ยนแปลง |
| [`docs/PROJECT_OVERVIEW.md`](./docs/PROJECT_OVERVIEW.md) | purpose, scope, non-goals, success criteria |
| [`docs/DEVELOPMENT_PLAN.md`](./docs/DEVELOPMENT_PLAN.md) | แผน 4 สปรินต์ + **ADR-01..04** + data model + API contract |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | HLA + diagrams + tech stack พร้อมเหตุผลที่เลือก |
| [`docs/SYSTEM_DOCUMENTATION.md`](./docs/SYSTEM_DOCUMENTATION.md) | วิเคราะห์ทุกโมดูล + business logic + technical debt |
| [`docs/API.md`](./docs/API.md) · [`docs/DATABASE.md`](./docs/DATABASE.md) | ทุก endpoint · ER + ทุกตาราง + migrations |
| [`docs/SECURITY.md`](./docs/SECURITY.md) · [`docs/RISK_REGISTER.md`](./docs/RISK_REGISTER.md) | threat model + security gate · ทะเบียนความเสี่ยง |
| [`docs/runbook.md`](./docs/runbook.md) | วิธีรัน/เปิดฟีเจอร์/แก้ปัญหา + UAT checklist |
| [`docs/AI_AGENT_GUIDE.md`](./docs/AI_AGENT_GUIDE.md) | กติกาเชิงลึก "แตะโค้ดยังไงไม่พัง" |

**เอกสารต้นทาง (read-only ห้ามแก้):** `DEP-PM Platform Blueprint v1.0.html` · `DEP v3.0 Master Plan.html` · `ai-dev-team-complete.html`

---

## ข้อควรรู้ก่อนแตะโค้ด

- **ห้าม set `task.status` ตรง ๆ** — ผ่าน `state_machine.transition()` เท่านั้น (ผิดลำดับ → 409)
- **ห้าม INSERT `agent_messages` ตรง ๆ** — ผ่าน `bus.publish()` เท่านั้น
- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ ห้ามลบ** — สำรองก่อนแตะเสมอ
- แก้ schema/สถานะฝั่ง backend → แก้ `frontend/src/lib/types.ts` ในคอมมิตเดียวกัน
- **ยังไม่มี authentication** — ห้าม expose พอร์ตออกนอกเครื่องจนกว่าจะผ่าน security gate ใน `docs/SECURITY.md`
