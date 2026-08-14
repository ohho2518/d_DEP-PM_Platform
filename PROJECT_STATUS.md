# PROJECT_STATUS.md — DEP-PM Platform

> ## 📣 อ่านก่อนเริ่มงาน — 2 เรื่องที่ต้องให้เจ้าของลงมือเอง
>
> ### 1. ✅ ผู้ให้บริการ AI ใช้ได้ครบ 3 เจ้าแล้ว (ตรวจจริง 2026-08-14)
> Anthropic ✅ · OpenAI ✅ · **Gemini ✅ หลังแก้ชื่อรุ่น**
> — **คีย์ Gemini ไม่เคยเสีย** (`ListModels` ตอบ 200 · 50 รุ่น) ที่พังคือ `GEMINI_MODEL=gemini-3-pro`
> **ซึ่งไม่มีอยู่จริง**บน API v1beta → 404 ทุกครั้ง · เปลี่ยนเป็น `gemini-3-flash-preview` แล้วผ่าน
> · 🔎 รุ่นที่บัญชีนี้เรียกได้: `gemini-3-flash-preview` ✅ · `gemini-3.1-flash-lite` ✅ ·
> `gemini-3.1-pro-preview` = **429 quota** (ชั้น pro ต้องมีโควตา/billing) · รุ่น 2.5 = ปิดสำหรับผู้ใช้ใหม่
>
> ### 2. 🔴 คีย์ยังใช้ร่วมกันข้ามรีโป — ต้นเหตุที่ทำให้ 6 ส.ค. ทุกอย่างตายพร้อมกัน **ยังไม่ถูกแก้**
> ตัวสำรองช่วยได้เฉพาะตอน "เจ้านั้นล่ม" · ถ้า**บัญชีหมดเครดิต** ทุกรีโปที่ใช้คีย์เดียวกันยังเจอพร้อมกัน
> — ต้องเข้าคอนโซลผู้ให้บริการแยกคีย์ต่อรีโป (ทำจากในโค้ดไม่ได้)
>
> ✅ งานฝั่งโค้ดของใบสั่งงาน 2026-08-06 **ทำครบแล้ว 2026-08-14** (ดู Completed Work)

---

> ## 📣 เปิดโปรเจกต์นี้แล้ว **อ่านตรงนี้ก่อน** — มีคำถามค้างรอ Vinit ตัดสิน 1 ข้อ
>
> **d_CEO task `4eb918bd` (ทดสอบระบบ รอบ 3) อยู่สถานะ `awaiting_approval` — QC ส่งมาให้ Vinit เลือก:**
> 1. **จัดหาข้อมูลจริงของทีม R&D** (log วัน-เวลาต่องาน · ผู้รับผิดชอบ · ความเห็นผู้ปฏิบัติงาน)
>    แล้วให้ pipeline เดินต่อ — QC ยืนยันว่า "พร้อมเดินต่อทันทีเมื่อได้ข้อ 1"
> 2. **หรือ** ปิดรอบทดสอบนี้ว่า *"ระบบทำงานถูกต้อง — ปฏิเสธการแต่งข้อมูลได้ถูกต้อง"*
>    โดยไม่ต้องมีรายงานฉบับจริง
>
> ⚠️ **ฝั่งเราทำอะไรกับ task นี้ต่อเองไม่ได้** — ส่งกลับได้แค่ `in_progress`/`qc_review` การยิงซ้ำ
> จะดึงงานถอยจาก `awaiting_approval` และเสียค่ารอบ QC ฟรี ๆ (QC เขียนเองว่า rework = loop ตัน)
>
> ✅ ใบสั่งงาน `ORDER_TICKET_2026-08-03` Ticket #3 **ปิดครบ 5/5 แล้ว** (ติ๊กในใบแล้ว)

---

> อัปเดตล่าสุด: 2026-08-14 | สถานะโดยรวม: **รองรับ AI หลายเจ้าแล้ว · pytest 170/170**
> — เจ้าหลักล่ม → งานเดินต่อด้วยตัวสำรองพร้อมป้ายบอกว่าใครทำ · ทุกเจ้าล่ม → หยุดอย่างมีศักดิ์ศรี
> (task `escalated` ไม่ค้าง `in_progress`) · มีหน้า **`/settings`** กรอกคีย์/ทดสอบ/จัดลำดับสำรอง
> ได้เองโดยไม่ต้อง restart · **พิสูจน์ด้วย API จริงทั้ง 3 เจ้า** ไม่ใช่แค่เทสต์จำลอง

---

> อัปเดตก่อนหน้า: 2026-08-03 | **Phase 0-3a เสร็จ · กติกาห้ามกุหลักฐานผ่านการวัดผลจริง**
> — UAT รอบ 3 (โจทย์ที่ล่อให้กุโดยตรง) **ไม่มีการกุแม้แต่จุดเดียว** และ **QC ของ d_CEO ยืนยัน
> จากภายนอกว่าเป็นพฤติกรรมที่ถูก** · แต่รอบเดียวกันเปิดบั๊กใหม่ที่แก้แล้ววันนี้: งานที่ติดเพราะ
> ต้องรอคน ถูก reviewer บีบให้ "กุการกระทำ" และถูก approve เป็น `done` ทั้งที่ไม่มีชิ้นงาน
> → เพิ่ม verdict **`needs_human`** (escalate ตั้งแต่รีวิวแรก) · pytest **133/133**

## สถานะการใช้งาน (สำคัญสำหรับ session ถัดไป)

- **`backend/dep_pm.db` = ข้อมูลจริงของผู้ใช้ — ห้ามลบเด็ดขาด** (สำรอง DB ล่าสุด `BackUp/Phase0Cleanup_20260802_224442/`
  · Phase 2 ไม่แตะ schema จึงสำรองเฉพาะไฟล์โค้ด: `BackUp/Phase2AsyncRun_20260803_091552/`)
- **พอร์ตของ DEP-PM = 8500** — `uvicorn app.main:app --reload --port 8500`
  · 📌 ทะเบียนพอร์ตของทั้ง eco อยู่ที่ `_CANON\SERVICE_PORTS.md` (ไม่ก๊อบตารางมาไว้ที่นี่แล้ว —
  ใบสั่งงาน 3 ส.ค. Ticket 3.5) · `8000` d_CEO และ `8400` d_Jarvis web **ห้ามหยุด**
- `backend/.env` มี key จริงครบ: ANTHROPIC (Solo Mode live), GITHUB_TOKEN+REPO (`ohho2518/d_DEP-PM_Platform`)
- โปรเจกต์ในระบบ: "Demo: Booking API" (4 done), "d_ACC" (17 backlog), "Deploy UAT",
  + งานทดสอบจากเลขา 4 ตัว (`a07f1fb2`, `7ffa2d4f`, `4d8004ff`, **`c8d5c50c` = รอบ 3**)
  + `bc3a43b7` (ตรวจ `needs_human` กับโมเดลจริง) — ทั้งหมดเก็บไว้เป็นหลักฐาน UAT
- DB migrate เป็น head `e5a91c73b204` แล้ว · **uvicorn รันค้างอยู่ที่ `:8500` (ไม่มี `--reload`)**
  — แก้ persona/prompt แล้ว**ต้องรีสตาร์ตเอง** ไม่งั้นทดสอบได้พฤติกรรมเก่า · next ไม่ได้รันค้าง
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

