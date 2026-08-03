# PROJECT_STATUS.md — DEP-PM Platform

> ## 📣 เปิดโปรเจกต์นี้แล้ว **อ่านตรงนี้ก่อน** — ใบสั่งงานรอบตรวจทั้ง eco 2026-08-03
>
> ### ✅ ของเมื่อเช้าปิดไปเองแล้ว 2 ข้อ (ตรวจ 3 ส.ค. 13:45)
> · **3.2 ยืนยันแล้วว่าใช้ได้จริง** — d_CEO ปิดเส้น `PATCH → qc_review` ให้แล้ว (contract **v6**) และ
> **รายงาน UAT รอบ 2 ของคุณ (`4936aa9e`) เดินผ่าน QC เป็น `done` เองโดยไม่มีใครกดอะไร** ✅
> · **3.3 ไฟล์ Phase 2 ที่ค้าง commit — เข้า git หมดแล้ว** ✅
>
> ### 🔴 ที่ยังเหลือ
> 1. **งานเก่า `d89c03a8` ยังค้าง `qc_review`** — รอบนั้น escalated 1 (review ไม่ผ่าน 2 ครั้ง:
>    "รวมเนื้อหาและจัดรูปแบบเป็น Markdown ฉบับสมบูรณ์") + ค้างรอตัวข้างบน 1 ·
>    **v6 ไม่ย้อนไปแตะงานเก่า** ⇒ ต้องรับช่วงงานที่ตันแล้วรายงานรอบใหม่ (ไม่ใช่แค่ยิง `/qc` ซ้ำ)
> 2. 🟠 **ตารางพอร์ตถูกก๊อบไว้ 3 ชุด** (`AGENTS.md` · `docs/runbook.md` · `PROJECT_STATUS.md`) —
>    ชี้มาที่ **`D:\Dev_Proj\6_KM\d_InnoHub\_CANON\SERVICE_PORTS.md`** แทน (ทะเบียนกลางตัวใหม่
>    ที่ตั้งขึ้นเพราะเหตุพอร์ต 8400 ชนพอดี) · เพิ่มบล็อก canon ใน `AGENTS.md` ด้วย
> 
> **ใบสั่งงานเต็ม:** `D:\Dev_Proj\0_CORE\d_CEO\docs\ORDER_TICKET_2026-08-03.md` → Ticket #3
> ทำข้อไหนเสร็จ → ติ๊ก `[x]` ในใบ + อัปเดตไฟล์นี้ · ไม่เห็นด้วยข้อไหน แย้งได้ในใบเดียวกัน
> (ใบนี้ออกจากรอบตรวจของเลขา — **ทุกข้อมีหลักฐานที่วัดจากของจริง** ไม่ได้มาจากการอ่านเอกสาร)

---

