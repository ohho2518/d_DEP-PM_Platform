# RISK_REGISTER.md — DEP-PM Platform

**Last updated:** 2026-08-02
**ที่มา:** `DEVELOPMENT_PLAN.md` §7 (risk เดิม 7 ข้อ) + `SYSTEM_DOCUMENTATION.md` §22 (technical debt) + สิ่งที่พบระหว่าง UAT และการตรวจ ecosystem

---

## Severity Scale

| Level | Meaning | Response |
|---|---|---|
| 🔴 Critical | Data loss, security breach, or system unusable | Fix before anything else |
| 🟠 High | Major feature broken or serious performance problem | Fix this sprint |
| 🟡 Medium | Degraded experience, technical debt with real cost | Schedule it |
| 🟢 Low | Cosmetic or minor cleanup | Fix when convenient |

---

## Active Risks

| # | Severity | Risk | Impact if it happens | Likelihood | Mitigation | Status |
|---|---|---|---|---|---|---|
| 1 | 🟡 | **CI callback `PATCH /api/deployments/:id` ไม่มี authentication** | ใครก็ตามที่ยิงถึงพอร์ตได้ เลื่อน task เป็น `deployed` ปลอมได้ | ต่ำตราบใดที่ bind localhost | **แก้แล้ว 2026-08-03:** shared secret ผ่าน header `X-DEP-PM-Secret` (`DEPLOY_CALLBACK_SECRET`) · ⚠️ **ไม่ตั้งค่า = ไม่ตรวจ** ตามค่าปริยาย dev — ต้องตั้งจริงก่อน expose พอร์ต | **Mitigated (ต้องตั้งค่า)** |
| 2 | 🔴 | **ข้อมูลอ่อนไหวหลุดเข้า prompt (PDPA)** | ข้อมูลลูกค้าไปอยู่ที่ผู้ให้บริการ LLM | ต่ำตอนนี้ (ยังไม่ใช้ข้อมูลลูกค้าจริง) | กติกาห้าม secrets ใน task spec · **ยังไม่มี field masking** (ต้องมีก่อนใช้กับข้อมูลจริง) | **Open** |
| 3 | 🟢 | ~~**`/run` synchronous + ไม่ thread-safe ต่อโปรเจกต์**~~ | UX ค้างยาว · ยิงซ้อนโปรเจกต์เดียวกัน = สถานะเพี้ยน · **บล็อกการรับงานจาก d_CEO** (ของเขาวัดจริง 1 task = 192 วิ) | — | **แก้แล้ว 2026-08-03 (Phase 2):** 202 + `run_id` + thread เบื้องหลัง + lock ต่อโปรเจกต์ (ซ้อน = 409) + `GET /:id/run` · เหลือข้อจำกัด: ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียว (restart = ประวัติหาย ผลงานไม่หาย) และยังไม่มีปุ่มยกเลิกรอบรัน | **Mitigated** |
| 4 | 🟠 | **ต้นทุน API เกินงบเมื่อเปิด Team Mode** | ค่าใช้จ่ายบานปลาย | กลาง | `MAX_TOKENS_PER_TASK` + เก็บ token ต่อ task แล้ว · **ยังไม่มีงบรวมต่อโปรเจกต์/alert** | **Partially mitigated** |
| 5 | 🟢 | ~~**OpenAI/Gemini executors ไม่เคยรันกับ service จริง**~~ | Team Mode อาจพังตอนใช้จริง | — | **ยิงจริงครบ 3 เจ้าแล้ว 2026-08-14** ผ่านปุ่มทดสอบของหน้า `/settings`: Anthropic ✅ · **OpenAI `gpt-5.2` ✅ (3.4 วิ)** · **Gemini ✅ (1.6 วิ) หลังแก้ชื่อรุ่น** — `gemini-3-pro` ที่ตั้งไว้เดิมไม่มีอยู่จริง (404) ส่วนคีย์ใช้ได้มาตลอด · เหลือ: token accounting ยังไม่วัดกับงานเต็มรอบ | **Mitigated** |
| 5.3 | 🟡 | **ชื่อรุ่นของผู้ให้บริการเปลี่ยน/ถูกปิดโดยที่เราไม่รู้** | ตั้งไว้ในค่าปริยาย/`.env` แล้วพังเงียบ ๆ ตอนเรียกจริง (404) · เสียเวลาไล่ผิดทางเพราะดูเหมือนปัญหาคีย์ | สูง — Google ปิดรุ่น 2.5 สำหรับผู้ใช้ใหม่ และ `gemini-3-pro` ไม่เคยมี | `classify_error` แยก 404 เป็น `request` (ไม่สลับเจ้าให้เปลืองเปล่า) · ปุ่มทดสอบที่ `/settings` บอกชนิดปัญหาให้เห็นทันที · runbook §4.2 มีคำสั่ง `ListModels` | **Monitored** |
| 5.1 | 🔴 | **ผู้ให้บริการ AI เจ้าเดียวล่ม = งานหยุดทั้งระบบ** (เหตุจริง 2026-08-06 เครดิตหมด → ทั้ง eco หยุดเงียบ) | รอบรันล้มกลางทาง · task ค้าง · แยกไม่ออกว่าบัญชีพังหรืองานไม่ผ่าน | เกิดมาแล้ว 1 ครั้ง | **แก้แล้ว 2026-08-14:** ลำดับสำรองจาก env + แยกชนิด error (สลับ/ลองซ้ำ/หยุด) + ติดป้ายว่าใครทำ + ทุกเจ้าล่ม → task `escalated` พร้อมเหตุ ไม่ค้าง `in_progress` · ⚠️ **คีย์ยังใช้ร่วมกันข้ามรีโป** (บัญชีหมดเครดิต = ทุกรีโปเจอพร้อมกันเหมือนเดิม) — ต้องแยกคีย์ที่คอนโซลผู้ให้บริการ | **Mitigated (เหลือแยกคีย์)** |
| 5.2 | 🟢 | ~~**หน้า `/settings` แก้คีย์ได้โดยไม่มี authentication**~~ | ใครที่ยิงถึงพอร์ตได้ เปลี่ยน/ลบคีย์ของระบบได้ | — | **ปิดแล้ว 2026-08-14:** `API_TOKEN` + header `X-DEP-PM-Token` บังคับทุก `/api/*` (ยืนยันด้วยการยิงจริง: ไม่แนบ → 401 · แนบถูก → 200) · คีย์ยังไม่เคยออกทาง API แบบเต็ม · ⚠️ เหลือข้อจำกัดที่ต้องรู้: token ฝั่ง frontend อยู่ใน bundle ⇒ **กันคนนอกยิงพอร์ต ไม่ได้กันคนที่ใช้เครื่องนี้** | **Mitigated** |
| 6 | 🟢 | ~~**SQLite → PostgreSQL พฤติกรรมต่างกัน** (JSON query, concurrency)~~ | ย้ายขึ้น staging แล้วพัง | — | **ปิด DoD แล้ว 2026-08-03:** migration + **pytest 107/107 ผ่านบน PostgreSQL 17.10** (`TEST_DATABASE_URL=postgresql+psycopg://…`) · DoD จับบั๊กจริงได้ 1 ตัว: seed migration ใช้ `sa.String` แทน `GUID` ทำให้ upgrade บน PG ตายทั้งชุด (แก้แล้ว) | **Mitigated** |
| 7 | 🟡 | **DEP v3.0 Engine จริงยังไม่มี** — Brownfield ใช้ stub | ผู้ใช้เข้าใจผิดว่า scan ได้จริง | สูง (stub อยู่นาน) | ตอบ `is_mock: true` + prefix `[mock]` ทุก finding · interface ล็อกไว้แล้ว (ADR-02) | **Mitigated** |
| 8 | 🟡 | **`types.ts` sync ด้วยมือ** | contract drift เงียบระหว่าง backend/frontend | กลาง | กติกา "แก้ backend ต้องแก้ types.ts คอมมิตเดียวกัน" · แผน: openapi-typescript codegen | **Open** |
| 9 | 🟡 | **Agent มอบหมายงานผิดประเภท** (routing heuristic เป็น keyword) | งานไปผิด persona คุณภาพตก | กลาง | log routing decision ทุกครั้งพร้อม matched keyword → ปรับ rules จากข้อมูลจริง | **Monitored** |
| 10 | 🟡 | **Task ที่ acceptance criteria ต้องการ artifact จริงจะ escalate เสมอ** | escalation rate สูงเกินเป้า < 10% | สูง (พบจริงใน UAT) | เขียน spec ให้ deliverable เป็นเอกสาร/โค้ด หรือให้คนรับ task ประเภท infra เอง | **Known behavior** |
| 11 | 🟡 | **นับ total แบบโหลดทุกแถว / `_next_runnable` re-query ต่อ task** | ช้าเมื่อข้อมูลโต | ต่ำที่ scale ปัจจุบัน | แก้ตอนย้าย PostgreSQL (COUNT(*) + window function) | **Accepted** |
| 12 | 🟡 | **ไม่มี structured logging / error tracking** | debug ปัญหา production ยาก | กลางเมื่อ deploy จริง | มี audit_log + agent_messages ใน DB เป็นทางเลือก · แผนหลัง MVP | **Open** |
| 13 | 🟢 | **PM Agent คืน JSON parse ไม่ได้** | breakdown ล้ม | ต่ำ | retry 1 ครั้ง → fallback plan (ไม่ 500 เด็ดขาด) | **Mitigated** |
| 14 | 🟢 | **Auto-deploy พังหน้า production** | ระบบลูกค้าล่ม | ต่ำ | auto path hardcode `staging` เท่านั้น · production ต้องคนสั่งผ่าน POST + แนะนำ GitHub environment protection | **Mitigated** |

