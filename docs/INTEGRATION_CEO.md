# INTEGRATION_CEO.md — Contract ร่วม DEP-PM ⇄ d_CEO

> **มุมมองฝั่ง consumer.** เจ้าของ contract (provider) = **d_CEO** (`D:\Dev_Proj\0_CORE\d_CEO`)
> ผู้เรียก (consumer) = **DEP-PM** ผ่านไฟล์เดียว `backend/app/integrations/ceo_client.py`
> **Contract version:** `v1` (ฝั่งเรา) · **Last synced:** 2026-08-02
> **สถานะ:** ⚠️ **ยังไม่ได้ให้ฝั่ง d_CEO ยืนยัน** — ดู §7

---

## 0. กฎเหล็ก

> **แตะผิวสัมผัสต่อไปนี้เมื่อไร ให้อัปเดตไฟล์นี้ทันที:**
> endpoint path/method · request/response schema · สถานะที่ส่งกลับ · timezone ·
> error codes · `backend/app/integrations/ceo_client.py`

1. เปลี่ยนแบบ **additive / backward-compatible เท่านั้น**
2. **provider (d_CEO) แก้ก่อนเสมอ** แล้วค่อย consumer (เรา) — เราไม่แก้โค้ดในรีโปเขา
3. อัปเดตไฟล์นี้ + bump version + `Last synced`
4. อัปเดต `PROJECT_STATUS.md` ของทั้งสองรีโป (โยงถึงกัน)
5. sync `ceo_client.py` + stub ใน `backend/tests/test_ceo_integration.py` (drift guard อยู่ที่นั่น)

---

## 1. บทบาทและวงงาน

```
Vinit (CEO) → d_Jarvis (หน้า) → d_CEO (สมอง) ──delegate──► DEP-PM (Team Lead R&D)
                                     ▲                          │
                                     └──── qc_review + output ───┘
                                        → QC gate (team-qc-km) → Vinit เคาะ
```

contract นี้ครอบเฉพาะ **ผิว REST ระหว่าง DEP-PM ↔ d_CEO** — การแตกงาน/รัน agent/deploy
เป็นเรื่องภายในของ DEP-PM ทั้งหมด

**กติกาแกน:** **1 task ธุรกิจใน d_CEO = 1 project ใน DEP-PM** (`projects.ceo_task_id` unique)
task ย่อยบนบอร์ดเราไม่ใช่ทะเบียนงานธุรกิจชุดที่สอง

---

## 2. การเชื่อมต่อ

| เรื่อง | ค่า |
|---|---|
| Base URL | `http://127.0.0.1:8000` (env `CEO_API_BASE` ฝั่งเรา) |
| Bind | **127.0.0.1 เท่านั้น** — API ทั้งสองฝั่งไม่มี auth |
| Auth | ไม่มี (Phase 1 ของทั้งคู่) |
| `X-Org-Id` | **ไม่ต้องส่ง** → d_CEO ใช้ org default (`dproai-innotech`) |
| **Timezone** | d_CEO คืนเวลาเป็น **UTC** — DEP-PM แปลงเป็น `Asia/Bangkok` **ตอนแสดงผลเท่านั้น** |
| Content-Type | `application/json` |
| Timeout | `CEO_TIMEOUT_SECONDS` (ปริยาย 15s) |
| ทีมที่เราอ่านงาน | `CEO_TEAM_NAME` ปริยาย **"Research & Development"** — resolve เป็น id ตอน runtime ผ่าน `GET /teams` (**teams เป็น data ห้าม hardcode id**) |

---

## 3. Endpoints ที่ DEP-PM พึ่งพา

### 3.1 `GET /health`
`{"status":"ok","app_env":"..."}` → ใช้ตัดสินว่าจะโชว์ปุ่มดึงงานไหม
ต่อไม่ได้ = แสดง "🧠 สมองออฟไลน์" **ไม่ crash**

### 3.2 `GET /teams`
`[{id, name, status, ...}]` — จับคู่ชื่อ `CEO_TEAM_NAME` → `team_id`
ไม่เจอชื่อ = ถือว่าไม่มีงานของเรา (inbox ว่าง) ไม่ error