> อัปเดตล่าสุด: 2026-08-03 | สถานะโดยรวม: **Phase 0-3a เสร็จ · UAT ผ่าน QC gate จริง**
> — วงจร Vinit → เลขา → DEP-PM → QC **เดินครบและผ่านการตรวจแล้ว** (`done 8/8`, verdict `PASS`)
> · ปิดความเสี่ยงค้าง 2 ข้อในวันเดียว: CI callback auth (Risk #1) + **test suite บน
> PostgreSQL 107/107** (DoD ของ ADR-01) · หยุดรอบรันกลางทางได้แล้ว
> · **งานถัดไป: ห้าม agent กุหลักฐาน** (QC จับได้ — Next Tasks #1)

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (สำรอง DB ล่าสุด `BackUp/Phase0Cleanup_20260802_224442/`
  · Phase 2 ไม่แตะ schema จึงสำรองเฉพาะไฟล์โค้ด: `BackUp/Phase2AsyncRun_20260803_091552/`)
- **พอร์ตของ DEP-PM = 8500** — `uvicorn app.main:app --reload --port 8500`
  · 📌 ทะเบียนพอร์ตของทั้ง eco อยู่ที่ `_CANON\SERVICE_PORTS.md` (ไม่ก๊อบตารางมาไว้ที่นี่แล้ว —
  ใบสั่งงาน 3 ส.ค. Ticket 3.5) · `8000` d_CEO และ `8400` d_Jarvis web **ห้ามหยุด**
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO (`ohho2518/d_DEP-PM_Platform`)
- โปรเจกต์ในระบบ: "Demo: Booking API" (4 done), "d_ACC" (17 backlog), "Deploy UAT",
  + งานทดสอบจากเลขา 2 ตัว (`a07f1fb2` ของ 2 ส.ค., `7ffa2d4f` ของ 3 ส.ค. — เก็บไว้เป็นหลักฐาน UAT)
- DB migrate เป็น head `e5a91c73b204` แล้ว · uvicorn/next ไม่ได้รันค้างไว้ (สตาร์ตเองตาม runbook)
- 🐘 **มี Docker container `dep-pm-pg-test` (PostgreSQL 17, พอร์ต 5432) รันค้างอยู่** —
  ตั้งใจเก็บไว้ให้รัน suite บน PG ซ้ำได้เร็ว (`TEST_DATABASE_URL=postgresql+psycopg://postgres:deppmtest@127.0.0.1:5432/dep_pm_pytest pytest`)
  · ไม่ใช้แล้วสั่ง `docker stop dep-pm-pg-test` ได้ · **ไม่ใช่ DB ของงานจริง** (ของจริงยังเป็น SQLite)

## ตำแหน่งใน ecosystem (ยืนยันโดย Vinit 2026-08-02)

```
Vinit (CEO) → d_Jarvis (หน้า) → d_CEO (สมอง) → delegate → DEP-PM (Team Lead R&D)
                                                    ↑ รายงานผล → QC gate → Vinit เคาะ
```

- ผู้สั่งงานคือ Vinit เสมอ — d_CEO เป็นตัวแปลงคำสั่งเป็น task แล้วกระจายให้ทีม ไม่ใช่เจ้านายของรีโปนี้
- DEP-PM ไม่ซ้ำกับ d_CEO เพราะ orchestrator ของเขาเรียก LLM **แบบไม่มี tool** → ได้แค่ข้อความ
  ส่วนที่นี่แตกงาน เขียนงาน ตรวจงาน และ deploy ได้จริง
- ยึด **1 task ธุรกิจใน d_CEO = 1 project ที่นี่** (ไม่สร้างทะเบียนงานธุรกิจซ้อน)

## Completed Work

### ใบสั่งงาน 2026-08-03 Ticket #3 (จากรอบตรวจของเลขา)

| ข้อ | สถานะ | หลักฐาน |
|---|---|---|
| 3.1 งานค้าง `d89c03a8` | ✅ **ทำงานจบแล้ว** | ตีกลับ `87a8d3f2` เข้าคิว → รัน 2 งาน **done ทั้งคู่** (163 วิ) → รายงานรอบใหม่ 22,488 ตัวอักษร · **แต่ฝั่งเลขายังค้าง `qc_review`** ดูหมายเหตุล่าง |
| 3.2 ตรวจเงื่อนไข v6 | ✅ **ยืนยัน** | `report_project` ยิง **PATCH เดียว** พร้อม `status`+`output` — มีเทสต์ล็อกไว้ · เพิ่ม `qc_task()` + `POST /api/ceo/qc/:id` |
| 3.3 ไฟล์ค้าง commit | ✅ | อยู่ใน `f8848f0` (Phase 2) ตั้งแต่เช้า |
| 3.4 รายงานอ้าง `:8400` | ✅ **ยืนยัน** | โค้ดใช้ `:8500` · grep `backend/app`+`frontend/src` ไม่เหลือ 8400 · ของเก่าใน DB ปล่อยไว้ |
| 3.5 ตารางพอร์ต 3 ชุด | ✅ | ชี้ `_CANON\SERVICE_PORTS.md` ครบ + เพิ่มในบล็อก canon ของ AGENTS.md |

> ⚠️ **3.1 ยังไม่ปิดสมบูรณ์ — ต้องให้เจ้าของสั่ง:** งานฝั่งเราเสร็จและรายงานไปแล้ว แต่ task
> `d89c03a8` **ค้าง `qc_review` ต่อ** เพราะ v6 ยิง QC เฉพาะตอน "เปลี่ยน**เข้า**" `qc_review`
> ส่วนงานนี้ค้างสถานะนั้นมาตั้งแต่ 2 ส.ค. (ตรงกับใบสั่งงานข้อ 1.2b ที่เขียนว่า v6 ไม่ย้อนแตะงานเก่า)
> ⇒ ปลดได้ด้วย `POST /api/ceo/qc/a07f1fb2-9c9b-4cf0-aec3-247283ed5eb4` (ปุ่มที่เพิ่งทำในข้อ 3.2)
> · **ยังไม่ยิงเอง** — 1 รอบ QC มีราคาราวครึ่งของค่างานหนึ่งชิ้น และใบสั่งงานระบุว่า "รอเจ้าของ"

### สิ่งที่ต้องเพิ่มเพื่อให้ 3.1 ทำได้ — `escalated → planned`

- เดิม `escalated` ไปได้แค่ `in_progress` (คนลงมือเอง) แต่ orchestrator หยิบเฉพาะ `planned`
  ⇒ **งานที่ escalate แล้วให้ agent ลองใหม่ไม่ได้เลย** · เพิ่มทางที่สองครบ 6 จุดตามกติกา §13
- `revision_count` **ไม่รีเซ็ต** โดยตั้งใจ — ตีกลับแล้วยังไม่ผ่าน = escalate ทันทีรอบเดียว
- พิสูจน์กับงานจริง: `87a8d3f2` ที่เคยถูกปฏิเสธ 2 รอบ (ผลิตแต่ `[[placeholder]]`)
  **ผ่านตั้งแต่ครั้งแรกหลังตีกลับ** เพราะได้ผลงานของ 3 งานต้นทางไปด้วย (Phase 3a)

### ปุ่มหยุดรอบรัน · PostgreSQL DoD · ทบทวน escalation (2026-08-03)

- **⏹ ยกเลิกรอบรัน:** `POST /:id/run/cancel` + ปุ่มบนบอร์ด · engine รับ `should_continue`
  ถามก่อนหยิบ task ถัดไป → **หยุดระหว่างช่อง ไม่ตัดกลาง task** · สถานะ `cancelled`
  ไม่รายงานกลับเลขา · lock ถูกปลด กด Run ใหม่ทำต่อได้
- **🐘 ปิด DoD ของ ADR-01:** conftest รับ `TEST_DATABASE_URL` → **pytest 107/107 ผ่านบน
  PostgreSQL 17.10** และบน SQLite เหมือนเดิม
  · 🐛 **จับบั๊กได้ทันทีที่ทำ:** seed migration `b2f1c0d3e4a5` ใช้ `sa.String` กับคอลัมน์ที่
  เป็น native `uuid` บน PG → `alembic upgrade head` **ตายทั้งชุด** (แก้เป็น `GUID`)
  · ⚠️ **แก้ migration ที่ apply แล้ว** ซึ่งปกติกติกาห้าม — ไม่มีทางอื่นเพราะตัวที่พังรันก่อน
  migration ใหม่เสมอ · ผลบน SQLite เหมือนเดิมทุกไบต์ (ยืนยันด้วย suite ทั้งชุดสองเอนจิน)
- **📊 escalation จากข้อมูลจริง:** 23 งานที่จบแล้ว · escalated 2 = **8.7%** · ทั้ง 2 ครั้ง
  สาเหตุเดียวกันคือไม่ได้รับผลงานของงานก่อนหน้า → **"reviewer เข้มเกินไป" เป็นข้อสรุปที่ผิด**
  (สรุปเต็มใน `runbook` §7) · หลัง Phase 3a escalated 0 · revision เฉลี่ย 0.67 → 0.12
- **📨 `docs/REQUEST_TO_CEO.md`** — จดหมายพร้อมส่งถึง session ของ d_CEO (ยังไม่ได้ส่ง)

### UAT รอบ 2 — **QC ของเลขาตอบ PASS** (2026-08-03)

d_CEO task `4936aa9e` → DEP-PM project `4d8004ff` — โจทย์เดียวกับรอบแรกทุกตัวอักษร

| | รอบ 1 (ก่อน Phase 3a) | รอบ 2 (หลัง Phase 3a) |
|---|---|---|
| tasks | 6 (กราฟ 3 ชั้น) | **8 (กราฟ 4 ชั้น)** |
| ผลรัน | done 5 · **escalated 1** | **done 8 · escalated 0** |
| เวลา | 507 วิ | 613 วิ |
| งาน "รวมเนื้อหา" (depend 3) | ผลิต `[[placeholder]]` → ปฏิเสธ 2 รอบ → escalated | **ผ่านรอบแรก 0 revision** |
| รายงานถึงเลขา | 2,652 ตัวอักษร (สรุปสถานะ) | **31,820 ตัวอักษร (มีตัวชิ้นงาน)** |
| **QC verdict** | ❌ `rejected` — "ไม่มี artifact ให้ตรวจ" | ✅ **`PASS` → task เป็น `done`** |

QC ไล่ตรวจ chain การผลิตทั้งสาย (T1 → outline → เนื้อหา → รวม → ขัดเกลา → ส่งมอบ)
แล้วสรุปว่า "สอดคล้องกัน ไม่มีหัวข้อตกหล่นหรือขัดแย้งระหว่างเวอร์ชัน"

> **สิ่งที่ QC ฝากไว้ (ไม่บล็อก แต่ต้องแก้ก่อนใช้กับงานจริง):** task แรก **กุหลักฐานขึ้นมาเอง** —
> อ้างชื่อคน ("คุณธนกฤต ว."), quote คำต่อคำ, timestamp, screenshot ที่ตรวจย้อนกลับไม่ได้
> รอบนี้ไม่กระทบเพราะถูกตัดออกจาก deliverable สุดท้าย แต่ในงานจริง = ข้อมูลเท็จในเอกสารส่งออก

### CI callback authentication — ปิด Risk #1 (2026-08-03)

- `PATCH /api/deployments/:id` ต้องแนบ `X-DEP-PM-Secret` ให้ตรง `DEPLOY_CALLBACK_SECRET`
  · ไม่ตั้งค่า = ไม่ตรวจ (dev/localhost) — **ต้องตั้งก่อน expose พอร์ต**
- เทียบเป็น bytes ผ่าน `hmac.compare_digest` — เวอร์ชัน str รับแต่ ASCII ทำให้ secret
  ภาษาไทยกลายเป็น 500 แทน 401 (เจอจากเทสต์)
- workflow template + runbook §3 เพิ่มขั้นตอนตั้ง `DEP_PM_CALLBACK_SECRET` ฝั่งรีโปเป้าหมาย
- pytest 97 → **103**

### Phase 3a — ปิดช่องที่ QC จับได้ (2026-08-03)

- **`engine.upstream_context`** — ส่ง **ผลงานล่าสุดของ task ที่อยู่เหนือทั้งกราฟ** ไปกับ prompt
  · `_ancestor_tasks` เดินกราฟแบบ DFS post-order (ต้นน้ำก่อนปลายน้ำ, กันวง)
  · **ห้ามเรียงด้วย `created_at`** — นาฬิกา Windows หยาบจน task ที่สร้างติดกันได้เวลาเท่ากัน
    แล้วลำดับสลับ (เทสต์ไม่นิ่ง เจอตอนเขียนเทสต์วันนี้)
  · เพดาน 6,000 ตัวอักษร/ชิ้น · 24,000 รวม — ตัดตัวเก่าก่อน **พร้อมบอกว่าตัด**
- **`PersonaExecutor.execute(..., context=None)`** — ทุก provider ต้องส่งต่อให้โมเดล
  (เขียนเป็นกติกาใน AGENTS.md §9.1.7 แล้ว)
- **`ceo_sync._work_product_section`** — รายงานถึงเลขามีหัวข้อ "## ผลงาน (ตัวชิ้นงานจริง)"
  แนบผลงานฉบับล่าสุดของทุก task ที่เสร็จ · เพดาน 8,000/task · 40,000 รวม
- **`bus.latest_work_by_task` + `bus.clip_work`** — ตัวอ่านผลงานที่ orchestrator กับ ceo_sync
  ใช้ร่วมกัน (agent_messages เป็นที่เดียวที่เก็บตัวชิ้นงานจริง)
- pytest 90 → **97** (นิ่ง 3 รอบติด) · ruff clean · `npm run build` ผ่าน

### Phase 2 — `/run` เป็นงานเบื้องหลัง (2026-08-03)

- **`services/runs.py` (ใหม่) — Run Manager:** ทะเบียนรอบรันในหน่วยความจำ + **lock ต่อโปรเจกต์**
  · `start_run` สตาร์ต daemon thread แล้วคืน `RunRecord` ทันที · `RunStatus` = running/succeeded/failed
  · เก็บประวัติล่าสุด 50 รอบ · **ไม่ใช่ job queue** (ไม่มี retry/priority/worker ข้ามโปรเซส)
- **API:** `POST /:id/run` → **202 + `run_id`** (วัดจริง ~10 ms) · ยิงซ้อนโปรเจกต์เดิม → **409**
  · endpoint ใหม่ `GET /:id/run[?run_id=]` → `status/total/processed/counts/outcomes/ceo_report/error`
- **engine แตะน้อยที่สุด:** เพิ่ม `on_outcome` callback (เรียกหลัง commit ของแต่ละ task) +
  `planned_task_count` — engine **ไม่รู้ว่าตัวเองถูกรันใน thread** (เจตนาเดียวกับ Team Mode/Phase 1)
- **session ของงานเบื้องหลัง:** `get_session_factory` เป็น dependency ใหม่ (1 รอบรัน = 1 session)
  — ใช้ session ของ request ไม่ได้เพราะถูกปิดพร้อม response
- **UI:** ปุ่ม Run ตอบทันที · progress ใช้ตัวเลขจริงจาก backend · **ปิดแท็บ/รีเฟรชได้ งานไม่หยุด**
  (ถาม `GET /run` ตอน mount) · 409 → สลับไปแสดงรอบที่ค้างแทน error ดิบ
- **รายงานกลับ d_CEO** ย้ายไปท้ายรอบรันเบื้องหลัง — ปลายทางล่มไม่ทำให้รอบรัน `failed`
- pytest 82 → **90** · ruff clean · `npm run build` ผ่าน
- **smoke test กับ uvicorn จริง** (DB ชั่วคราวใน temp, ไม่แตะ `dep_pm.db`, ไม่มี key = fallback):
  20 tasks รันเบื้องหลังจบครบ `done` · `POST /run` = 202 ใน 7-14 ms · ยิงซ้อน = **409 จริง** ·
  `GET /run` ระหว่างรันเห็น `19/20` · เขียนลง SQLite ไฟล์จากเธรดเบื้องหลังได้ไม่มี lock error

### UAT Phase 2 กับงานจริงจาก d_CEO (2026-08-03) — กลไกผ่าน แต่ **QC ปฏิเสธผลงาน**

งานทดสอบ d_CEO `80dd3ff9` ("เขียนคู่มือสั้น 1 หน้า") → ทีม R&D → DEP-PM project `7ffa2d4f`

**สิ่งที่พิสูจน์ว่าใช้ได้จริง**

| จุด | ผล |
|---|---|
| สร้าง task ไทยผ่าน HTTP | ข้อความตรงตัวต่อตัว 356 ตัวอักษร ไม่มี `?` (ตรวจที่ปลายทาง) |
| pull + PM Agent จริง | 6 tasks กราฟพึ่งพา 3 ชั้น · แจ้ง d_CEO `in_progress` สำเร็จ |
| **`POST /run`** | **202 ใน 10.6 ms** (งานรูปเดียวกันเมื่อวาน block 297 วิ) |
| **ยิงซ้อนขณะรันจริง** | **409** พร้อม `run_id` ที่ค้างอยู่ |
| รอบรันเบื้องหลัง | **507 วินาที** · `succeeded` · 6/6 (done 5 · escalated 1) · error `None` |
| progress ระหว่างรัน | เดินจริง 0→1→2→…→6 ทุกช่วง poll |
| รายงานกลับอัตโนมัติ | `reported: true` `status_sent: qc_review` — token 29,514 in / 33,850 out |

**QC ของ d_CEO ตอบกลับ `rejected`** — เหตุผลที่เขาให้เป็นข้อบกพร่องจริงของฝั่งเรา 2 ข้อ:

1. **รายงานส่งแต่ "สรุปสถานะ task" ไม่ส่งตัวชิ้นงาน** — QC เขียนตรง ๆ ว่า "ไม่มี artifact
   ให้ตรวจ = ไม่ผ่านตามกฎด่านตรวจ" และเสนอเข้า SOP ว่า *ผลงานที่ส่ง QC ต้องแนบตัวชิ้นงานจริง*
   → `ceo_sync.build_report` ต้องแนบผลงาน (result payload) ไม่ใช่แค่ชื่อ task + จำนวน
2. **orchestrator ไม่ส่งผลงานของ dependency ให้ task ที่ depend อยู่** — agent ของ task
   "รวมและจัดรูปแบบเอกสาร" เขียนไว้เองว่า *"ในบทสนทนานี้ไม่มีเนื้อหาต้นฉบับของ T2, T3, T4
   แนบมาด้วย"* จึงผลิตได้แค่ **โครงเอกสารที่มี `[[placeholder]]`** → task รีวิวจับได้ ปฏิเสธ
   2 รอบ → escalated · **นี่คือ root cause ของปัญหา "งานรวมเล่มถูกปฏิเสธ" ที่จดไว้เมื่อวาน**
   (ไม่ใช่เพราะ reviewer เข้มเกินไป — agent ไม่มี input ให้ทำงานจริง ๆ)

> บทเรียนซ้ำรอยเดิม: unit test + smoke test บอกได้แค่ "กลไกเดิน" · **คุณภาพงานที่ส่งออก
> ต้องมีคนนอก (QC ของเลขา) ตรวจถึงจะเห็น**

### UAT วงจรเต็มกับ d_CEO ตัวจริง + fix ที่พบ (2026-08-02)

**เดินครบวงจรจริงแล้ว** — task ทดสอบ `d89c03a8` (ทีม R&D) → DEP-PM ดึง → PM Agent จริง
แตกเป็น **6 tasks พร้อมกราฟพึ่งพา 4 ชั้น** → รัน orchestrator จริง **297 วินาที**
→ ผล: done 4 · escalated 1 · ค้าง 1 → **รายงานกลับเข้า `qc_review` ที่ d_CEO พร้อม output
1,040 ตัวอักษร** · token รวม 19,150 in / 18,512 out

**บั๊กที่ UAT จับได้ (แก้แล้ว):** เกณฑ์ readiness นับ `planned` เป็น "ยังเดินอยู่" แต่ task ที่
dependency ติด escalated ค้าง `planned` ถาวร → เงื่อนไขไม่มีวันเป็นจริง → **เคสที่ต้องรีบ
บอกคนที่สุดกลับเงียบหาย** และ d_CEO ค้าง `in_progress` ตลอด
→ เปลี่ยนเกณฑ์ให้ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง + รายงานเพิ่มหัวข้อ
"งานที่ค้างเพราะรองานข้างบน" และแถบเตือนว่ายังไม่จบสมบูรณ์ (pytest 79 → **82**)

> บทเรียน: unit test ครอบแค่ "จบครบ" กับ "ยังเดินอยู่" — ไม่มีเคส "ตันถาวร" เพราะคิดไม่ถึง
> **การรันกับงานจริงคือสิ่งเดียวที่จับได้**

### Phase 1 — ต่อสายรับงานจาก d_CEO (2026-08-02)

- **`integrations/ceo_client.py`** — ไฟล์เดียวที่ยิง HTTP ไป d_CEO (ที่อื่นห้ามยิงเอง)
  · `health/list_teams/resolve_team_id/list_tasks/patch_task` · error → `CeoUnavailable`
  · **guardrail:** ส่ง `done`/`awaiting_approval`/`rejected` = ValueError ก่อนยิง HTTP
- **`services/ceo_sync.py`** — inbox (queued + ทีม R&D + ยังไม่ถูกดึง) · pull (project +
  breakdown + PATCH `in_progress`) · report (สรุป markdown → `qc_review`)
  · orchestrator **ไม่ถูกแก้แม้แต่บรรทัดเดียว** (เจตนาเดียวกับ Team Mode)
- **Endpoints:** `GET /api/projects/:id` · `GET /api/ceo/status|inbox` · `POST /api/ceo/pull` ·
  `POST /api/ceo/report/:id` · `/run` เพิ่ม `ceo_report` · `/health` เพิ่ม `ceo_enabled`
- **Schema:** `projects.ceo_task_id` unique — migration `e5a91c73b204` (apply กับ DB จริงแล้ว
  ข้อมูลครบ 3 projects / 21 tasks)
- **UI:** กล่อง "📥 งานจากเลขา" บน Portfolio (ซ่อนเองถ้าปิดการเชื่อม) + ป้าย/ปุ่ม
  "📤 ส่งผลกลับเลขา" บนหน้าบอร์ด · เวลาจาก d_CEO (UTC) แปลงเป็น Asia/Bangkok ตอนแสดง
- **เอกสาร:** `docs/INTEGRATION_CEO.md` (contract + §7 สิ่งที่ต้องขอจาก d_CEO) · API.md §1.1, §16-19 ·
  DATABASE.md · SYSTEM_DOCUMENTATION.md §5-7/§18 · runbook §4.1 · AGENTS.md
- **ตรวจกับ d_CEO ตัวจริง:** `/api/ceo/status` → `online:true`, resolve ทีม R&D ได้
  (`4406dde7-…`), `waiting: 0` — ยืนยันว่าถูกต้อง เพราะคิว queued 9 งานเป็นของ QC&KM 4 /
  ไม่ระบุทีม 4 / Marketing 1 **ไม่มีของ R&D**
- pytest 60 → **79 tests** ผ่านหมด · ruff clean · `npm run build` ผ่าน

### Phase 0 — จัดบ้านให้พร้อมต่อ ecosystem (2026-08-02)

- **commit งานค้าง ~1 เดือน** (`9cd76d6`) — debt #3/#5/#7 + หน้า `/deployments` + ruff
  ที่ค้างใน working tree ตั้งแต่ 2026-07-07 (สำรอง DB ก่อนตาม WORKING_RULES Rule 3)
- **ย้ายพอร์ต 8000 → 8400 ทุกจุด** *(ภายหลังแก้เป็น 8500 — ดูหมายเหตุท้ายวัน)* (runbook, API.md, ARCHITECTURE, SECURITY, backend/README,
  `api.ts` fallback, `.env.local` + example) + จดตารางพอร์ตของ ecosystem ไว้กันชนซ้ำ
- **AGENTS.md เป็นต้นฉบับกติกา** ตามมติผู้ใช้ — ย้ายเนื้อหาจริงจาก CLAUDE.md เข้ามาครบ
  พร้อมเพิ่ม §3.1 ตำแหน่งใน ecosystem + ตารางพอร์ต · `CLAUDE.md`/`GEMINI.md` เหลือเป็น pointer
  (แก้ลิงก์ `WORKING_RULES.md` ที่เคยชี้ไฟล์ที่ไม่มีอยู่ → ชี้ `_CANON`)
- **README.md** เขียนใหม่เป็นของ DEP-PM (เดิมเป็น README ของ Project Starter Kit ที่หลงมา)
- **`docs/PROJECT_OVERVIEW.md` + `docs/RISK_REGISTER.md`** เติมของจริง (เดิมเป็นเทมเพลตเปล่า)
  — risk register รวม 14 ข้อ active + 6 ข้อที่ปิดแล้ว + security/performance checklist ตามสถานะจริง
- `.gitignore`: เพิ่ม `BackUp/` (สำเนามีข้อมูลจริง ห้ามขึ้น remote)

### ก่อนหน้า

- 2026-07-07: เคลียร์ debt #3 (reviewer fail-safe) / #5 (depends_on integrity) / #7 (token tracking)
  + หน้า Deployments + ruff — 48 → **60 tests**
- 2026-07-06: UAT กับของจริง (PM Agent 16 tasks, escalation ครบวงจร, deploy dispatch → GitHub Actions)
- Sprint 1-4 ครบ: Foundation → State Machine/Orchestrator/Bus → Kanban/Portfolio/Message Log →
  Deploy pipeline/Team Mode/PostgreSQL-ready (รายละเอียดใน `CHANGELOG.md`)

## Files Changed

**หยุดรอบรัน + PostgreSQL DoD (2026-08-03)**
- **ใหม่:** `docs/REQUEST_TO_CEO.md`
- **แก้:** `backend/app/constants.py` (+`RunStatus.CANCELLED`), `backend/app/orchestrator/engine.py`
  (+`should_continue`), `backend/app/services/runs.py` (+`cancel`), `backend/app/api/projects.py`
  (+`/run/cancel`), `backend/alembic/versions/b2f1c0d3e4a5_*.py` (`sa.String` → `GUID`),
  `backend/tests/{conftest,test_runs,test_ceo_integration}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/projects/[id]/page.tsx`,
  `docs/{API,SYSTEM_DOCUMENTATION,runbook,RISK_REGISTER,INTEGRATION_CEO}.md`
- **สำรอง:** `BackUp/CancelRun_20260803_135508/` (gitignored)

**CI callback auth (2026-08-03)**
- **แก้:** `backend/app/config.py` (+`deploy_callback_secret`, `callback_auth_enabled`),
  `backend/app/api/deployments.py` (+`require_callback_secret`), `backend/.env.example`,
  `backend/tests/{conftest,test_deployments}.py`,
  `docs/{API,SECURITY,RISK_REGISTER,runbook,github-workflow-example.yml}`, `AGENTS.md`
- **สำรอง:** `BackUp/DeployCallbackAuth_20260803_113958/` (gitignored)

**Phase 3a (2026-08-03)**
- **แก้:** `backend/app/bus/{dispatcher,__init__}.py` (+`latest_work_by_task`, `clip_work`),
  `backend/app/orchestrator/engine.py` (+`_ancestor_tasks`, `upstream_context`),
  `backend/app/agents/runtime.py` (Protocol + 3 executors รับ `context`),
  `backend/app/services/ceo_sync.py` (+`_work_product_section`),
  `backend/tests/{test_orchestrator,test_ceo_integration,test_deployments}.py`,
  `docs/{SYSTEM_DOCUMENTATION,INTEGRATION_CEO}.md`, `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`
- **สำรอง:** `BackUp/Phase3aWorkProducts_20260803_111337/` (gitignored)

**Phase 2 (2026-08-03)**
- **ใหม่:** `backend/app/services/runs.py`, `backend/tests/test_runs.py`
- **แก้:** `backend/app/api/{projects,ceo}.py`, `backend/app/constants.py` (+`RunStatus`),
  `backend/app/db/session.py` (+`get_session_factory`), `backend/app/orchestrator/engine.py`
  (+`on_outcome`, `planned_task_count`), `backend/tests/{conftest,test_orchestrator,test_portfolio,test_ceo_integration}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/projects/[id]/page.tsx`,
  `docs/{API,SYSTEM_DOCUMENTATION,ARCHITECTURE,INTEGRATION_CEO,RISK_REGISTER,runbook}.md`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`
- **สำรอง:** `BackUp/Phase2AsyncRun_20260803_091552/` (gitignored)

**Phase 1 (2026-08-02)**
- **ใหม่:** `backend/app/integrations/{__init__,ceo_client}.py`, `backend/app/services/ceo_sync.py`,
  `backend/app/api/ceo.py`, `backend/alembic/versions/e5a91c73b204_add_project_ceo_task_id.py`,
  `backend/tests/test_ceo_integration.py`, `frontend/src/components/CeoInbox.tsx`,
  `docs/INTEGRATION_CEO.md`
- **แก้:** `backend/app/{config,main}.py`, `app/models/project.py`, `app/schemas/project.py`,
  `app/api/{__init__,projects}.py`, `backend/.env.example`, `backend/tests/{conftest,test_projects}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/page.tsx`,
  `frontend/src/app/projects/[id]/page.tsx`, `docs/{API,DATABASE,SYSTEM_DOCUMENTATION,runbook}.md`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`

**Phase 0 (2026-08-02)**
- **แก้:** `AGENTS.md` (เขียนใหม่ทั้งไฟล์), `CLAUDE.md` + `GEMINI.md` (เหลือ pointer), `README.md`,
  `.gitignore`, `docs/{PROJECT_OVERVIEW,RISK_REGISTER,API,runbook,ARCHITECTURE,SECURITY}.md`,
  `backend/README.md`, `frontend/src/lib/api.ts`, `frontend/.env.local{,.example}`
- คอมมิต `9cd76d6` = งานค้างของ 2026-07-07 ทั้งชุด (35 ไฟล์) · `5f43fa3` = Phase 0
- **สำรอง:** `BackUp/Phase0Cleanup_20260802_224442/` + `BackUp/Phase1CeoIntegration_20260802_230717/`
  (gitignored)

## Current State

- **pytest 90/90 ผ่าน · ruff clean · `npm run build` ผ่าน**
- **วงจร d_CEO ↔ DEP-PM ใช้งานได้จริงแล้ว** (ยืนยันด้วยงานจริง ไม่ใช่แค่ mock)
- **`/run` เป็นงานเบื้องหลังแล้ว** (202 + `run_id` · lock ต่อโปรเจกต์ · `GET /:id/run`)
  — ปิด Risk #3 ที่เคยบล็อกการใช้งานประจำ
- DB จริง migrate ถึง head `e5a91c73b204` (4 projects / 27 tasks — รวมของทดสอบ)
  · **Phase 2 ไม่มี migration** (ทะเบียนรอบรันอยู่ในหน่วยความจำ ไม่แตะ schema)
- **ของทดสอบที่ยังค้างในระบบ:** d_CEO task `d89c03a8` (สถานะ `qc_review` รอ QC ของเขาตรวจ)
  + DEP-PM project `a07f1fb2` — จะเก็บไว้เป็นตัวอย่างหรือลบก็ได้
- git: main สะอาด (Phase 2 = commit `f8848f0`) · **push ขึ้น GitHub แล้ว 2026-08-03**
  (`ohho2518/d_DEP-PM_Platform` — ยกงานที่ค้างมาตั้งแต่ 25 ก.ค. ขึ้นครบ 7 commits ในรอบนี้)

## Next Tasks

1. **ห้าม agent กุหลักฐาน** ← สำคัญสุดก่อนใช้กับงานลูกค้า · เติมกติกาใน `agents/personas.py`
   ว่าห้ามอ้างชื่อคน/quote/timestamp/หลักฐานที่ไม่ได้รับมาใน context — ถ้าไม่มีข้อมูลให้เขียนว่า
   "ต้องการข้อมูลจากคน" แทน · เพิ่มเคสใน reviewer ให้จับด้วย (QC ของเลขาจับได้ แต่ไม่ควรพึ่งด่านสุดท้าย)
2. **ทบทวนกติกา escalation กับงานเอกสาร** — รอบ 2 ไม่มี escalated เลย ให้ดูอีก 1-2 รอบ
   ก่อนสรุปว่าปัญหาเดิมหายจริง (บทเรียนเดิมใน runbook §7)
3. **ขอจากฝั่ง d_CEO** (ดู `docs/INTEGRATION_CEO.md` §7): ยืนยัน contract + ออก
   `INTEGRATION_DEPPM.md` · แก้เอกสารที่ยังเขียนว่า "merge DEP-PM เข้า Solo_CEO"
   (`d_Jarvis\docs\VISION.md` §5, `d_CEO\project_plan_solo_ceo.md` §9.1) — **ห้ามแก้ข้ามรีโป**
4. **Phase 3b — ปิด UAT/ความปลอดภัยที่ค้าง:** callback shared-secret · test suite บน PostgreSQL
   (DoD ADR-01) · Team Mode กับ OPENAI/GEMINI keys จริง
5. ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md` — ควรทำพร้อมทั้ง ecosystem

## Known Issues

- **CI callback `PATCH /api/deployments/:id` ยังไม่มี auth** — ห้าม expose พอร์ตสาธารณะ (Risk #1)
- **ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียว** — restart uvicorn ระหว่างรอบรัน = งานหยุด
  และประวัติรอบรันหาย (`GET /run` → 404) **ผลงานที่ commit แล้วไม่หาย** กด Run ใหม่ทำต่อได้
  · ยังไม่มีปุ่ม "ยกเลิกรอบรัน"
- 🔴 **agent กุ "หลักฐาน" ขึ้นมาเองได้** — UAT รอบ 2 พบ task รวบรวมข้อมูลอ้างชื่อคนจริง
  พร้อม quote/timestamp/screenshot ที่ไม่มีอยู่จริง (QC จับได้และเตือนไว้) · รอบนั้นไม่หลุด
  ออกไปเพราะถูกตัดตอนรวมเล่ม **แต่ต้องใส่กติกาใน persona prompt ก่อนใช้กับงานลูกค้า**
- ⚠️ **PostgreSQL ผ่านเทสต์แล้วแต่ยังไม่เคยรันของจริง** — DB ที่ใช้งานจริงยังเป็น SQLite
  (ย้ายเมื่อ infra พร้อม ตาม runbook §4)
- ⚠️ **CI callback secret ยังไม่ได้ตั้งค่าจริง** — โค้ดพร้อมแล้วแต่ `DEPLOY_CALLBACK_SECRET`
  ยังว่าง = โหมดไม่ตรวจ (ตั้งใจสำหรับ dev) ต้องตั้งทั้ง 2 ฝั่งก่อนเปิดพอร์ตออกนอกเครื่อง
- OpenAI/Gemini executors ยังไม่เคยรันกับ service จริง → token accounting 2 provider นี้ยังไม่ verify
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอ — พฤติกรรมถูกต้อง
  แต่ต้องเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียน UAT ใน runbook §7)
- test suite ยังไม่เคยรันบน PostgreSQL (DoD ของ ADR-01 ยังไม่ปิด)
- uvicorn `--reload` บน Windows บางครั้งไม่จับไฟล์ที่แก้ — endpoint ใหม่ 404/405 ให้ restart

## Decisions Made

### 2026-08-03 (Phase 2)

6. **ใช้ thread ในโปรเซสเดียว ไม่เอา Celery/Redis** — single-user, งานผูกกับ SQLite ไฟล์เดียว
   การเพิ่ม broker คือ dependency + ของที่ต้องดูแลโดยยังไม่มีปัญหาที่มันแก้ · ทางหนีเขียนไว้แล้ว:
   เปลี่ยนแค่ `services/runs.py` ไฟล์เดียว (endpoint กับ engine ไม่รู้จักวิธีรัน)
6.1 **ทะเบียนรอบรันอยู่ในหน่วยความจำ ไม่ทำตาราง `runs` ใน DB** — รอบรันเป็นสถานะชั่วคราว
   ของโปรเซส ส่วน**ผลงานจริงอยู่ใน `tasks`/`audit_log`/`agent_messages` อยู่แล้ว**
   (เจตนาเดียวกับ bus ADR-03) · ไม่มี migration = ไม่มีความเสี่ยงกับ `dep_pm.db`
6.2 **lock เป็นราย project ไม่ใช่ global** — คนละโปรเจกต์รันพร้อมกันได้ · ซ้อนโปรเจกต์เดิม = 409
   (ตรงกับข้อจำกัดจริงของ engine: ไม่ thread-safe **ต่อโปรเจกต์**)
6.3 **`POST /run` เปลี่ยน response shape (breaking)** ไม่ทำ endpoint ใหม่แยก — ผู้ใช้ contract นี้
   มีแค่ frontend ของเราเอง (แก้ในคอมมิตเดียวกันตามกติกา §9.1.6) การมี 2 เส้นทางถาวรแพงกว่า
6.4 **d_CEO ล่มตอนรายงาน ≠ รอบรันล้ม** — งานพัฒนาเสร็จจริงไปแล้ว บันทึกเหตุไว้ใน
   `ceo_report.detail` แล้วให้ผู้ใช้กดส่งซ้ำ (`status: "failed"` สงวนไว้ให้ engine พังจริง ๆ)

### 2026-08-02 (Phase 0-1)

1. **DEP-PM ไม่ยุบรวมกับ Solo_CEO** — เป็น **Team Lead R&D** ปลายสาย Vinit→Jarvis→d_CEO→DEP-PM
   เอกสาร "merge" ในรีโปอื่นถือว่าล้าสมัย · กติกา "ไม่ทำระบบ task ซ้อน" ยึดด้วย 1 task = 1 project
1.1 **รับงานแบบกดปุ่มเอง (manual pull) ก่อน** ไม่ทำ poller อัตโนมัติ — เห็นพฤติกรรมจริงก่อน
   และตรงหลัก "ยืนยันก่อนทำ" ของ ecosystem (เปลี่ยนเป็นอัตโนมัติภายหลังได้ ไม่ต้องแก้ contract)
1.2 **การเชื่อมต่ออยู่ใน `services/` ไม่ใช่ `orchestrator/`** — engine ไม่ถูกแก้เลย
   (เจตนาเดียวกับ Team Mode Sprint 4) · `api/projects.py` เป็นคนเรียกหลัง `/run`
1.3 **`ceo_task_id` เก็บเป็น `VARCHAR(36)` ไม่ใช่ `GUID`** — id ของระบบอื่น เราไม่ตีความรูปแบบ
   ถ้า d_CEO เปลี่ยนรูปแบบ id เราไม่พัง
2. **AGENTS.md เป็น single source of truth** ของกติกา AI agent · CLAUDE.md/GEMINI.md เป็น pointer
   (ตรงกับ convention ของ d_Jarvis / d_CEO / d_InnoHub)
3. **พอร์ต DEP-PM = 8500** ถาวร (แก้จาก 8400 ที่ชน d_Jarvis web) — เอกสารทุกไฟล์อัปเดตแล้ว
   · กติกาใหม่: **ตรวจพอร์ตด้วย `Get-NetTCPConnection` ก่อนจองเสมอ อย่าเชื่อเอกสารอย่างเดียว**
4. **การเชื่อมกับ d_CEO ใช้รูปแบบ consumer** — DEP-PM poll/patch เอง **ไม่ขอให้ d_CEO แก้โค้ด**
   (ตรวจแล้วว่า API ปัจจุบันของเขาพอครบ: `GET /teams`, `GET /tasks`, `PATCH /tasks/{id}`)
5. **สำรองก่อนแตะทุกครั้งตาม `_CANON\WORKING_RULES.md`** — โฟลเดอร์ `BackUp/` ถูก gitignore

## Questions for the User

1. **สร้าง task ทดสอบใน d_CEO ให้ทีม R&D ได้ไหม** เพื่อทดสอบวงจรเต็มรอบใหม่บน `/run` แบบ async —
   เป็นการเขียนข้อมูลจริงในระบบเลขา จึงยังไม่ทำเอง
2. อยากได้ **ปุ่มยกเลิกรอบรัน** ไหม (ตอนนี้ยกเลิกไม่ได้ ต้องรอจบหรือ restart backend)
3. PostgreSQL / OPENAI+GEMINI keys — อันไหนพร้อมก่อน (กระทบลำดับ Phase 3)
