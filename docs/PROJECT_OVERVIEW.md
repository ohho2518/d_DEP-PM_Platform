# PROJECT_OVERVIEW.md — DEP-PM Platform

**Status:** Active (MVP ครบ 4 สปรินต์ — อยู่ระหว่างต่อเข้า ecosystem)
**Last updated:** 2026-08-02

---

## 1. Purpose

DEP-PM คือแพลตฟอร์มบริหารโปรเจกต์แบบ AI-Native ที่ให้ **มนุษย์และ AI Agent ทำงานอยู่บนบอร์ดเดียวกัน** — รับ requirement เป็นภาษาคน แล้วให้ AI แตกเป็นงานย่อยพร้อมผังพึ่งพา มอบหมายให้ agent หรือคน ติดตามสถานะบน Kanban และ deploy อัตโนมัติเมื่องานผ่าน review โดยทุกอย่างที่ agent ทำถูกบันทึกให้ตรวจย้อนหลังได้ทั้งหมด

ในระบบนิเวศ dPRO ระบบนี้ทำหน้าที่เป็น **Team Lead R&D** — ปลายทางที่งานพัฒนาซอฟต์แวร์ซึ่งถูก delegate ลงมาจาก d_CEO ถูกลงมือทำจริง (ดู `AGENTS.md` §3.1)

## 2. Business Goal

ลดเวลาจาก **Requirement → First Deploy ลง 50%** เทียบ workflow เดิมของทีม dPRO โดยให้ AI รับงาน routine (แตกงาน, implement, review รอบแรก) และให้คนใช้เวลากับการตัดสินใจเฉพาะจุดที่ระบบยกให้ (escalate)

## 3. Problems Solved

| # | Problem today | How this system solves it |
|---|---|---|
| 1 | แตกงานจาก requirement กินเวลา PM มาก | PM Agent แตกเป็น Task Plan JSON อัตโนมัติ พร้อม priority / estimate / `depends_on` |
| 2 | งานที่มอบให้ AI ไม่มี audit trail | ทุก state change ลง `audit_log` · ทุกข้อความ agent ลง `agent_messages` · ทุก routing decision ถูก log |
| 3 | Dashboard มี blind spot ระหว่างงานคนกับงาน AI | ทุก task ไม่ว่าใครทำ ไหลผ่าน State Machine เดียวกัน |
| 4 | คุณภาพงาน AI ไม่แน่นอน | Reviewer persona ตรวจทุกงาน + Escalation Rule (reject 2 ครั้ง → คนรับช่วง) |
| 5 | สั่ง deploy เองทุกครั้งหลังงานเสร็จ | task ผ่าน review → staging deploy อัตโนมัติ; production ยังต้องคนกด (Manual Gate) |

## 4. Target Users

| User type | What they need | How often they use it |
|---|---|---|
| เจ้าของ/หัวหน้าทีม R&D (Vinit) | เห็นภาพรวมทุกโปรเจกต์ ยืนยัน scope ตัดสินงานที่ escalate | ทุกวันทำงาน |
| ทีม R&D ที่รับงาน delegate จาก d_CEO | รับงาน แตกงาน ปล่อย agent ทำ แล้วรายงานผลกลับ | ต่อรอบงานที่ถูกมอบหมาย |
| AI Agent (PM / Dev / Senior Architect / Reviewer) | อ่าน spec ทำงาน ส่งงาน รีวิว ผ่าน API เดียวกับคน | ตลอดเวลาที่ orchestrator รัน |

## 5. Scope

**In scope**

- Project Intake — New Project เต็มรูปแบบ, Existing/Brownfield ใช้ stub (ADR-02)
- AI Task Breakdown + ยืนยัน scope โดยคน
- Task Orchestration: routing → execute → review → revision → escalation
- Kanban Board · Task detail · Inter-Agent Message Log · Portfolio · Deployments view
- Automated Deploy ผ่าน GitHub `repository_dispatch` (staging auto / production manual)
- Solo Mode (Claude ทุกบทบาท) และ Team Mode (หลาย provider) สลับด้วย config

**Out of scope (Non-goals)**

- Billing / Invoicing และ agent marketplace ภายนอก
- Mobile native app (ใช้ responsive web)
- Knowledge Graph จริง + Metadata Engine จริง (รอ DEP v3.0 Phase 2+ — ตอนนี้เป็น stub)
- Authentication / RBAC (MVP เป็น single-user บน localhost — จะทำพร้อมทั้ง ecosystem)
- Realtime WebSocket (ใช้ polling ตาม ADR-04)
- **ทะเบียนงานระดับธุรกิจ** — เป็นของ d_CEO เท่านั้น ที่นี่เก็บเฉพาะ task ย่อยของงานพัฒนา