### 3.3 `GET /tasks?status=queued&limit=200`
`[{id, org_id, input_text, assigned_team_id, status, output, created_at, completed_at}]`
DEP-PM กรองฝั่งตัวเอง: `assigned_team_id == team_id ของ R&D` **และ** ยังไม่มี project ที่ `ceo_task_id` ตรงกัน

### 3.4 `PATCH /tasks/{id}` — เส้นทางเดียวที่เราเขียนกลับ
```http
PATCH http://127.0.0.1:8000/tasks/{id}
{"status": "in_progress"}                      # ตอนรับงาน
{"status": "qc_review", "output": "<markdown>"} # ตอนส่งผลงาน
```
- **200** → TaskOut · **400** = status ไม่รู้จัก/body ว่าง · **404** = ไม่พบ/คนละ org
- 🔴 **DEP-PM ส่งได้แค่ `in_progress` และ `qc_review` เท่านั้น**
  `done` / `awaiting_approval` / `rejected` **ห้ามส่ง** — บังคับด้วย `ALLOWED_OUTBOUND_STATUSES`
  ใน `ceo_client.py` (ValueError ก่อนยิง HTTP)
  **เหตุผล:** มติ Vinit 2026-08-02 (เคสเดียวกับ d_MOS) — กฎเหล็ก *"ไม่มีงานถึง Vinit/ลูกค้า
  โดยไม่ผ่าน QC"* งานของเราต้องผ่าน QC gate ของ d_CEO เสมอ

**รูปแบบ `output` ที่เราส่ง** (markdown — QC ของ d_CEO จะต่อท้ายด้วยหัวข้อ `## ผลตรวจ QC`)
```markdown
# ผลงานจากทีม R&D — <ชื่อโปรเจกต์>

งานทั้งหมด N รายการ · เสร็จ X · ต้องการคนตัดสิน Y

## งานที่ทำเสร็จ
- [P1] ออกแบบ schema (แก้ 1 รอบ) · deploy แล้ว

## งานที่ต้องการคนตัดสิน (escalated)
- [P0] ต่อ CI — <เหตุผลจากข้อความ question บน bus>

## ต้นทุน
token: input 1,234 · output 567

## อ้างอิง
DEP-PM project `<uuid>` — เปิดบอร์ด/บทสนทนา agent ย้อนหลังได้ที่ `/projects/<uuid>` (backend `:8500`)
```

---

## 4. Endpoints ฝั่ง DEP-PM (สำหรับผู้ใช้/UI — ไม่ใช่ผิวสัมผัสกับ d_CEO)

| method | path | ทำอะไร |
|---|---|---|
| GET | `/api/ceo/status` | สมองออนไลน์ไหม + team_id + จำนวนงานที่รอ · **ไม่ 503** แม้ปิดอยู่ |
| GET | `/api/ceo/inbox` | งาน queued ของทีม R&D ที่ยังไม่ถูกดึง |
| POST | `/api/ceo/pull` | `{task_ids?: [], breakdown?: true}` → รับงาน + สร้างโปรเจกต์ + แตกงาน + PATCH `in_progress` |
| POST | `/api/ceo/report/{project_id}` | ส่งผลงานกลับเป็น `qc_review` |

รายละเอียด request/response → `docs/API.md` §16-19

---

## 5. พฤติกรรมที่ตกลงไว้

| สถานการณ์ | DEP-PM ทำอะไร |
|---|---|
| d_CEO ปิดอยู่ | `/api/ceo/*` ตอบ **503** พร้อมข้อความ (ยกเว้น `/status` ที่ตอบ `online:false`) · เส้นทางอัตโนมัติหลัง `/run` **เพิกเฉยเงียบ** ไม่ทำให้ run พัง |
| ดึงงานซ้ำ | กรองออกด้วย `ceo_task_id` unique — pull รอบสองได้ `count: 0` |
| สร้างโปรเจกต์แล้วแต่ PATCH ไม่ผ่าน | เก็บโปรเจกต์ไว้ + `acknowledged: false` — ยิง report ทีหลังได้ (ไม่ rollback) |
| งานยังไม่จบ | `report` ตอบ `ready:false` และ **ไม่แตะ d_CEO** — "ไม่จบ" = ยังมี agent ถืองานอยู่ **หรือ** ยังมี `planned` ที่ dependency จบครบแล้ว (รันต่อได้) **หรือ** ยังมี `backlog` (ไม่ยืนยัน scope) |
| งานจบแต่มี escalated | ยังรายงานเป็น `qc_review` พร้อมระบุรายการที่ต้องการคนตัดสิน — **เราไม่ตัดสินเองว่างานล้มเหลว** |
| มี escalated แล้วตัวที่ depend ค้าง `planned` ถาวร | **ถือว่าจบรอบ → รายงานทันที** พร้อมหัวข้อ "งานที่ค้างเพราะรองานข้างบน" · เกณฑ์นี้ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง (บั๊กที่แก้แล้ว 2026-08-02: เดิมค้างไม่รายงานตลอดกาล) |
| `/run` จบและโปรเจกต์มาจาก d_CEO | รายงานอัตโนมัติ + คืนผลใน field `ceo_report` ของ response |