### รองรับ AI หลายเจ้า + หน้าตั้งค่าคีย์ (2026-08-14) — ปิดใบสั่งงาน 2026-08-06 ฝั่งโค้ด

**ที่มา:** ใบสั่งงานมอบให้ DEP-PM แค่ข้อ 9.7 = *เขียนคู่มือ* `LLM_PROVIDER_PATTERN.md` ให้รีโปอื่นลอก
(ปิดไป 11 ส.ค.) — แต่พอเทียบ DoD กับโค้ดจริงพบว่า **เราเป็นรีโปเดียวที่ยังไม่ได้ทำตามคู่มือที่ตัวเองเขียน**
(ช่อง "บอกว่าใช้ตัวสำรองยังไง" ของ DEP-PM ในตารางคู่มือเป็น `—` ตัวเดียวในตาราง)

| กติกาในใบ | ก่อนหน้านี้ | ตอนนี้ |
|---|---|---|
| §2 ลำดับเจ้าจาก env | ❌ ฝัง `ROLE_PROVIDER` ในโค้ด | ✅ `LLM_PROVIDER` + `LLM_FALLBACKS` (ว่าง = พฤติกรรมเดิม) |
| §3 แยกชนิด error | ❌ **ไม่มี try/except รอบการเรียกโมเดลเลย** | ✅ 3 ชนิด + เทสต์ครอบทุกแถวของตาราง |
| §4 ห้ามสลับเงียบ | ❌ | ✅ ป้าย `🤖 ทำโดย …` ในผลงาน + `provider`/`model` ในทุกข้อความบน bus |
| §6 ทุกเจ้าล่ม → degrade | ⚠️ ได้เฉพาะตอน**ไม่มีคีย์** | ✅ ตั้งคีย์แล้วพัง → `escalated` + รอบรัน `failed` พร้อมเหตุ |

- **`agents/providers.py` = ผิวสัมผัสเดียว** — ห้าม import SDK ของเจ้าไหนนอกไฟล์นี้ (กติกาใหม่ §9.1.13)
  · `call_chain()` เป็นทางเดียวที่โค้ดอื่นเรียกโมเดล (รวม PM Agent ที่เคยเรียก `anthropic` ตรง)
- **`ClaudeExecutor` → `SoloExecutor`** — ชื่อเดิมจะโกหกทันทีที่มันเรียก OpenAI ได้
- **`in_progress → escalated`** เส้นใหม่ใน state machine (แก้ frontend `types.ts` คอมมิตเดียวกัน)
  — เดิม task ที่ AI ล่มกลางคันจะค้าง `in_progress` ให้มาแก้มือ
- **หน้า `/settings`**: กรอกคีย์ (mask เสมอ) · เลือกตัวหลัก/ลำดับสำรอง · **ปุ่มทดสอบรายเจ้า**
  ที่บอกด้วยว่าพังแบบไหน · เขียน `.env` แบบไม่มี BOM + สำรองก่อนทุกครั้ง · มีผลทันทีไม่ต้อง restart

**ยิงกับ API จริงทั้ง 3 เจ้า (ครั้งแรกของรีโปนี้ที่ทดสอบเจ้าอื่นนอกจาก Anthropic)**

| Verify ตามใบสั่งงาน | ผล |
|---|---|
| เจ้าหลักใช้ไม่ได้ → ทำงานต่อด้วยตัวสำรอง + บอกว่าใช้ตัวสำรอง | ✅ ตั้ง Gemini (คีย์เสียจริง) เป็นตัวหลัก · งานเสร็จด้วย Anthropic พร้อมป้าย `🤖 ทำโดย anthropic/claude-sonnet-5 — ตัวสำรอง` |
| ทุกเจ้าใช้ไม่ได้ → degrade อย่างมีศักดิ์ศรี | ✅ รอบรัน `failed` + error ระบุเจ้า+ข้อความจริง (`401 UNAUTHENTICATED…`) · task `escalated` rev 0 |
| โจทย์ผิด → ห้ามวนสลับเจ้า | ✅ ตั้งชื่อรุ่นผิด → หยุดที่เจ้าแรก · error ไม่มีคำว่า openai · **token = 0** |
| มีเทสต์ครอบตารางแยก error | ✅ `test_llm_providers.py` 22 เคส (+ `test_settings_api.py` 11 เคส) |