## 6. Expected Benefits

- เวลาจาก requirement ถึง deploy แรกลดลงครึ่งหนึ่ง
- งาน AI ทุกชิ้นตรวจย้อนหลังได้ 100% (ใครทำ ทำอะไร ตอนไหน ด้วยเหตุผลอะไร)
- คนเข้ามาแตะเฉพาะงานที่ระบบยกให้ ไม่ต้องนั่งเฝ้าทุก task
- ต้นทุน token ต่อ task วัดได้จริง (เก็บสะสมบน `tasks.tokens_input/tokens_output`)

## 7. Assumptions

_ทุกข้อคือความเสี่ยงจนกว่าจะพิสูจน์ — ดู `RISK_REGISTER.md`_

1. DEP v3.0 Metadata Engine **ยังไม่มีโค้ดจริง** → Brownfield scan เป็น mock ตลอด MVP (ADR-02)
2. ผู้ใช้คนเดียว รันบนเครื่อง dev Windows → ยังไม่ต้องมี auth/Docker/PostgreSQL
3. Claude API key เดียวพอสำหรับ Solo Mode (ทุก persona ใช้ key เดียว ต่างกันที่ system prompt)
4. โค้ดที่เขียนตาม ADR-01 จะย้าย SQLite → PostgreSQL ได้โดยไม่แก้ query (**ยังไม่พิสูจน์** — ยังไม่ได้รัน suite บน PG)
5. งานที่ d_CEO delegate ลงมาจะแมปเป็น "1 task ธุรกิจ = 1 project ที่นี่" ได้พอดี

## 8. Constraints

| Type | Constraint |
|---|---|
| Budget | ต้นทุน LLM ต่อ task ต้องคุมได้ — `MAX_TOKENS_PER_TASK` + token counter ต่อ task |
| Timeline | MVP 4 สปรินต์ (~8 สัปดาห์) — เสร็จแล้ว งานถัดไปคือการต่อเข้า ecosystem |
| Technical | Schema ต้อง portable SQLite↔PostgreSQL (ห้าม dialect-specific SQL) · ไม่เพิ่ม infrastructure ก่อนจำเป็น · **พอร์ต 8500** (8000 เป็นของ d_CEO) |
| Regulatory / Legal | PDPA — ห้ามให้ข้อมูลส่วนบุคคล/ความลับหลุดเข้า prompt (ยังไม่มี masking — เป็นงานก่อนใช้กับข้อมูลลูกค้าจริง) |
| Team | คนเดียว + AI agents — เลือกสถาปัตยกรรมที่ debug ง่ายกว่าเสมอ |

## 9. Design Philosophy

1. **Auditable by default** — ทุกอย่างที่ agent ทำต้องตรวจย้อนหลังได้ (`audit_log` + `agent_messages` เป็น source of truth)
2. **Interface ก่อน implementation** — ส่วนที่ยังไม่พร้อมล็อกเป็น interface + stub เพื่อเสียบของจริงภายหลังโดยไม่แก้ผู้เรียก
3. **Graceful degradation** — ไม่มี API key ระบบยังเดินครบวงจร และบอกผู้ใช้ชัดว่าอยู่โหมด fallback
4. **Upgrade path ชัดทุก ADR** — เริ่มเบา (SQLite, in-process bus, polling) แต่เขียนเส้นทางขึ้นสเปกเต็มไว้ล่วงหน้า
5. **ไม่สร้าง source of truth ซ้อน** — งานระดับธุรกิจอยู่ที่ d_CEO, สถานะโปรเจกต์อยู่ที่ d_OS_Lite, ความจริงธุรกิจอยู่ที่ `CANONICAL_FACTS.md`

## 10. Success Criteria

| KPI | เป้าหมาย | สถานะ |
|---|---|---|
| Time from Requirement → First Deploy | ลดลง 50% เทียบ workflow เดิม | ยังไม่วัด (ต้องมีข้อมูลใช้งานจริงต่อเนื่อง) |
| Task auto-routing accuracy | > 90% ไม่ต้อง reassign มือ | ยังไม่วัด (routing decision ถูก log ไว้แล้ว) |
| Escalation rate | < 10% ของ task ทั้งหมด | ยังไม่วัด — UAT พบว่า task ที่ต้องการ artifact จริงจะ escalate เสมอ |
| Deploy success rate (staging → prod) | > 95% | ยังไม่วัด (dispatch จริงผ่านแล้ว 1 ครั้ง, callback ยังไม่ครบวงจร) |
| **รับงานจาก d_CEO ได้ครบวงจร** | สั่งผ่าน Telegram → งานเดินที่ DEP-PM → รายงานกลับเข้า QC gate | **ยังไม่ทำ — เป้าหมายถัดไป** |