---

## 6. ทดสอบแล้ว (2026-08-02)

- ✅ `GET /api/ceo/status` กับ d_CEO ตัวจริง → `online:true`, resolve ทีม R&D ได้
  (`4406dde7-64ec-44b6-9139-4abc61b58aa6`), `waiting: 0`
- ✅ ยืนยันว่า `waiting: 0` ถูกต้อง — คิว queued 9 งานเป็นของ QC&KM 4 / ไม่ระบุทีม 4 / Marketing 1
  **ไม่มีงานของ R&D** จึงยังไม่มีอะไรให้ดึง
- ✅ pull / report / guardrail / degrade เมื่อออฟไลน์ — ครอบด้วย 20 เทสต์ใน
  `backend/tests/test_ceo_integration.py` (stub client ผ่าน dependency override ไม่ mock HTTP)
- ✅ **UAT วงจรเต็มกับงานจริง** (task `d89c03a8`, ได้รับอนุญาตจาก Vinit):
  สร้าง task ให้ทีม R&D → DEP-PM เห็นในคิว → ดึง → PM Agent จริงแตกเป็น 6 tasks
  (กราฟพึ่งพา 4 ชั้น) → รัน 297 วินาที → done 4 / escalated 1 / ค้าง 1 →
  **d_CEO ได้สถานะ `qc_review` + output 1,040 ตัวอักษร** · token 19,150 in / 18,512 out
- 🐛 **บั๊กที่ UAT จับได้ (แก้แล้ว):** เกณฑ์ readiness เดิมนับ `planned` เป็น "ยังเดินอยู่"
  ทำให้โปรเจกต์ที่มี escalated ไม่เคยรายงานเลย → d_CEO ค้าง `in_progress` ตลอดกาล
- ⬜ ยังไม่ได้ทดสอบ: งานที่จบ 100% โดยไม่มี escalated · การรับหลายงานพร้อมกัน

---

## 7. สิ่งที่ต้องขอจากฝั่ง d_CEO

1. **ยืนยัน contract นี้** แล้วออก `docs/INTEGRATION_DEPPM.md` ฝั่ง provider (ตามแบบ
   `INTEGRATION_JARVIS.md` / `INTEGRATION_MOS.md`) — ปัจจุบัน d_CEO **ยังไม่มีเอกสารใด
   กล่าวถึง DEP-PM เลย**
2. **แก้เอกสารที่ล้าสมัย:** `project_plan_solo_ceo.md` §9.1 ยังเขียนว่า *"d_DEP-PM ควบรวม
   เป็น engine เดียวกับ Solo_CEO"* — ขัดกับสายบังคับบัญชาที่ Vinit ยืนยัน 2026-08-02
   (เช่นเดียวกับ `d_Jarvis\docs\VISION.md` §5)
3. **ยืนยันกติกาการมอบงาน:** งานที่ต้องการให้ DEP-PM ทำ ต้องตั้ง `assigned_team_id`
   = ทีม Research & Development ตอน `POST /tasks` (ไม่งั้นเราไม่เห็นในคิว)
4. (ทางเลือก) ถ้าอยากให้ DEP-PM รับงานอัตโนมัติแทนการกดปุ่ม — ต้องตกลงเรื่องความถี่ poll
   หรือให้ d_CEO ยิง webhook มาที่ `:8500` แทน