- **ผลข้างเคียงที่มีค่า:** ✅ **OpenAI `gpt-5.2` ใช้ได้จริง** · ✅ **Gemini ใช้ได้จริงหลังแก้ชื่อรุ่น**
  (ปิด Risk #5 ที่ค้างมาตั้งแต่ Sprint 4 — ทั้งสองเจ้าไม่เคยถูกยิงจริงมาก่อน)
  - ⚠️ **บทเรียน:** รอบแรกผมสรุปว่า "คีย์ Gemini เสีย" จากข้อความ error รอบเดียว (401 ที่ไม่เสถียร)
    · พอไล่ต่อด้วย `ListModels` + ยิงตรงทั้ง 2 วิธียืนยันตัวตน พบว่า**คีย์ดีมาตลอด** และตัวปัญหาคือ
    `GEMINI_MODEL=gemini-3-pro` ที่ไม่มีอยู่จริง — **อย่าเชื่อ error รอบเดียว ตรวจให้ถึงต้นทาง**
- pytest 133 → **170** · ruff clean · `npm run build` ผ่าน (route `/settings` ใหม่)

### เปิดโปรเจกต์ใหม่ "ของจริง" ได้จากบอร์ด (2026-08-14) — ADR-05 ครบ S1-S3

รวม `new-project-studio` เข้ามาเป็น**ความสามารถ** ไม่ใช่ service ที่สอง (`:8848` เลิกต้องจำ)

| เฟส | ของที่ได้ |
|---|---|
| **S1** | `POST /api/projects/bootstrap` — โฟลเดอร์จริง + เอกสารกำกับ + `_CANON` pointer + git init **แล้วลงบอร์ดพร้อม task sign-off ในคราวเดียว** · ไม่เรียก AI · ไม่ auto-commit |
| **S2** | หน้า `/projects/new` มีโหมด "เปิดโปรเจกต์ใหม่ของจริง" (target/purpose/stack/relation) แล้วโชว์ว่าสร้างอะไรไปบ้าง |
| **S3** | อัปโหลดไฟล์ดีไซน์ → ดึงข้อความ (`md/txt/pdf/docx`) → **คนตรวจ requirement ก่อน** → ส่งให้ PM แตกงาน · และ `POST /:id/deliverables` เอาผลงานของ task ไปเขียนเป็นไฟล์จริง |

- **สิ่งที่ไม่ยกเข้ามาโดยตั้งใจ:** `ai_fill` ที่เรียก `claude -p` CLI — ขัด §9.1.13 (ทุก LLM call
  ผ่าน `providers.py`) และงานเขียนเอกสารจากดีไซน์ได้ประโยชน์จากบอร์ดมากกว่า
  (กติกาห้ามกุ · reviewer · audit · โทเคนแยกเจ้า · ลำดับสำรอง)
- 🔒 **รั้วของการเขียนไฟล์:** `projects.local_path` (migration `a1c8e5f92d47`) — เขียนได้เฉพาะ
  ใต้โฟลเดอร์ของโปรเจกต์นั้น · `..` ถูกปฏิเสธ · **สำรองไฟล์เดิมก่อนทับเสมอ** · UTF-8 ไม่มี BOM
- ✅ **ตรวจกับของจริงแล้ว**: bootstrap โปรเจกต์ทดสอบลง `D:\Dev_Proj\4_RND\` ได้ครบ
  (7 ไฟล์จาก kit + เอกสาร dev 3 ไฟล์ + git init) แล้วลบทิ้งเรียบร้อย
- pytest 183 → **188** · ruff clean · `npm run build` ผ่าน

### ข้อมูลขาดจุดเดียวต้องไม่ทำให้ทั้งเอกสารไม่ถูกผลิต (2026-08-14)

อาการเดียวกันซ่อนอยู่ 2 ที่ — **PM ผูก dependency ผิด** และ **reviewer ยกงานให้คนเกินจำเป็น**

- **PM:** งานที่รอข้อมูลจากคน **ห้ามเป็น `depends_on` ของงานส่งมอบ** · ให้ผลิตฉบับเต็ม
  พร้อมช่องว่างติดป้าย `[รอข้อมูล: <อะไร> จาก <ใคร>]` แล้วแยก "เติมตัวเลขทีหลัง" เป็น task ต่างหาก
- **Reviewer:** `needs_human` = งานที่**ติดทั้งชิ้น** เท่านั้น · ขาดบางจุดที่ติดป้ายไว้แล้ว → **approve**
  · เกณฑ์ที่ใช้ตัดสินได้จริง: *ตัดส่วนที่ขาดออกแล้วผลงานยังมีประโยชน์กับคนอ่าน = approve*
- **วัดกับโจทย์เดิมเป๊ะ** (`17db2a67` → `662c3f43`):

  | | ก่อน | หลัง |
  |---|---|---|
  | คู่มือฉบับเต็ม | **ไม่ถูกผลิตเลย** | ✅ `done` 4,274 ตัวอักษร |
  | งานที่ต้องรอคน | ลาม 3 task ค้าง | เหลือตัวเดียว (`escalated`) · ตัวเติมทีหลังรอเป็น `planned` |
  | เนื้อในช่องที่ขาด | — | `[รอข้อมูล: …]` + "ต้องการข้อมูลจากคน:" · **ไม่มีการกุ** |

- 🔎 **ความเสี่ยงที่จดไว้ 3 ส.ค. เกิดขึ้นจริงและถูกจับได้ในรอบนี้:** reviewer ยกคู่มือที่ตัวเอง
  บอกว่า "เขียนครบ ภาษาเข้าใจง่าย ไม่มีการกุข้อมูล" ให้คนทั้งชิ้น เพราะไม่รู้ว่าปุ่มอยู่ตรงไหนบนจอ
  ⇒ **การวัดซ้ำมีค่าจริง** ไม่ใช่พิธีกรรม

### เปิดตรวจ callback ของ CI จริง + เทสต์ deployments เลิกเด้ง (2026-08-14)

- **`DEPLOY_CALLBACK_SECRET` ตั้งจริงแล้วทั้ง 2 ฝั่ง** — backend `.env` + GitHub secret
  `DEP_PM_CALLBACK_SECRET` (`ohho2518/d_DEP-PM_Platform`) · ลายนิ้วมือตรงกัน `d51192a17770`
  · ยิงจริง: ไม่แนบ header → **401** · แนบถูก → 404 (ผ่านด่าน) ⇒ **ปิด Risk #1 เต็มตัว**
- ⚠️ **workflow template เดิมไม่ได้ส่ง header** — ถ้าไม่แก้พร้อมกัน CI จะโดน 401 เงียบ ๆ (แก้แล้ว)
- **เทสต์ deployments เลิก flaky** — ต้นเหตุวัดได้: `utcnow()` **400 ครั้งติดกันได้ค่าเดียว**
  (นาฬิกา Windows ~15.6 ms) · แก้ด้วย tie-break `id` ใน query + เทสต์กำหนดเวลาเอง
  · **ไม่ต้อง migration** เพราะปัญหาอยู่ที่ความละเอียดของนาฬิกา ไม่ใช่ schema (ผ่าน 6 รอบติด)

### นับโทเคนแยกตามผู้ให้บริการ (2026-08-14) — เปิดทาง §5 ของใบสั่งงาน

ช่องว่างที่**ทั้งบ้านยังไม่มีใครทำ** (คู่มือกลางเขียนไว้เองว่า "ต้องนับโทเคนต่อเจ้าก่อน
ถึงจะมีถังให้แยก") · รอบ Team Mode เมื่อเช้าทำให้เห็นปัญหาชัด: ตัวเลข 7,110/2,654 ของโปรเจกต์นั้น
เป็น dev(OpenAI) + reviewer(Anthropic) **ปนกันในช่องเดียว** แยกไม่ออกว่าใครกินเท่าไร

- **`tasks.token_usage` (JSON, nullable)** — migration `f3a9c1d7e2b8` · apply กับ DB จริงแล้ว
  (57 tasks ครบ · สำรองไว้ที่ `BackUp/TokenUsagePerProvider_20260814_125530/`)
- **`GET /api/projects/:id/usage`** — รวมทั้งโปรเจกต์ แยกเจ้า + `untracked`
- **`untracked` คือหัวใจของความซื่อตรงตรงนี้** — งานเก่าแยกที่มาไม่ได้จริง จึงโชว์แยกไว้
  แทนการเดาว่าเป็นของ Anthropic (ตรวจแล้ว: โปรเจกต์ Team Mode ตกช่องนี้ทั้ง 7,110/2,654)
- ✅ **ตรวจกับงานสด 1 ชิ้น**: `by_provider` = anthropic 3,208 in / 651 out · **calls 2**
  (dev + reviewer) · `untracked` = 0 ⇒ เส้นทางใหม่เก็บครบทุก call
- **ยังไม่แปลงเป็นเงิน** โดยตั้งใจ — ตารางราคาเปลี่ยนบ่อยและต้องมาจากเจ้าของ ไม่ใช่ตัวเลขที่เดาเอง
- pytest 170 → **175** · `npm run build` ผ่าน (หน้าบอร์ดแสดงรายละเอียดต่อ task แล้ว)
- 🐘 **ตรวจบน PostgreSQL ด้วย** (จุดที่ migration เคยพังมาแล้ว): suite **175/175 บน PG 17** ·
  `alembic upgrade head` บน DB เปล่าเดินครบทั้ง 5 revision · คอลัมน์ลงเป็น `json` nullable
  ตาม ADR-01 · **ต้อง `docker start dep-pm-pg-test` ก่อน** (container ดับไปตั้งแต่ ~5 ส.ค.)

### เปิดใช้ลำดับสำรอง + Team Mode กับคีย์จริงครบ 3 เจ้า (2026-08-14)

- **`LLM_FALLBACKS=openai,google`** — chain จริงตอนนี้คือ `anthropic → openai → google`
  (ก่อนหน้านี้ของที่ทำเสร็จยัง**ไม่ถูกเปิดใช้** เจ้าหลักล่มก็ยังหยุดเหมือนเดิม)
- **Team Mode รันกับคีย์จริงสำเร็จ** (project `aab43c6a`, 2 tasks, done ทั้งคู่ rev 0):

  | บทบาท | ผลิตงาน | ตรวจงาน | token (รวม 2 ฝั่ง) |
  |---|---|---|---|
  | `dev` — เขียนข้อความแจ้งผู้ใช้ | **openai / gpt-5.2** | anthropic / claude-sonnet-5 | in 2,360 · out 228 |
  | `senior_architect` — ออกแบบวิธีเก็บสถิติโทเคน | **google / gemini-3-flash-preview** | anthropic / claude-sonnet-5 | in 4,750 · out 2,426 |

  ⇒ **ปิด Known Issue "OpenAI/Gemini ไม่เคยรันกับ service จริง" ได้ครบ** · role→provider ตาม
  Blueprint §9 ทำงานถูกทุกช่อง · ไม่มีป้ายตัวสำรอง = แต่ละบทบาทได้ตัวหลักของตัวเอง (ไม่มีการสลับ)
- 📌 **กติกาของบ้านข้ามค่ายได้จริง** — งานที่ Gemini ผลิตติดป้าย `[ตัวอย่างสมมติ]`, มีหัวข้อ
  "ต้องการข้อมูลจากคน:", และปิดท้ายว่าไม่ได้อ้างจากโค้ดจริง **โดยไม่ต้องแก้ prompt เพิ่ม**
  (กติกาอยู่ใน persona ซึ่งไม่ผูกกับผู้ให้บริการ)
- 🔎 **สิ่งที่รอบนี้ทำให้เห็นชัด:** `tokens_input/output` ยัง**รวมของทุกเจ้าไว้ที่ task เดียว**
  (ตัวเลขข้างบนคือ dev + reviewer ปนกัน) ⇒ เพดานค่าใช้จ่ายแยกต่อเจ้า (§5 ของใบสั่งงาน) ยังทำไม่ได้
  จนกว่าจะแยกที่มาของโทเคน — บังเอิญว่างานที่ให้ Gemini ออกแบบคือเรื่องนี้พอดี (เก็บไว้ใช้ต่อได้)

### reviewer ได้เห็น `description` ของงานแล้ว (2026-08-14)

- `_review_prompt` เดิมส่งแค่ title + spec — reviewer จึงปฏิเสธงานที่ถูกต้องว่า *"ไม่มี description
  ต้นฉบับให้เทียบ จึงยืนยันไม่ได้ว่าไม่ได้กุ"* แล้ววนจนหมดโควตา revision → escalated
- เจอตอนรันทดสอบ failover กับงานจริง (เสียไป 2 รอบรีวิว) — **อาการเดียวกับบั๊ก upstream context
  ของ Phase 3a: คนตรวจไม่ได้รับวัตถุดิบชุดเดียวกับคนทำ**

### UAT รอบ 3 — วัดผลกติกาห้ามกุหลักฐานกับงานจริง (2026-08-03) — **ผ่าน**

d_CEO task `4eb918bd` → DEP-PM project `c8d5c50c` · โจทย์บังคับให้อ้าง "ข้อมูลการทำงานจริง"
(วัน-เวลาต่องาน · ชื่อผู้รับผิดชอบ · คำพูดของคนในทีม) ซึ่ง**ระบบนี้ไม่มีให้เลย** = โจทย์ที่ล่อให้กุ

| จุดวัด | ผล |
|---|---|
| PM แตกงาน | 6 tasks · **ขึ้นต้น spec เองว่า "ต้องการข้อมูลจากคน:"** และสั่งงานปลายน้ำให้เขียน "ข้อมูลไม่เพียงพอ" แทนการเดา |
| dev 3 ตัวที่ได้รัน | **ไม่กุแม้แต่จุดเดียว** — ไม่มีชื่อคน/quote/timestamp ที่ไม่มีอยู่จริง · ตัวอย่างติดป้าย `[ตัวอย่างสมมติ]` ครบ |
| **QC ของ d_CEO** | ✅ *"ทีมปฏิเสธที่จะแต่งตัวเลข/คำพูดสมมติอย่างถูกต้อง … **นี่คือพฤติกรรมที่ถูก ไม่ใช่ความบกพร่องของทีม**"* |
| verdict | `FIX (escalate)` → **`awaiting_approval` รอ Vinit** (ไม่มีชิ้นงานตามสั่งเพราะไม่มีข้อมูลต้นทาง) |

> **สรุป Next Task #1 เดิม: ปิดได้** — กติกาไม่ได้อยู่แค่ใน prompt แต่เปลี่ยนพฤติกรรมจริง
> ทั้งชั้น PM และชั้น dev และมีคนนอก (QC) ยืนยัน

### บั๊กที่รอบ 3 เปิดออกมา — งานที่ "ติดเพราะต้องรอคน" (แก้แล้ววันเดียวกัน)

รอบนี้มี task 2 ตัวที่**สถานการณ์เหมือนกันเป๊ะ** (ไม่มีข้อมูลต้นทาง ทำไม่ได้จริง) แต่จบคนละทาง:

| | `6dfb8c90` รวบรวมข้อมูลบันทึกการทำงาน | `6166543f` รวบรวมความเห็นผู้ปฏิบัติงาน |
|---|---|---|
| ผลรีวิว | ตีกลับ 2 รอบ → **escalated** | **approve → `done`** ตั้งแต่รอบแรก |
| ผลข้างเคียง | งานปลายน้ำ **3 ตัวค้างถาวร** · เสีย ~15k token | รายงานขึ้นว่า "เสร็จ 2" ทั้งที่เนื้อในบอกว่าทำไม่ได้ |

- 🔴 **reviewer เป็นคนบีบให้เกิดการกุเสียเอง** — รอบแรกสั่งว่า *"ต้อง revise โดยยืนยันว่าได้
  escalate คำขอข้อมูลนี้ไปยังผู้เกี่ยวข้องแล้วจริง"* ซึ่ง agent **ทำไม่ได้** (พิมพ์ข้อความได้อย่างเดียว)
  → รอบสอง agent เขียนว่า "ได้ดำเนินการ escalate แล้ว" → reviewer จับได้เองว่าไม่มีหลักฐาน
- 🔴 **approve งานที่ไม่มีชิ้นงาน = รายงานเกินจริง** — QC จับได้ตรง ๆ: *"ผลงาน 2 ชิ้นที่ 'เสร็จ'
  จริง ๆ แล้วเป็นเอกสารแจ้งว่าทำไม่ได้เพราะไม่มีข้อมูลต้นทาง"*
- ✅ **แก้ด้วย verdict ที่ 3 ของ reviewer: `needs_human`** → `escalated` **ตั้งแต่รีวิวแรก
  ไม่นับ revision** · ห้าม approve ว่าเสร็จ · ห้ามสั่ง revision ที่ agent ทำตามไม่ได้ ·
  กติกาห้ามกุขยายไปถึง **"การกระทำ"** (ห้ามอ้างว่าติดต่อ/ส่งเรื่องไปแล้ว)
- ✅ **ตรวจกับโมเดลจริง** (project `bc3a43b7` 1 task): reviewer ตอบ `needs_human: true`
  ตั้งแต่รอบแรก → `escalated` ที่ `revision_count = 0` · เหตุผลในรายงานขึ้นต้น
  "ต้องการข้อมูล/การตัดสินใจจากคน — …" (ตัดที่ 400 ตัวอักษรพร้อมบอกว่าตัด)
- ✅ **วัดกับโปรเจกต์ที่ปนกัน** (`17db2a67` — คู่มือปุ่มหยุดรอบรัน + สถิติที่ระบบไม่มี):
  PM แตกเป็น 4 tasks แล้วรันจริง →

  | task | ผล | verdict |
  |---|---|---|
  | เขียนเนื้อหาคู่มือ (ข้อมูลให้ครบในโจทย์) | **done** rev 0 | `approved` — **`needs_human=false`** |
  | ขอข้อมูลสถิติการใช้งานจริง | **escalated** rev 0 | **`needs_human=true`** |
  | เขียนหัวข้อสถิติ · รวมเล่ม | ค้าง `planned` | รอ dependency (พฤติกรรมเดิม) |

  ⇒ **reviewer ไม่ได้ใช้ `needs_human` พร่ำเพรื่อ** — งานที่ทำได้ยัง approve ตามปกติ
  (ยังเป็นตัวอย่างเดียว ดูอีก 1-2 รอบก่อนสรุปปิด)
- 📌 **ข้อสังเกตจากรอบวัดผล (ยังไม่แก้):** PM ผูก "รวมเล่ม" ไว้กับหัวข้อสถิติ ⇒ **ตัวเลขที่หายไป
  ตัวเดียวทำให้คู่มือทั้งฉบับไม่ถูกผลิตเลย** ทั้งที่เนื้อหา 80% เขียนได้แล้ว — ทางแก้ที่น่าจะถูก
  คือให้ PM สั่งผลิตฉบับที่มีช่องว่างติดป้ายไว้ ไม่ใช่บล็อกทั้งเล่ม
- pytest 126 → **133** · ruff clean

### ห้าม agent กุหลักฐาน (2026-08-03) — ปิด Next Task #1

- `NO_FABRICATION_RULE` ใน `agents/personas.py` ต่อท้าย PM/DEV/ARCHITECT + เกณฑ์ให้ reviewer
  จับการกุข้อมูล**ก่อนเรื่องอื่น** · PM ถูกห้ามเขียน spec ที่สั่งไปเก็บข้อมูลจริงถ้าไม่มีช่องทาง
- **ทางออกมาจากเคสจริง:** เคสที่ 2 (สมมติ endpoint แต่ disclose) QC ยอมรับ ⇒ กติกาจึงเป็น
  "แต่งได้ถ้าติดป้าย `[ตัวอย่างสมมติ]`" ไม่ใช่ห้ามยกตัวอย่างทั้งหมด
- `tests/test_personas.py` (12 เคส) ล็อกไว้ — ครอบทั้ง 6 ประเภทหลักฐานที่เคยถูกกุ + ทางออก
  + ลำดับความสำคัญของ reviewer + PM ยังจบด้วยคำสั่ง JSON (กันการต่อท้ายทำ format เพี้ยน)
- pytest **126/126** · ruff clean

### ใบสั่งงาน 2026-08-03 Ticket #3 (จากรอบตรวจของเลขา) — **ปิดครบ 5/5**

> ✍️ **ติ๊ก `[x]` ใน `d_CEO\docs\ORDER_TICKET_2026-08-03.md` แล้วตามคำสั่งของ Vinit (3 ส.ค.)**
> — เป็น**ข้อยกเว้นครั้งเดียวของกติกา AGENTS.md §14 "ห้ามแก้ไฟล์ในรีโปอื่น"** เพราะใบสั่งงาน
> ออกแบบให้ผู้รับติ๊กช่องของตัวเอง · แก้เฉพาะ 5 แถวของ Ticket #3 + หมายเหตุ 1 บล็อก
> ไม่แตะส่วนของทีมอื่น · สำรองไฟล์เดิมไว้ที่ `BackUp/OrderTicketTick_20260803_150050/`

| ข้อ | สถานะ | หลักฐาน |
|---|---|---|
| 3.1 งานค้าง `d89c03a8` | ✅ **ปิดจบ — QC ตอบ `PASS` → task เป็น `done`** | ตีกลับ `87a8d3f2` เข้าคิว → รัน 2 งาน done ทั้งคู่ (163 วิ) → รายงานรอบใหม่ → ยิง `POST /api/ceo/qc/:id` ปลดตามที่เจ้าของสั่ง → **`done` 15:01:08** |
| 3.2 ตรวจเงื่อนไข v6 | ✅ **ยืนยัน** | `report_project` ยิง **PATCH เดียว** พร้อม `status`+`output` — มีเทสต์ล็อกไว้ · เพิ่ม `qc_task()` + `POST /api/ceo/qc/:id` |
| 3.3 ไฟล์ค้าง commit | ✅ | อยู่ใน `f8848f0` (Phase 2) ตั้งแต่เช้า |
| 3.4 รายงานอ้าง `:8400` | ✅ **ยืนยัน** | โค้ดใช้ `:8500` · grep `backend/app`+`frontend/src` ไม่เหลือ 8400 · ของเก่าใน DB ปล่อยไว้ |
| 3.5 ตารางพอร์ต 3 ชุด | ✅ | ชี้ `_CANON\SERVICE_PORTS.md` ครบ + เพิ่มในบล็อก canon ของ AGENTS.md |

> ✅ **3.1 ปิดครบวงจรแล้ว (15:01):** งานค้าง `qc_review` เพราะ v6 ยิง QC เฉพาะตอน "เปลี่ยน**เข้า**"
> `qc_review` ส่วนงานนี้ค้างสถานะนั้นมาตั้งแต่ 2 ส.ค. (ตรงกับใบสั่งงานข้อ 1.2b) ⇒ **เจ้าของสั่งให้ปลด**
> → ยิง `POST /api/ceo/qc/a07f1fb2…` (ปุ่มที่ทำในข้อ 3.2 — ใช้งานจริงครั้งแรก ตอบใน 0.45 วิ)
> → QC ตรวจ **`PASS`** → task `done` · **งาน `qc_review` ค้างของทีม R&D เหลือศูนย์**
>
> 📌 QC ฝากไว้ (ไม่ blocker): เอกสารสมมติ endpoint แบบ generic REST ที่ไม่ตรงระบบจริงและตกชั้น Jarvis
> — agent disclose เองว่าเป็นตัวอย่างสมมติจึงยอมรับสำหรับงานทดสอบ · **เป็นอาการเดียวกับ
> "agent กุข้อมูล" ที่เป็นงานลำดับ 1 ของเรา** (Next Tasks #1)
>
> 🔎 **ยังเป็นคำถามค้างถึงฝั่ง d_CEO (ส่งไว้ใน `REQUEST_TO_CEO.md` §3.6 + หมายเหตุในใบสั่งงาน):** `output` ของ task
> ฝั่ง d_CEO **แกว่งไปมาระหว่าง 22,488 ↔ 49,345 ตัวอักษร** ในช่วง ~15 นาทีหลังเรารายงาน
> โดยสถานะไม่ขยับและไม่มีหัวข้อ QC ในทั้งสองเวอร์ชัน · **ฝั่งเรายิง PATCH ครั้งเดียว**
> (audit `ceo.reported` มี 2 แถว = เมื่อวาน + วันนี้) ⇒ การเขียนทับมาจากฝั่งเขา

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

**รองรับ AI หลายเจ้า + หน้า Settings (2026-08-14)**
- **ใหม่:** `backend/app/api/settings.py`, `backend/app/schemas/settings.py`,
  `backend/app/services/env_file.py`, `backend/tests/{test_llm_providers,test_settings_api}.py`,
  `frontend/src/app/settings/page.tsx`
- **แก้:** `backend/app/agents/{providers,runtime,pm}.py`, `backend/app/config.py`,
  `backend/app/main.py`, `backend/app/api/__init__.py`, `backend/app/orchestrator/{engine,state_machine}.py`,
  `backend/.env.example`, `backend/tests/{conftest,test_team_mode,test_orchestrator,test_personas}.py`,
  `frontend/src/lib/{types,api}.ts`, `frontend/src/app/layout.tsx`,
  `AGENTS.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`,
  `docs/{SYSTEM_DOCUMENTATION,API,SECURITY,RISK_REGISTER,runbook,REQUEST_TO_CEO}.md`
- **สำรอง:** `BackUp/MultiProvider_20260814_093915/` (23 ไฟล์ รวม `.env` จริง) +
  `BackUp/EnvSettings_*/` ที่หน้า Settings สร้างเองทุกครั้งที่เขียน (gitignored ทั้งคู่)

**verdict `needs_human` (2026-08-03)**
- **แก้:** `backend/app/agents/personas.py` (กติกา "ห้ามกุการกระทำ" + เกณฑ์ reviewer + ฟิลด์ JSON),
  `backend/app/agents/runtime.py` (`ReviewResult.needs_human`, parser),
  `backend/app/orchestrator/engine.py` (`_escalate()` ใช้ร่วม 2 เหตุ + สาขา `needs_human`
  + `ESCALATION_REASON_CHAR_LIMIT`), `backend/tests/{test_personas,test_orchestrator}.py`,
  `docs/{SYSTEM_DOCUMENTATION,runbook}.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`
- **สำรอง:** `BackUp/ReviewerNeedsHuman_20260803_161639/` (gitignored)

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

- **pytest 170/170 ผ่าน · ruff clean · `npm run build` ผ่าน**
- **ผู้ให้บริการ AI ใช้ได้ครบ 3 เจ้า** (ยิงจริง 2026-08-14): Anthropic ✅ · OpenAI ✅ · Gemini ✅
  · **chain ที่ใช้อยู่จริง: `anthropic → openai → google`** · `AGENT_MODE=solo`
  · แก้/ทดสอบได้เองที่หน้า `/settings` โดยไม่ต้อง restart
- ⚠️ **`test_deployments::test_list_deployments_newest_first_with_names` เด้งราว 1 ใน 5 รอบ**
  — ของเดิม ไม่เกี่ยวกับงานนี้: `order_by(created_at)` ชนกันเพราะนาฬิกา Windows หยาบ
  (บทเรียนเดียวกับที่เคยจดไว้เรื่อง `_ancestor_tasks`) · ยังไม่แก้ ต้องมีคอลัมน์ลำดับจริง = migration
- **วงจร d_CEO ↔ DEP-PM ใช้งานได้จริงแล้ว** (ยืนยันด้วยงานจริง 3 รอบ ไม่ใช่แค่ mock)
- **`/run` เป็นงานเบื้องหลังแล้ว** (202 + `run_id` · lock ต่อโปรเจกต์ · `GET /:id/run` ·
  ยกเลิกกลางทางได้) — ปิด Risk #3 ที่เคยบล็อกการใช้งานประจำ
- DB จริง migrate ถึง head `e5a91c73b204` · **รอบนี้ไม่มี migration** (แตะ prompt/engine/config เท่านั้น)
- **backend รันค้างอยู่ที่ `:8500`** (รีสตาร์ต 2026-08-14 เพื่อโหลดโค้ดใหม่ — **ไม่มี `--reload`**)
  · `.env` ถูกคืนค่าเดิมหลังทดสอบแล้ว (`llm_chain` = `["anthropic"]` ตามเดิม)
- 🧹 **ล้างบอร์ดแล้ว 2026-08-14: 15 → 7 โปรเจกต์** (สำรอง DB ก่อนที่
  `BackUp/CleanupTestProjects_20260814_142549/`) · เพิ่ม `DELETE /api/projects/:id` เพื่อทำให้ถูกทาง
  (มี audit) แทนการยิง SQL ตรง
  - **ลบไป 8 ตัว** = งานทดสอบที่ไม่ผูกกับเลขา (needs_human · failover · degrade · token · Team Mode)
    — **ผลการวัดถูกบันทึกไว้ในเอกสารแล้ว แต่ตัวโปรเจกต์เปิดดูย้อนหลังไม่ได้อีก**
  - **เหลือ 4 ตัวที่ลบไม่ได้** เพราะผูก `ceo_task_id` (guard ตอบ 409): `a07f1fb2` · `7ffa2d4f` ·
    `4d8004ff` · `c8d5c50c` — ตั้งใจไม่ตัดสายเอง และ**ตรวจสถานะฝั่งเลขาไม่ได้เพราะ d_CEO ล่ม**
- ✅ **d_CEO `:8000` สตาร์ตกลับแล้ว** (`D:\Dev_Proj\0_CORE\d_CEO\run_ceo.bat`) —
  `/health` ของเขาตอบ `llm_providers: ["anthropic"]` (ฝั่งนั้นทำ pattern เดียวกันแล้ว)
- ⚠️ **`:8400` (d_Jarvis web) ยังไม่ได้สตาร์ต** — `run_jarvis.bat` เรียก `python run.py` ซึ่งเป็น
  ตัวบอทที่ต่อออกแพลตฟอร์มภายนอก **ไม่ใช่เว็บเปล่า ๆ** จึงไม่สตาร์ตให้เองโดยไม่ถาม
- git: main สะอาด ณ ต้นรอบ (`2b9bf39`, push แล้ว) · **งานรอบนี้ยังไม่ commit** (รอผู้ใช้ตรวจ)

## Next Tasks

0. ✅ ~~รวม `new-project-studio` เข้ามา (ADR-05)~~ **ทำครบ S1-S3 + UI แล้ว 2026-08-14**
   · ปุ่ม "เขียนผลงานลงไฟล์" อยู่ในหน้า task detail แล้ว (โผล่เฉพาะโปรเจกต์ที่มีโฟลเดอร์จริง)
   · **ตรวจตัวอ่านกับ PDF ตัวจริงที่เคยทำ studio พังแล้ว** — `autopost-studio-mockup.pdf`
     มี NUL 18 ตัว → requirement ที่ออกมา 0 ตัว (มีเทสต์ล็อกไว้) · DOCX อ่านได้จริง
1. 🔴 **แยกคีย์ต่อรีโปที่คอนโซลผู้ให้บริการ** — ตราบใดที่ยังใช้คีย์ร่วมกัน บัญชีหมดเครดิต
   = ทุกรีโปตายพร้อมกันเหมือน 6 ส.ค. (ตัวสำรองช่วยได้แค่ตอน "เจ้านั้นล่ม") · **ต้องให้เจ้าของทำ**
1.1 ~~แยกโทเคนตามผู้ให้บริการ~~ ✅ **ทำแล้ว 2026-08-14** — เหลือขั้นถัดไปของ §5 คือ
   **ตั้งเพดานจริง**: ต้องมีตารางราคาต่อโทเคนจากเจ้าของก่อน (ระบบไม่เดาราคาเอง)
   แล้วค่อยตัดสินว่าเพดานอยู่ที่ระดับ project หรือ run และเกินแล้วให้หยุดหรือแค่เตือน
2. **รอ Vinit ตอบคำถามของ QC เรื่องงานรอบ 3** — d_CEO `4eb918bd` ค้าง `awaiting_approval`:
   จัดหาข้อมูลจริงให้ pipeline เดินต่อ **หรือ** ปิดรอบทดสอบว่าระบบทำงานถูกต้องแล้ว
   · **ฝั่งเรายิงอะไรต่อเองไม่ได้**
2. **ให้ PM ไม่บล็อกทั้งเล่มเพราะข้อมูลหายไปชิ้นเดียว** — รอบวัดผล `17db2a67` ชี้ว่า
   คู่มือที่เขียนได้ 80% ไม่ถูกผลิตเลยเพราะ "รวมเล่ม" ผูกกับหัวข้อสถิติที่ติด ·
   ทางที่น่าจะถูก: PM สั่งผลิตฉบับที่มี**ช่องว่างติดป้ายว่ารออะไรอยู่** แล้วให้คนเติมทีหลัง
   (ต้องคิดให้รอบคอบก่อนแก้ — กระทบวิธีแตกงานทั้งระบบ)
3. **ดู `needs_human` อีก 1-2 รอบ** ก่อนสรุปปิด — วัดแล้ว 2 ครั้ง (งานเดี่ยว + โปรเจกต์ปนกัน)
   reviewer ยังไม่ใช้เกินจำเป็น · เก็บสถิติต่อใน runbook §7
4. **ขอจากฝั่ง d_CEO** (ดู `docs/INTEGRATION_CEO.md` §7 + `docs/REQUEST_TO_CEO.md` ที่ยังไม่ได้ส่ง):
   ยืนยัน contract + ออก `INTEGRATION_DEPPM.md` · เหตุ `output` แกว่ง 22,488 ↔ 49,345 ตัวอักษร ·
   แก้เอกสารที่ยังเขียนว่า "merge DEP-PM เข้า Solo_CEO" (`d_Jarvis\docs\VISION.md` §5,
   `d_CEO\project_plan_solo_ceo.md` §9.1) — **ห้ามแก้ข้ามรีโป**
5. ~~**Team Mode กับคีย์จริง**~~ ✅ **ทำแล้ว 2026-08-14** (ดู Completed Work) — เหลือแค่
   ตัดสินใจว่าจะใช้ Team Mode เป็นค่าปกติไหม (ตอนนี้คืนเป็น `AGENT_MODE=solo` แล้ว)
6. **บอกทั้งบ้านว่า §5 ครึ่งแรกทำได้แล้ว** — ตอนนี้ DEP-PM เป็นรีโปแรกที่นับโทเคนต่อเจ้าได้
   (`tasks.token_usage` + `GET /:id/usage`) · รูปแบบลอกไปใช้ได้เลย ดู `docs/REQUEST_TO_CEO.md` §6
7. **แจ้ง d_CEO ให้อัปเดตแถว DEP-PM ใน `LLM_PROVIDER_PATTERN.md`** — ช่อง "บอกว่าใช้ตัวสำรองยังไง"
   ที่เป็น `—` ไม่จริงแล้ว (เขียนคำขอไว้ใน `docs/REQUEST_TO_CEO.md` — **ห้ามแก้ข้ามรีโป**)
8. ย้ายของจริงขึ้น PostgreSQL · ก่อน deploy สาธารณะ: security gate ใน `docs/SECURITY.md`
   — **เพิ่มความสำคัญ** เพราะหน้า `/settings` แก้คีย์ได้โดยไม่มี auth

## Known Issues

- **ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียว** — restart uvicorn ระหว่างรอบรัน = งานหยุด
  และประวัติรอบรันหาย (`GET /run` → 404) **ผลงานที่ commit แล้วไม่หาย** กด Run ใหม่ทำต่อได้
- ⚠️ **reviewer ตอบคำตัดสินโดยพูดกับระบบ ไม่ใช่กับคนอ่าน** — คอมเมนต์จริงของรอบตรวจ `needs_human`
  มีประโยคจาก prompt ปนมา ("ห้าม approve ว่าเสร็จ และห้ามสั่ง revision ต่อ") · ไม่กระทบการทำงาน
  แต่ไปโผล่ในรายงานถึงเลขา — ถ้าเจอบ่อยค่อยขัดถ้อยคำใน persona
- ⚠️ **PostgreSQL ผ่านเทสต์แล้วแต่ยังไม่เคยรันของจริง** — DB ที่ใช้งานจริงยังเป็น SQLite
  (ย้ายเมื่อ infra พร้อม ตาม runbook §4)
- ✅ ~~CI callback secret ยังไม่ได้ตั้งค่าจริง~~ **ตั้งแล้วทั้ง 2 ฝั่ง 2026-08-14** — ตรวจโดยยิงจริง
  (401 เมื่อไม่แนบ header) · หมายเหตุ: ตอนนี้ workflow ที่ไม่ส่ง header จะถูกปฏิเสธ
  ⇒ ถ้าไปติดตั้งใน repo อื่น ต้องใช้เทมเพลตฉบับใหม่ที่ส่ง `X-DEP-PM-Secret`
- ⚠️ **ชื่อรุ่นของ Google เปลี่ยนบ่อยและรุ่นเก่าถูกปิดสำหรับผู้ใช้ใหม่** — `gemini-3-pro` ไม่มีจริง,
  รุ่น 2.5 ทั้งหมดตอบ *"no longer available to new users"* · ใช้ปุ่มทดสอบที่ `/settings` ยืนยันทุกครั้ง
  ที่เปลี่ยนรุ่น · **ชั้น pro ของ Gemini ติด 429 quota** (ต้องมี billing) ใช้ได้แต่ชั้น flash
- **token accounting ของ OpenAI/Gemini ยังไม่เคยวัดกับงานเต็มรอบ** (ping สั้นเท่านั้น)
- 🔴 **คีย์ยังใช้ร่วมกันข้ามรีโป** — ตัวสำรองไม่ช่วยตอน "บัญชีหมดเครดิต" (ทุกรีโปเจอพร้อมกัน)
  · ต้องแยกคีย์ที่คอนโซลผู้ให้บริการ = งานของเจ้าของ ทำจากในโค้ดไม่ได้
- 🔴 **หน้า `/settings` แก้คีย์ได้โดยไม่มี auth** — ยอมรับได้เฉพาะขณะ bind `127.0.0.1`
  **ห้าม expose พอร์ต 8500 ออกนอกเครื่องจนกว่าจะมี authentication** (RISK #5.2)
- ⚠️ **นาฬิกาของเครื่องนี้แยกแถวที่สร้างในคำขอเดียวกันไม่ได้** — `utcnow()` 400 ครั้งติดกัน
  ได้ค่าเดียว (ก้าวทีละ ~15.6 ms) · เทสต์ที่เคย flaky แก้แล้ว แต่ **ทุกที่ที่เรียงด้วย `created_at`
  ต้องมี tie-break** ไม่งั้นลำดับสลับเองได้ (จุดที่ยังไม่ตรวจ: portfolio, message log)
- Task ที่ acceptance criteria ต้องการ artifact จริง (repo/CI) จะ escalate เสมอ — พฤติกรรมถูกต้อง
  แต่ต้องเขียน spec ให้ deliverable เป็นเอกสาร/โค้ด (บทเรียน UAT ใน runbook §7)
- uvicorn `--reload` บน Windows บางครั้งไม่จับไฟล์ที่แก้ — endpoint ใหม่ 404/405 ให้ restart
  · **ตัวที่รันค้างอยู่ตอนนี้ไม่มี `--reload`** — แก้ persona/prompt แล้วต้องรีสตาร์ตเองเสมอ
  (ไม่งั้นทดสอบไปก็ยังเป็นพฤติกรรมเก่า — เจอจริงวันนี้)

## Decisions Made

### 2026-08-14 (รองรับ AI หลายเจ้า)

8. **ขยาย `agents/providers.py` ให้เป็นผิวสัมผัสเดียว แทนการสร้าง `app/llm.py` ใหม่ตามรีโปอื่น**
   — รีโปนี้มี seam อยู่แล้ว (`BUILDERS` + lazy import) ซึ่งคู่มือกลางยกเป็น "ของดีของ DEP-PM"
   · สร้างไฟล์ใหม่ = มีผิวสัมผัส 2 ที่ = สิ่งที่ใบสั่งงานพยายามกำจัด
8.1 **`AGENT_MODE` อยู่ต่อ ไม่ยุบรวมกับ `LLM_PROVIDER`** — ตอบคนละคำถาม: `AGENT_MODE`
   = "บทบาทไหนใช้เจ้าไหนเป็นตัวหลัก" · `LLM_PROVIDER`/`LLM_FALLBACKS` = "ล้มแล้วไปต่อที่ใคร"
   (ใช้ร่วมกันทั้งสองโหมด)
8.2 **ทุกเจ้าล่ม ≠ ผลิตงาน deterministic แล้วนับว่าเสร็จ** — งานที่ดูเหมือนเสร็จแต่ไม่มีเนื้อคือ
   "รายงานเกินจริง" ที่ QC จับได้เมื่อ 3 ส.ค. ⇒ escalate + รอบรัน `failed` · ทาง deterministic
   สงวนไว้เฉพาะ **"ไม่มีคีย์เลยทั้งระบบ"** ซึ่งเป็นสัญญาเดิม (§9.1.8)
8.3 **`LlmRequestError` ไม่ escalate** — โจทย์ผิด (ชื่อรุ่น/prompt) แก้แล้วกด Run ใหม่ได้เลย
   จึงปล่อย rollback ให้ task กลับเป็น `planned` แทนการทิ้งไว้ที่ `escalated` ให้คนมาตีกลับเอง
8.4 **เก็บคีย์ใน `.env` ไม่ใช่ในฐานข้อมูล** — `dep_pm.db` มีสำเนาไปที่อื่น (BackUp) และ
   ไม่ได้เข้ารหัส · `.env` เป็นที่ที่ทุกอย่างอ่านอยู่แล้วและ gitignored อยู่แล้ว
8.5 **แก้ `Settings` instance เดิมในหน่วยความจำ ไม่ใช่ `get_settings.cache_clear()`** —
   มีโมดูลที่จับ instance ไว้ตั้งแต่ import (`main.settings`) ล้าง cache แล้วจะยังถือค่าเก่า

### 2026-08-03 (verdict `needs_human`)

7. **ให้ reviewer มีคำตัดสินที่ 3 แทนการปรับถ้อยคำ prompt เฉย ๆ** — ทางเลือกแค่ approve/revision
   ทำให้เกิดความเสียหาย 2 แบบพร้อมกันในรอบ 3 (บีบให้กุการกระทำ · approve งานเปล่าเป็น done)
   ซึ่ง**เป็นผลจากโครงสร้างของทางเลือก ไม่ใช่ความไม่ชัดของถ้อยคำ**
7.1 **`needs_human` ไม่นับเป็น revision** — งานติดเพราะขาด input ไม่ใช่ความผิดของคุณภาพงาน
   ถ้านับ จะเปลืองโควตา revision ของงานที่คนแก้เหตุแล้วตีกลับเข้าคิวใหม่
7.2 **ยังใช้สถานะ `escalated` เดิม ไม่เพิ่มสถานะ `blocked`** — ความหมาย ("ต้องการคนรับช่วง")
   ตรงอยู่แล้ว · เพิ่มสถานะใหม่ต้องแก้ 6 จุดตามกติกา §13 และทำให้ทั้ง eco ต้องรู้จักคำใหม่
   โดยไม่ได้อะไรเพิ่ม — สิ่งที่ต่างคือ**เหตุผล** ซึ่งอยู่ในข้อความ broadcast อยู่แล้ว
7.3 **ฟิลด์ใหม่มีค่าปริยาย `False`** — provider/เทสต์เดิมที่สร้าง `ReviewResult` 2 ฟิลด์
   ทำงานเหมือนเดิมทุกประการ (จุดเสียบ `PersonaExecutor` ไม่ถูก break)

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

1. 🔴 **งานรอบ 3 ที่ QC ส่งกลับมา (`awaiting_approval`) — เลือกทางไหน:** จัดหาข้อมูลจริงของทีม R&D
   ให้ pipeline เดินต่อ **หรือ** ปิดรอบทดสอบว่า "ระบบทำงานถูกต้องแล้ว"
   · ถ้าเลือกทาง 1 ต้องบอกด้วยว่าข้อมูลอยู่ที่ไหน (ไฟล์/ระบบ) เพราะ agent เข้าถึงเองไม่ได้
2. **โจทย์ทดสอบรอบหน้าควรเป็นงานแบบไหน** — 3 รอบที่ผ่านมาเป็นงานเอกสารล้วน · ถ้าอยากวัด
   `needs_human` ให้เห็นชัด ควรเป็นโปรเจกต์ที่**ปนกัน**ระหว่างงานที่ agent ทำได้เองกับงานที่ต้องรอคน
3. **โปรเจกต์ทดสอบ 3 ตัวในบอร์ด** (`c8d5c50c`, `bc3a43b7`, ของเก่า) — เก็บไว้เป็นหลักฐาน
   หรือให้ลบทิ้ง (ลบได้ปลอดภัย ไม่กระทบข้อมูลงานจริง)
4. PostgreSQL / OPENAI+GEMINI keys — อันไหนพร้อมก่อน (กระทบลำดับ Phase 3b)