### Closed (2026-08-02)

| # | Risk | ปิดยังไง |
|---|---|---|
| C1 | **งานพัฒนา ~1 เดือนค้างใน working tree ไม่เคย commit** | commit `9cd76d6` (สำรอง DB ก่อนตาม WORKING_RULES) |
| C2 | **พอร์ต 8500 vs 8000 ชนกับ d_CEO** — เอกสารบอกให้รันที่ :8000 ซึ่งรันไม่ขึ้นจริง | ย้ายทั้งระบบเป็น 8500 + จดตาราง port ของ ecosystem ไว้ใน `AGENTS.md` §3.1 และ `runbook.md` |
| C3 | **AGENTS.md ประกาศตัวเป็นต้นฉบับแต่เนื้อหาว่าง** (`Need confirmation` ทั้งไฟล์) ขณะที่ของจริงอยู่ใน CLAUDE.md | ย้ายเนื้อหาจริงเข้า AGENTS.md · CLAUDE.md/GEMINI.md เป็น pointer |
| C4 | Reviewer parse-fail = auto-approve (งานไม่ถูกตรวจหลุดเป็น done) | retry 1 → reject → เข้า revision/escalation ปกติ |
| C5 | `depends_on` ไม่มี referential integrity (dangling id ทำให้ task ไม่มีวัน runnable แบบเงียบ) | validate ตอน create (400) + `DELETE /api/tasks/:id` ปฏิเสธถ้ามีตัวอ้าง (409) |
| C6 | ไม่มี token-usage tracking ต่อ task | `tasks.tokens_input/tokens_output` สะสมทุก call ทุก provider |

---

## Security Checklist

- [x] No hardcoded secrets anywhere in code or history — `.env` gitignored, `.env.example` เป็น placeholder
- [x] All user input validated server-side — Pydantic ทุก endpoint + State Machine กัน transition ผิด
- [x] SQL parameterized — ORM ล้วน ห้าม raw SQL (ADR-01)
- [ ] **Authentication on every protected route** — ยังไม่มี auth เลย (by design, MVP single-user)
- [ ] **Authorization checked per resource** — มาพร้อม auth
- [ ] Passwords hashed — N/A (ยังไม่มีระบบผู้ใช้)
- [x] Secrets in environment variables, never in the repo
- [ ] Dependencies scanned for known CVEs — ยังไม่ได้ทำ
- [x] Internal errors never exposed to end users — FastAPI default + fallback ทุกเส้นทาง agent
- [ ] **Data backed up, and restore tested at least once** — สำรอง `dep_pm.db` เป็นไฟล์แล้ว แต่ **ยังไม่เคยทดสอบ restore**

## Performance Checklist

- [x] No N+1 queries ในเส้นทางหลัก (deployments list เติมชื่อแบบ batch แล้ว)
- [ ] Indexes on all columns used in `WHERE`/`JOIN`/`ORDER BY` — ยังไม่ได้ตรวจครบ (ดู `DATABASE.md`)
- [x] Large result sets paginated — `limit` clamp 1..200 ทุก list endpoint
- [x] No blocking work on the UI thread — polling หยุดเมื่อแท็บไม่ active
- [x] Connections closed properly — `get_db()` yield-close ต่อ request
- [ ] Caching used where reads dominate — ไม่มี (ข้อมูลเปลี่ยนตลอด + single-user)
- [x] **`/run` ไม่ block request** — 202 + `run_id` แล้วรันเบื้องหลัง (Phase 2, วัดจริง ~10 ms ต่อ request)

---

## Assumptions That Could Break

| Assumption | What breaks if it's wrong | How to verify |
|---|---|---|
| โค้ดพอร์ตข้าม SQLite→PostgreSQL ได้โดยไม่แก้ query (ADR-01) | ย้าย staging ไม่ได้ ต้องแก้ query ทั้งระบบ | รัน test suite เต็มบน PostgreSQL (DoD ของ ADR-01) |
| Claude key เดียวพอสำหรับทุก persona ใน Solo Mode | คุณภาพ review ต่ำเพราะ reviewer เป็นโมเดลเดียวกับผู้ทำงาน | เทียบผล Solo vs Team Mode บนงานชุดเดียวกัน |
| Reviewer persona ตัดสินคุณภาพได้ใกล้เคียงคน | งานคุณภาพต่ำหลุดเป็น done หรือ escalate เกินจำเป็น | สุ่มตรวจงานที่ผ่าน review ด้วยคน เทียบอัตราเห็นตรงกัน |
| "1 task ธุรกิจใน d_CEO = 1 project ที่นี่" แมปได้พอดี | งานจาก d_CEO ลงมาแล้วแตกไม่ลงตัว ต้องมีทะเบียนซ้อน | ลองรับงานจริง 3-5 งานแล้ววัดว่าต้องแก้มือกี่ครั้ง |
| ผู้ใช้คนเดียว ไม่ต้องมี auth | ระบบถูกยิงจากเครือข่ายเมื่อเผลอ expose พอร์ต | ตรวจว่า bind `127.0.0.1` เสมอ + ทำ security gate ก่อน deploy |
