# CHANGELOG — DEP-PM Platform

## 2026-08-15 — เส้นทางงาน 6 ขั้น + ชนิดงาน + ไอเดียขึ้นบอร์ด (ADR-06)

ผู้ใช้บอกว่า "UI ยังเข้าใจยาก" — ต้นเหตุคือหน้าจอจัดตาม**ของในระบบ** ไม่ได้จัดตาม**เส้นทางที่งานเดิน**
นี่คือก้อนแรกของการรื้อ: ทำให้ทุกหน้าตอบได้ว่า *ตอนนี้อยู่ตรงไหน · ต่อไปทำอะไร*

- **แถบ 6 ขั้น** (ไอเดีย → โครงสร้าง → แผนงาน → ลงมือ → ส่งขึ้นระบบ → การตลาด) พร้อมสีประจำขั้น
  อยู่ทั้งบนบอร์ดและหน้ารวม + บรรทัด **"ขั้นต่อไป: …"** ที่บอกงานถัดไปเป็นประโยคเดียว
- 🔴 **ขั้นคำนวณสดจากของจริง ไม่ได้เก็บในฐานข้อมูล** — อ่านจากโฟลเดอร์ · สถานะ task · deployment
  ที่มีอยู่จริง ⇒ **โกหกไม่ได้** (บทเรียนจาก 3 ส.ค. ที่รายงานว่าเสร็จทั้งที่ไม่มีชิ้นงาน)
- **ชนิดงาน `projects.kind` 3 แบบ** (migration `b6e2f4a81c39` · `server_default='code'` ⇒ ของเดิม
  หมายความเหมือนเดิมทุกประการ):
  - `code` ครบ 6 ขั้น · `doc` **ข้ามขั้นโครงสร้าง** และเรียกขั้น 5 ว่า **"ส่งมอบ"**
  - `idea` เดิน 3 ขั้นแรกแล้วจบที่ปุ่ม **"ยกระดับเป็นโปรเจกต์จริง"** (`POST /:id/promote`)
    — งานที่ศึกษาไว้อยู่ครบ ไม่ใช่การเริ่มใหม่ · scaffold ล้ม = ไม่เปลี่ยนชนิด
- **ดึงไอเดียเก่าขึ้นบอร์ดได้** (`/ideas/preview` + `/ideas/import`) — **อ่านอย่างเดียว ไม่แตะไฟล์ต้นทาง**
  · ยิงซ้ำไม่งอก · `.md` + `.html` ชื่อเดียวกันนับเป็นเรื่องเดียว · ไฟล์เดี่ยว**ไม่ผูก `local_path`**
  (โฟลเดอร์รวมเป็นของหลายคน ผูกไว้ = เปิดสิทธิ์เขียนทับกัน)
- **ทำจริงบนเครื่องแล้ว:** ดึงไอเดีย **9 เรื่อง** จาก `D:\Dev_Proj\IDEAs` + `D:\Dev_Proj\6_KM\Ideas`
  ขึ้นบอร์ด (ชื่อไทยครบถ้วน · โฟลเดอร์ได้ `local_path` · ไฟล์เดี่ยวไม่ได้) · ยิงซ้ำได้ 0 รายการ
- กติกาใหม่ **§9.1.15**: ห้ามเก็บ stage เป็นคอลัมน์ ห้ามคำนวณขั้นฝั่ง frontend
- pytest 214 → **250** (`test_stages.py` 22 · `test_ideas_import.py` 14) · ruff clean · `npm run build` ผ่าน

## 2026-08-15 — ปุ่มเปิดระบบ `Start-DEP-PM.exe`

เปิดระบบเคยต้องใช้ 2 เทอร์มินัลกับคำสั่ง 6 บรรทัด และพลาดซ้ำ ๆ อยู่ 3 จุด — ตอนนี้ดับเบิลคลิกครั้งเดียว

- **ตรวจก่อนสตาร์ต:** มี venv ไหม · สร้าง `.env`/`.env.local` จากตัวอย่างให้ถ้ายังไม่มี ·
  **เตือนเมื่อ `API_TOKEN` ไม่ตรงกับ `NEXT_PUBLIC_API_TOKEN`** (อาการคือหน้าเว็บขึ้น
  "โหลดบอร์ดไม่ได้" ทั้งที่ backend ปกติ — เคยหลงไปไล่ผิดที่)
- **ฐานข้อมูล:** อัปเกรดให้ตรง head อัตโนมัติ โดย**สำรอง `dep_pm.db` ไว้ก่อนเสมอ** (Rule 3)
  · อัปเกรดล้ม = ไม่สตาร์ตระบบ และข้อมูลเดิมไม่ถูกแตะ
- **ไม่สตาร์ตซ้อน** — พอร์ตมีคนใช้อยู่แล้วและตอบ `/health` แบบ DEP-PM → ใช้ตัวเดิม
  (เคยเกิดจริง 14 ส.ค.: uvicorn 2 ตัวบนพอร์ตเดียว ตัวที่ถือพอร์ตเป็นคนละตัวกับที่คิด)
- **ไม่แตะ `:8000` (d_CEO) / `:8400` (d_Jarvis)** — แสดงสถานะให้ดูเฉย ๆ · ปุ่มหยุดฆ่าเฉพาะ
  `:8500`/`:3000` และตรวจก่อนว่าใช่ระบบเราจริง
- เมนูหลังเปิด: **[O]** เปิดหน้าเว็บ · **[S]** หยุดระบบ (หยุดของรอบก่อนได้ด้วย) · **[Q]** ออกโดยปล่อยรันต่อ
- **ชอร์ตคัต "เปิดระบบ DEP-PM" บนหน้า Desktop** — สร้าง/ซ่อมด้วย `.\tools\launcher\make-shortcut.ps1`
  · ชื่อภาษาไทยอยู่ในไฟล์ `shortcut-name.txt` แยกต่างหาก เพราะสคริปต์ `.ps1` ต้องเป็น ASCII
- วัดจริงบนเครื่อง: **cold start 7.8 วินาที** · log อยู่ที่ `logs\backend.log` / `logs\frontend.log`
- 🔧 **บทเรียนใหม่:** `.ps1` ที่มีภาษาไทยแต่ไม่มี BOM → PowerShell 5.1 อ่านเป็น ANSI แล้ว
  **parse พังทั้งไฟล์** · กติกาบ้านคือ UTF-8 ไม่มี BOM ⇒ สคริปต์ `.ps1` ต้องเป็น ASCII ล้วน
  (ตัวโปรแกรม `.py` ใช้ไทยได้ตามปกติ)

## 2026-08-14 — เพดานค่าใช้จ่ายต่อโปรเจกต์ (§5 ใบสั่งงาน 2026-08-06 — ช่องสุดท้ายที่ค้าง)

- `GET /api/projects/:id/usage` เพิ่ม **`cost_usd` ต่อเจ้า + บล็อก `budget`** (ใช้ไป/เพดาน/เกินหรือยัง)
  · คิดจาก `LLM_PRICE_<เจ้า>_IN/OUT` (ราคาต่อ 1 ล้านโทเคน) × โทเคนที่นับได้
- **`LLM_BUDGET_USD` + `LLM_BUDGET_ACTION`** — เพดาน**ต่อโปรเจกต์** · `warn` (ปริยาย) = เตือนอย่างเดียว ·
  `stop` = รอบรัน**ไม่หยิบ task ใหม่** แล้วจบเป็น `succeeded` พร้อม **`stopped_reason`**
  (ช่องใหม่ใน `GET /:id/run` — **คนละช่องกับ `error`**: ไม่ใช่ความล้มเหลว)
  · ถามก่อนหยิบงานใหม่เท่านั้น **ไม่ตัดกลาง task** ที่จ่ายค่าโทเคนไปแล้ว (เจตนาเดียวกับปุ่มยกเลิก)
- หน้า `/settings` ตั้งเพดาน + โหมดได้เอง (มีผลทันที ไม่ต้อง restart) และแสดงตารางราคาที่ใช้คิดเงิน
  แบบ**อ่านอย่างเดียว** · บอร์ดขึ้นแถบ `💰 ใช้ไปประมาณ $x / เพดาน $y` พร้อมยอดแยกรายเจ้า
- ⚠️ **ตัวเลขเงินทุกจุดเป็น "ประมาณการ"** จากราคาประกาศ ณ 2026-08-14 ที่**ยังไม่ยืนยันกับบิลจริง** ·
  โทเคนของงานเก่าที่ระบุเจ้าไม่ได้ **ไม่ถูกคิดเงิน** แต่ระบบบอกไว้ (`excludes_untracked`)
  ว่าของจริงสูงกว่านี้ — ห้ามอ่านว่า "ใช้น้อย"
- pytest 202 → **214** (`test_usage_budget.py` 11 เคส: สูตรคิดเงิน · warn ทำงานต่อ · stop หยุดก่อน
  task ถัดไป · API บอกเหตุที่หยุด · ตั้งเพดานจากหน้าเว็บแล้วเป็น **ตัวเลข** ไม่ใช่ข้อความ)

## 2026-08-14 — รองรับ AI หลายเจ้า + หน้าตั้งค่าคีย์ (ใบสั่งงาน 2026-08-06)

**สลับผู้ให้บริการได้โดยไม่แก้โค้ด และไม่สลับเงียบ**

- **`LLM_PROVIDER` + `LLM_FALLBACKS`** — ตัวหลักและลำดับสำรองมาจาก env (ว่าง = พฤติกรรมเดิม)
  · ใช้ร่วมกันทั้ง Solo และ Team Mode (Team ยังมีตัวหลักต่อบทบาทตาม Blueprint §9 เหมือนเดิม)
- **แยกชนิด error 3 แบบ** ใน `agents/providers.py` (ผิวสัมผัสเดียวที่คุยกับผู้ให้บริการ):
  บัญชีใช้ไม่ได้ → **สลับทันที** · ชั่วคราว → ลองซ้ำก่อน · **โจทย์ผิด → ห้ามสลับ** (จ่ายสองเจ้าเปล่า ๆ)
  · เก็บ **body ของ error** ไม่ใช่แค่รหัสสถานะ
- **ห้ามสลับเงียบ** — ผลงานที่ทำด้วยตัวสำรองมีป้าย `🤖 ทำโดย <เจ้า>/<รุ่น> — ตัวสำรอง` ต่อท้าย
  และ `provider`/`model` ถูกบันทึกในทุกข้อความบน bus (รวมผลตรวจของ reviewer)
- **ทุกเจ้าล่ม = หยุดอย่างมีศักดิ์ศรี** — task ไป `escalated` พร้อมเหตุที่บอกว่าเจ้าไหนพังเพราะอะไร
  (**ไม่ค้าง `in_progress` ให้มาแก้มือ** — เพิ่มเส้น `in_progress → escalated` ใน state machine)
  · รอบรันจบเป็น `failed` พร้อมข้อความเดียวกัน · `/health` เพิ่ม `llm_providers` + `llm_chain`
- **PM Agent เลิกเรียก SDK ตรง** — ใช้ลำดับสำรองเหมือนที่อื่น · degrade แล้วเขียน**เหตุ**ลงใน spec
  ของ task ที่สร้าง (เดิมได้แผนเปล่า ๆ โดยไม่บอกว่าทำไม)

**หน้าใหม่ `/settings` — กรอกคีย์ · เลือกตัวหลัก/ลำดับสำรอง · ปุ่มทดสอบรายเจ้า**

- บันทึกลง `backend/.env` (สำรองไฟล์เดิมทุกครั้ง · UTF-8 **ไม่มี BOM**) แล้ว**มีผลทันทีไม่ต้อง restart**
- ปุ่มทดสอบยิงจริงหนึ่งครั้งต่อเจ้า แล้วบอกด้วยว่าพังแบบไหน (บัญชี/ชั่วคราว/คำขอผิด)
- 🔒 คีย์**ไม่เคยออกจาก API แบบเต็ม** (mask เท่านั้น) · หน้านี้แก้คีย์ได้โดยไม่มี auth ⇒
  **ห้าม expose พอร์ต 8500 ออกนอกเครื่อง** (ยกระดับ auth เป็นบล็อกเกอร์ใน SECURITY/RISK)

**ผลจากการยิงจริง (ครั้งแรกของรีโปนี้ที่ทดสอบ provider อื่นนอกจาก Anthropic)**

- ✅ Anthropic · ✅ **OpenAI `gpt-5.2`** · ✅ **Gemini** — ยิงผ่านครบทั้ง 3 เจ้า
  (ปิด Risk #5 ที่ค้างมาตั้งแต่ Sprint 4: "OpenAI/Gemini ไม่เคยรันกับ service จริง")
- 🔧 **`GEMINI_MODEL` ค่าปริยายเดิม `gemini-3-pro` ไม่มีอยู่จริง** บน API v1beta → 404 ทุกครั้ง ·
  เปลี่ยนเป็น `gemini-3-flash-preview` (ยิงผ่านจริง) · รุ่น 2.5 ทั้งหมดถูกปิดสำหรับผู้ใช้ใหม่แล้ว
  และชั้น pro ของ Gemini ติด 429 quota — ใช้ได้แต่ชั้น flash บนบัญชีนี้
- **พิสูจน์ failover ด้วยของจริง:** ตั้ง Gemini (คีย์เสียจริง) เป็นตัวหลัก + Anthropic เป็นสำรอง →
  งานเดินจนจบด้วย Anthropic พร้อมป้ายบอก · ตั้งให้ไม่มีสำรอง → `failed` + `escalated` พร้อมเหตุ ·
  ตั้งชื่อรุ่นผิด → หยุดที่เจ้าแรก **ไม่ลามไปเจ้าที่สอง** (token = 0)
- pytest 133 → **170** (`test_llm_providers.py` 22 เคสครอบตารางแยก error ทุกแถว + `test_settings_api.py` 11 เคส)

## 2026-08-14 — ประตูหน้าบ้านของ API (`API_TOKEN`)

- ตั้ง `API_TOKEN` → **ทุก `/api/*` ต้องแนบ `X-DEP-PM-Token`** (เทียบด้วย `hmac.compare_digest`)
  · ไม่ตั้ง = ไม่ตรวจ (dev บน localhost — พฤติกรรมเดิมไม่เปลี่ยน)
- **ยกเว้นโดยตั้งใจ:** `/health` (probe) · `/docs` · `OPTIONS` (preflight) ·
  **`PATCH /api/deployments/:id`** ที่มี secret ของตัวเองอยู่แล้ว — บังคับ token ด้วยจะทำให้
  workflow ที่ติดตั้งไปแล้วทุกตัวพังทันที
- ⚠️ **token ต้องเป็น ASCII** — เจอตอนเขียนเทสต์: HTTP header ส่งภาษาไทยไม่ได้เลย
  (client โยน `UnicodeEncodeError` ก่อนยิงด้วยซ้ำ) ⇒ ตั้ง token ไทย = **ล็อกตัวเองออกจาก API**
  · เพิ่ม validator ให้ fail-fast ตอนสตาร์ตพร้อมบอกวิธีสร้าง token ที่ถูก
- **ปิด Risk #5.2** ที่หน้า `/settings` สร้างขึ้นเอง (แก้คีย์ AI ได้โดยไม่ต้องล็อกอิน) ·
  ตั้งค่าจริงแล้วบนเครื่องนี้ ยืนยันด้วยการยิง: ไม่แนบ → **401** · แนบถูก → **200**
- ⚠️ ข้อจำกัดที่ต้องรู้: ฝั่ง frontend อ่าน `NEXT_PUBLIC_API_TOKEN` ซึ่ง**อยู่ใน bundle ที่ browser
  โหลดได้** ⇒ กันคนนอกที่ยิงเข้าพอร์ต **ไม่ได้กันคนที่นั่งอยู่หน้าเครื่องนี้**
- pytest 195 → **202**

## 2026-08-14 — ตั้งเพดานเวลาของการเรียกโมเดล (`LLM_TIMEOUT_SECONDS`)

- **ค่าปริยายของ SDK คือ 600 วินาที** — เจอจริงตอนทดสอบวงจรเต็ม: `/breakdown` ด้วย prompt
  ที่ได้จาก PDF **ค้างครบ 10 นาที** · ถ้าไม่ตั้งเพดานเอง กลไก "ลองซ้ำ + ไล่เจ้าสำรอง"
  จะกลายเป็นครึ่งชั่วโมงต่อหนึ่ง task ⇒ ตัวสำรองที่ทำไว้ก็ช่วยอะไรไม่ได้เพราะกว่าจะถึงคิว
- ตั้งเพดาน **120 วิ/เจ้า** (ปรับได้ด้วย env) ให้ทั้ง 3 client · มีเทสต์ล็อกว่าทุกเจ้าได้รับค่านี้จริง
- โจทย์เดียวกันหลังตั้งเพดาน: PM แตกงานสำเร็จใน **97.5 วิ** (7 tasks)

## 2026-08-14 — DEP-PM เปิดโปรเจกต์ใหม่ "ของจริง" ได้แล้ว (ADR-05 S1-S3)

**S1 — `POST /api/projects/bootstrap`**
- สร้าง**โฟลเดอร์จริง** + เอกสารกำกับจาก kit + ตัวชี้ `_CANON` + `.gitignore` + `requirements.txt`
  + `git init` แล้ว**ลงบอร์ดพร้อม task sign-off** ในคราวเดียว · **ไม่เรียก AI · ไม่ auto-commit**
- ย้าย `scaffold.py` + แม่แบบเอกสารมาจาก `new-project-studio` (รีโปนั้นหยุดพัฒนา —
  **เจ้าของแม่แบบคือรีโปนี้แล้ว**) · `SCAFFOLD_ALLOWED_ROOT` เป็นรั้ว: target นอกรากนี้ = 400
- จบปัญหาที่ `pm_sync.py` ของ studio ชี้พอร์ต `8000` (ของ d_CEO) มาตั้งแต่ต้น — ตรรกะย้ายมาอยู่ฝั่งเรา

**S2 — หน้า `/projects/new` มีโหมด "เปิดโปรเจกต์ใหม่ของจริง"**
- กรอก target/purpose/stack/relation → เห็นรายการไฟล์ที่สร้างและขั้นตอนที่ทำ → เข้าบอร์ดได้เลย

**S3 — ไฟล์ดีไซน์กลายเป็นงานบนบอร์ด**
- `POST /:id/design-files` (multipart): เก็บไฟล์ที่ `_design_input/` แล้วดึงข้อความจาก
  `.md/.txt/.pdf/.docx` → คืน requirement ให้**คนตรวจก่อน**ส่งต่อ `/breakdown`
  · รูปภาพบอกตรง ๆ ว่าอ่านไม่ได้ **ไม่เดาเนื้อหาจากชื่อไฟล์**
- `POST /:id/deliverables`: เอาผลงานของ task ไป**เขียนเป็นไฟล์จริง** — เขียนได้เฉพาะใต้โฟลเดอร์
  โปรเจกต์ · **สำรองไฟล์เดิมก่อนทับเสมอ** · UTF-8 ไม่มี BOM · ไม่ commit ให้
- **ทำไมต้องมีขั้นนี้:** agent คืนข้อความเท่านั้น (ทุก LLM call ผ่าน providers ที่ไม่มี tool เขียนไฟล์)
  ⇒ การเปลี่ยนผลงานเป็นไฟล์เป็นขั้นที่คนสั่งเอง ไม่ใช่ agent ทำเองเงียบ ๆ
- คอลัมน์ใหม่ `projects.local_path` (migration `a1c8e5f92d47`) = รั้วของทุกการเขียนไฟล์
- dependency ใหม่: `pypdf` · `python-docx` · `python-multipart` (lazy import — ไม่มีก็ยังอัปโหลดได้)
- pytest 183 → **188**

## 2026-08-14 — ลบโปรเจกต์ได้ + ล้างงานทดสอบออกจากบอร์ด

- **`DELETE /api/projects/:id`** (ใหม่) — ลบโปรเจกต์พร้อม tasks/messages/deployments ·
  เขียน audit `project.deleted` · **409 ถ้าโปรเจกต์ผูกกับงานของ d_CEO** (ฝั่งโน้นยังอ้างอยู่)
  · ยังไม่ทำปุ่มบน UI โดยตั้งใจ — กันกดพลาด
- **ล้างบอร์ด 15 → 7 โปรเจกต์** (สำรอง DB ก่อน) · ลบงานทดสอบ 8 ตัวที่ไม่ผูกกับเลขา
  · เหลือ 4 ตัวที่ guard ปฏิเสธเพราะมี `ceo_task_id`

## 2026-08-14 — ข้อมูลขาดจุดเดียวต้องไม่ทำให้ทั้งเอกสารไม่ถูกผลิต

**แก้ 2 ที่ที่ทำให้เกิดอาการเดียวกันคนละมุม**

- **PM:** ห้ามผูก `depends_on` ของงานส่งมอบไว้กับงานที่รอข้อมูลจากคน — ให้ผลิตฉบับเต็ม
  โดยเว้นช่องว่างติดป้าย `[รอข้อมูล: <อะไร> จาก <ใคร>]` แล้วแยก "อัปเดตตัวเลขทีหลัง" เป็น task ต่างหาก
- **Reviewer:** `needs_human` มีไว้สำหรับงานที่**ติดทั้งชิ้น** — ขาดรายละเอียดบางจุดที่ติดป้ายไว้แล้ว
  ให้ **approve** · เกณฑ์: *ถ้าตัดส่วนที่ขาดออกแล้วผลงานยังมีประโยชน์กับคนอ่าน = approve*
- **วัดกับโจทย์เดิมเป๊ะ** (คู่มือปุ่มหยุดรอบรัน + สถิติที่ระบบไม่มี):

  | | ก่อนแก้ (`17db2a67`) | หลังแก้ (`662c3f43`) |
  |---|---|---|
  | คู่มือฉบับเต็ม | **ไม่ถูกผลิตเลย** (ค้าง planned) | ✅ **done** — 4,274 ตัวอักษร |
  | งานที่ต้องรอคน | ลาม 3 task | แยกอยู่ตัวเดียว (`escalated`) |
  | ช่องที่ขาด | — | `[รอข้อมูล: … จากทีม/ผู้ดูแลระบบ]` + "ต้องการข้อมูลจากคน:" ไม่มีการกุ |

- 🔎 **รอบวัดผลจับได้ว่า `needs_human` เริ่มถูกใช้เกินจำเป็นจริง** — คู่มือที่ reviewer เองบอกว่า
  "เขียนครบ ภาษาเข้าใจง่าย ไม่มีการกุข้อมูล" ถูกยกให้คนทั้งชิ้นเพราะไม่รู้ว่าปุ่มอยู่ตรงไหนบนจอ
  (ความเสี่ยงที่จดไว้ตั้งแต่ 3 ส.ค. — เกิดขึ้นจริงและปิดแล้ว)

## 2026-08-14 — เปิดตรวจ callback ของ CI จริง + เทสต์ deployments เลิกเด้ง

- **`DEPLOY_CALLBACK_SECRET` ตั้งค่าจริงแล้วทั้ง 2 ฝั่ง** (backend `.env` + GitHub secret
  `DEP_PM_CALLBACK_SECRET` ของ `ohho2518/d_DEP-PM_Platform`) — ยืนยันด้วยการยิงจริง:
  ไม่แนบ header → **401** · แนบถูก → ผ่านด่านไปถึง 404 ตามคาด · **ปิด Risk #1 เต็มตัว**
- ⚠️ **`docs/github-workflow-example.yml` เดิมไม่ได้ส่ง header** — ถ้าไม่แก้พร้อมกัน CI จะโดน
  401 เงียบ ๆ ทุกครั้ง · เพิ่ม `-H "X-DEP-PM-Secret: ${{ secrets.DEP_PM_CALLBACK_SECRET }}"` แล้ว
- **`test_list_deployments_newest_first` เลิก flaky** — วัดได้ว่า `utcnow()` **400 ครั้งติดกัน
  คืนค่าเดียวกันหมด** (นาฬิกา Windows ก้าวทีละ ~15.6 ms) แถวที่สร้างในคำขอเดียวกันจึงเวลาเท่ากันเป๊ะ
  · แก้ที่ query (tie-break ด้วย `id` → ลำดับคงที่ทุกครั้งที่เรียก UI ไม่สลับเอง)
  + เทสต์กำหนดเวลาต่างกันเอง · **ไม่ต้องทำ migration** เพราะปัญหาอยู่ที่ความละเอียดของนาฬิกา
  ไม่ใช่ที่ schema (ผ่าน 6 รอบติด)

## 2026-08-14 — นับโทเคนแยกตามผู้ให้บริการ (§5 ของใบสั่งงาน)

- **คอลัมน์ใหม่ `tasks.token_usage`** (migration `f3a9c1d7e2b8`) —
  `{"anthropic": {"model": …, "input": …, "output": …, "calls": …}}` สะสมทุก execute/review call
  · `tokens_input/output` เดิม**ไม่เปลี่ยนพฤติกรรม** (ยังเป็นยอดรวมของ task)
- **`GET /api/projects/:id/usage`** — รวมทั้งโปรเจกต์ แยกตามเจ้า เรียงจากตัวที่กินมากสุด
  · หน้าบอร์ดแสดงรายละเอียดต่อ task ใต้บรรทัด tokens เดิม
- ⚠️ **`untracked`** — งานที่ทำก่อนวันนี้แยกที่มาไม่ได้จริง จึงแสดงแยกไว้ **ไม่เดาย้อนหลัง**
  ว่าเป็นของ Anthropic (ของจริง: โปรเจกต์ Team Mode เมื่อเช้า 7,110/2,654 โทเคนตกอยู่ช่องนี้ทั้งก้อน)
- **ยังไม่แปลงเป็นเงิน** — ตารางราคาต้องมาจากเจ้าของ ไม่ใช่ตัวเลขที่ระบบเดาเอง ·
  สิ่งที่ได้ตอนนี้คือ "ถัง" ที่เพดานต่อเจ้าจะเกาะได้
- pytest 170 → **175**

## 2026-08-14 — เปิดใช้ลำดับสำรองจริง + Team Mode ครบ 3 เจ้า

- `LLM_FALLBACKS=openai,google` ⇒ chain ที่ใช้อยู่จริงคือ **`anthropic → openai → google`**
  (ก่อนหน้านี้กลไกพร้อมแต่ยังไม่ได้เปิดใช้ — เจ้าหลักล่มก็ยังหยุดเหมือนเดิม)
- **Team Mode รันกับคีย์จริงสำเร็จ**: `dev` → OpenAI `gpt-5.2` · `senior_architect` → Google
  `gemini-3-flash-preview` · reviewer → Anthropic — done ทั้งคู่ rev 0 และนับโทเคนได้จริง
  ⇒ ปิด Known Issue "OpenAI/Gemini ไม่เคยรันกับ service จริง"
- 📌 กติกาห้ามกุหลักฐาน/ต้องการข้อมูลจากคน **ข้ามค่ายได้เอง** — งานที่ Gemini ผลิตติดป้าย
  `[ตัวอย่างสมมติ]` และเขียนหัวข้อ "ต้องการข้อมูลจากคน:" โดยไม่ต้องแก้ prompt เพิ่ม
- 🔎 เห็นชัดว่า `tokens_input/output` ยังรวมทุกเจ้าไว้ที่ task เดียว ⇒ **§5 เพดานแยกต่อเจ้า
  ยังทำไม่ได้** จนกว่าจะแยกที่มาของโทเคน (มีแบบร่างจากรอบนี้แล้ว)

## 2026-08-14 — reviewer ได้เห็น `description` ของงานแล้ว

- `_review_prompt` เดิมส่งแค่ title + spec · หลังใส่กติกาห้ามกุหลักฐาน reviewer จึงปฏิเสธงาน
  ที่ถูกต้องด้วยเหตุผลว่า *"ไม่มี description ต้นฉบับให้เทียบ"* แล้ววนจนหมดโควตา → escalated
- เจอตอนทดสอบ failover กับงานจริง (2 รอบรีวิว, เสียโทเคนฟรี) — อาการเดียวกับบั๊ก upstream
  context ของ Phase 3a: **คนตรวจไม่ได้รับวัตถุดิบชุดเดียวกับคนทำ**

## 2026-08-03 — บันทึก UAT กับงานจริงจาก d_CEO (ย้ายมาจาก PROJECT_STATUS)

ตัวเลขที่วัดได้จากการรันกับงานจริง เก็บไว้ที่นี่เพื่อให้ `PROJECT_STATUS.md` เหลือแต่สถานะปัจจุบัน
(AGENTS.md §11) — **ข้อสรุปที่ยังใช้ตัดสินใจอยู่ทุกวันนี้ยังอยู่ในไฟล์นั้น**

**UAT รอบ 1 — วงจรเต็มกับ d_CEO ตัวจริง (2026-08-02)** · task `d89c03a8` → 6 tasks กราฟ 4 ชั้น
→ รัน **297 วินาที** → done 4 · escalated 1 · ค้าง 1 → รายงานกลับเข้า `qc_review` (output 1,040
ตัวอักษร · token 19,150 in / 18,512 out)
- 🐛 **บั๊กที่จับได้:** เกณฑ์ readiness นับ `planned` เป็น "ยังเดินอยู่" แต่ task ที่ dependency ติด
  escalated ค้าง `planned` ถาวร ⇒ เงื่อนไขไม่มีวันเป็นจริง — **เคสที่ต้องรีบบอกคนที่สุดกลับเงียบหาย**
  · แก้ให้ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง + เพิ่มหัวข้อ "งานที่ค้างเพราะรองานข้างบน"
- บทเรียน: unit test ครอบแค่ "จบครบ" กับ "ยังเดินอยู่" — เคส "ตันถาวร" คิดไม่ถึง **การรันกับงานจริงคือสิ่งเดียวที่จับได้**

**UAT รอบ 2 (Phase 2) — กลไกผ่าน แต่ QC ปฏิเสธผลงาน (2026-08-03)** · task `80dd3ff9` → project `7ffa2d4f`

| จุดวัด | ผล |
|---|---|
| สร้าง task ไทยผ่าน HTTP | ตรงตัวต่อตัว 356 ตัวอักษร ไม่มี `?` |
| `POST /run` | **202 ใน 10.6 ms** (งานรูปเดียวกันเมื่อวาน block 297 วิ) · ยิงซ้อน = **409** |
| รอบรันเบื้องหลัง | **507 วินาที** · `succeeded` · done 5 · escalated 1 · progress เดินจริงทุกช่วง poll |
| รายงานกลับอัตโนมัติ | `reported: true` → `qc_review` · token 29,514 in / 33,850 out |

- **QC ตอบ `rejected`** ด้วยข้อบกพร่องจริง 2 ข้อ: (1) รายงานส่งแต่สรุปสถานะ **ไม่มีตัวชิ้นงานให้ตรวจ**
  (2) orchestrator ไม่ส่งผลงานของ dependency ให้ task ที่ depend อยู่ ⇒ agent ผลิตได้แค่โครงที่มี
  `[[placeholder]]` — **นี่คือ root cause ของ "งานรวมเล่มถูกปฏิเสธ" ไม่ใช่เพราะ reviewer เข้มเกินไป**
  ⇒ แก้ทั้งคู่ใน Phase 3a วันเดียวกัน
- บทเรียน: unit test + smoke test บอกได้แค่ "กลไกเดิน" · **คุณภาพงานที่ส่งออกต้องมีคนนอกตรวจถึงจะเห็น**

**UAT รอบ 3 หลัง Phase 3a (2026-08-03)** · โจทย์เดียวกับรอบ 2 ทุกตัวอักษร → project `4d8004ff`

| | รอบ 2 | รอบ 3 |
|---|---|---|
| tasks / ผลรัน | 6 · done 5 · escalated 1 | **8 · done 8 · escalated 0** |
| งาน "รวมเนื้อหา" (depend 3) | ผลิต `[[placeholder]]` → ปฏิเสธ 2 รอบ | **ผ่านรอบแรก 0 revision** |
| รายงานถึงเลขา | 2,652 ตัวอักษร (สรุปสถานะ) | **31,820 ตัวอักษร (มีตัวชิ้นงาน)** |
| **QC verdict** | ❌ `rejected` | ✅ **`PASS` → task เป็น `done`** |

**สถิติ escalation ที่ใช้ตัดสินว่า "reviewer เข้มเกินไป" เป็นข้อสรุปที่ผิด** — 23 งานที่จบแล้ว ·
escalated 2 = 8.7% · **ทั้ง 2 ครั้งสาเหตุเดียวกันคือไม่ได้รับผลงานของงานก่อนหน้า** ·
หลัง Phase 3a: escalated 0 · revision เฉลี่ย 0.67 → 0.12 (สรุปเต็มใน `docs/runbook.md` §7)

## 2026-08-03 — งานที่ "ติดเพราะต้องรอคน" ส่งต่อให้คนทันที (verdict `needs_human`)

- **reviewer มีคำตัดสินที่ 3: `needs_human`** — งานที่ทำต่อไม่ได้เพราะ**ขาดข้อมูล/สิทธิ์ที่ agent
  หามาเองไม่ได้** → `escalated` **ตั้งแต่รีวิวแรก** โดย**ไม่นับเป็น revision** (ไม่ใช่ความผิดของงาน)
  · เหตุผลในรายงานถึงเลขาขึ้นต้นว่า **"ต้องการข้อมูล/การตัดสินใจจากคน — …"** แยกจาก
  "review ไม่ผ่าน 2 ครั้ง" ชัดเจน · Message Log เก็บ flag ไว้ให้ย้อนดูได้
- **reviewer ถูกห้าม 2 อย่าง:** (1) approve งานแบบนี้ว่า "เสร็จ" — รายงานจะนับเป็นงานที่ทำเสร็จ
  ทั้งที่ไม่มีชิ้นงาน (2) สั่ง revision ที่ agent ทำตามไม่ได้ (ติดต่อคน · escalate จริง · เข้าระบบภายนอก)
- **กติกาห้ามกุขยายไปถึง "การกระทำ":** ห้ามเขียนว่า "ได้ส่งเรื่อง/ติดต่อผู้เกี่ยวข้องแล้ว"
  ทั้งที่ทำได้แค่พิมพ์ข้อความ
- **ที่มา — UAT รอบ 3 กับโจทย์ที่ล่อให้กุโดยตรง:** กติกาห้ามกุ**ได้ผล** (ไม่มีการกุเลย ·
  QC ของ d_CEO ยืนยันว่า "เป็นพฤติกรรมที่ถูก") แต่เปิดจุดบกพร่องแทน — reviewer สั่งให้ agent
  "ยืนยันว่า escalate ไปแล้วจริง" ซึ่งทำไม่ได้ → agent เขียนว่าทำแล้ว → รอบถัดมา reviewer
  จับได้เอง ⇒ **เสีย 2 รอบแล้วตันอยู่ดี** และงานสถานการณ์เดียวกันอีกตัวถูก approve เป็น `done`
  ทั้งที่เนื้อในบอกว่าทำไม่ได้ (QC จับได้ทั้งคู่)
- ตรวจกับโมเดลจริงแล้ว 1 งาน: `needs_human: true` ตั้งแต่รอบแรก → `escalated` ที่ revision 0
- pytest 126 → **133**

## 2026-08-03 — ห้าม agent กุหลักฐาน (กติกาใน persona + เกณฑ์ให้ reviewer จับ)

- **`NO_FABRICATION_RULE` ต่อท้าย PM/DEV/ARCHITECT** — เขียนชื่อคน · คำพูดในเครื่องหมายคำพูด ·
  วันเวลา · ไฟล์/ลิงก์/ภาพหน้าจอ · ตัวเลขผลวัด · endpoint ของระบบจริง **ได้เฉพาะที่มีอยู่จริง
  ใน task/spec/ผลงานก่อนหน้า** · ไม่มีข้อมูลให้เขียน "ต้องการข้อมูลจากคน:" แทน ·
  ยกตัวอย่างได้ถ้าติดป้าย `[ตัวอย่างสมมติ]`
- **reviewer จับการกุข้อมูลเป็นอันดับแรก** — เจอแล้ว reject ทันที พร้อมระบุว่า
  **สำคัญกว่าความครบของเนื้อหา** (งานที่ครบแต่มีข้อมูลเท็จแย่กว่างานที่ขาดแล้วบอกตรง ๆ)
- **PM ถูกสั่งเพิ่ม:** ห้ามเขียน spec ที่สั่งให้ไป "สัมภาษณ์/เก็บข้อมูลจริง" ถ้าไม่มีช่องทางให้ทำ
  — เป็นต้นทางที่ทำให้ agent แต่งหลักฐาน (เคสจริง)
- **ที่มา:** QC ของ d_CEO จับได้ 2 เคสในวันเดียว — อ้างชื่อคน "คุณธนกฤต ว." พร้อม quote/timestamp/
  screenshot ที่ไม่มีอยู่จริง · และเอกสารที่สมมติ endpoint ของระบบจริง (เคสหลัง disclose ว่าเป็น
  ตัวอย่าง → QC ยอมรับ ⇒ ทางออกคือ "แต่งได้ถ้าติดป้าย")
- `tests/test_personas.py` ล็อกกติกาไว้เป็นสัญญา · pytest 114 → **126**

## 2026-08-03 — ตีกลับงานที่ escalate ให้ agent ทำใหม่ได้ + ปุ่มสั่ง QC ตรวจซ้ำ (ใบสั่งงาน Ticket #3)

- **`escalated → planned` ("ตีกลับเข้าคิว")** — เดิม escalated ไปได้แค่ `in_progress` (คนลงมือเอง)
  แต่ orchestrator หยิบเฉพาะ `planned` ⇒ **งานที่ escalate ไปแล้วให้ agent ลองใหม่ไม่ได้เลย**
  · ใช้เมื่อแก้ "เหตุ" ที่ทำให้ตันแล้ว · `revision_count` **ไม่รีเซ็ต** โดยตั้งใจ — ตีกลับแล้ว
  ยังไม่ผ่านจะ escalate ทันทีรอบเดียว ไม่วนจ่ายค่า LLM
- **`POST /api/ceo/qc/:project_id` + `ceo_client.qc_task()`** — ปุ่มฉุกเฉินสั่ง QC ของเลขาตรวจซ้ำ
  · **ปกติไม่ต้องใช้**: contract v6 ของ d_CEO ส่งเข้า QC ต่อเองเมื่อ PATCH เลื่อนสถานะ**เข้า**
  `qc_review` พร้อม `output` — ซึ่งเราส่งใน **PATCH เดียว** อยู่แล้ว (มีเทสต์ล็อกไว้)
  · ⚠️ 1 รอบ QC มีราคาราวครึ่งของค่างานหนึ่งชิ้น
- **ตารางพอร์ตเลิกก๊อบ 3 ชุด** — `AGENTS.md`/`runbook`/`PROJECT_STATUS` ชี้ไป
  `_CANON\SERVICE_PORTS.md` (ทะเบียนกลางที่ตั้งขึ้นหลังเหตุ 8400 ชนเมื่อ 2 ส.ค.)
- pytest 107 → **114**

## 2026-08-03 — ปุ่มหยุดรอบรัน · ปิด DoD PostgreSQL · ทบทวน escalation

**⏹ หยุดรอบรันได้แล้ว**
- ปุ่ม **"หยุดรอบรัน"** บนหน้าบอร์ด + `POST /api/projects/:id/run/cancel`
- **หยุดหลัง task ที่กำลังทำอยู่จบ ไม่ตัดกลางคัน** — ตัดกลางจะเหลือ task ค้างสถานะให้แก้มือ
  และจ่ายค่า token ไปแล้วโดยไม่ได้ผลงาน · รอบที่หยุดได้สถานะ `cancelled`
  **ไม่รายงานกลับเลขา** (รอบยังไม่จบ) · งานที่เสร็จแล้วอยู่ครบ กด Run ใหม่ทำต่อได้

**🐘 test suite รันบน PostgreSQL ได้จริงแล้ว (ปิด DoD ของ ADR-01)**
- `TEST_DATABASE_URL=postgresql+psycopg://…` → **pytest 107/107 ผ่านบน PostgreSQL 17.10**
  (ชุดเดียวกับ SQLite) · ไม่ตั้ง = SQLite ในหน่วยความจำเหมือนเดิม
- 🐛 **DoD จับบั๊กจริงได้ทันที:** migration `b2f1c0d3e4a5` (seed agent) ประกาศ `id` เป็น
  `sa.String` แต่คอลัมน์จริงบน PG เป็น native `uuid` → **`alembic upgrade head` ตายทั้งชุด**
  แปลว่าคำสัญญา "แค่เปลี่ยน `DATABASE_URL`" ใช้ไม่ได้จริงมาตลอด — แก้เป็น `GUID` แล้ว
  (ผลบน SQLite เหมือนเดิมทุกประการ · ยืนยันด้วย suite ทั้งชุดบนทั้งสอง engine)

**📊 ทบทวน escalation จากข้อมูลจริง** (`runbook` §7)
- งานที่จบแล้วทั้งหมด 23 รายการ · escalated 2 = **8.7%** (เป้า < 10%)
- **escalation ทั้ง 2 ครั้งมีสาเหตุเดียวกัน: agent ไม่ได้รับผลงานของงานก่อนหน้า** —
  ข้อสรุปเดิมที่ว่า "reviewer เข้มเกินไป" **ผิด** reviewer ถูกทั้งสองครั้ง
- หลัง Phase 3a: escalated 0 และ revision เฉลี่ยลดจาก 0.67 → 0.12 ในโจทย์เดียวกัน

**📨 `docs/REQUEST_TO_CEO.md`** — จดหมายพร้อมส่งถึง session ของ d_CEO (ยืนยัน contract,
แก้เอกสารที่ยังเขียนว่าให้ยุบรวม DEP-PM, กติกามอบงาน) **ไม่แก้ข้ามรีโป**

## 2026-08-03 — CI callback มี authentication แล้ว (ปิด Risk #1)

- **`PATCH /api/deployments/:id` ต้องแนบ header `X-DEP-PM-Secret`** ให้ตรงกับ
  `DEPLOY_CALLBACK_SECRET` — endpoint เดียวในระบบที่ผู้เรียกอยู่นอกเครื่อง จึงเป็นจุดเดียวที่มี auth
  · ไม่ตรง/ไม่แนบ = **401** และไม่แตะสถานะจริง
- **ไม่ตั้งค่า = ไม่ตรวจ** (ค่าปริยาย) — dev บน localhost และ workflow ที่ติดตั้งไปแล้วไม่พัง
  🔴 แต่ **ต้องตั้งก่อนเปิดพอร์ตออกนอกเครื่อง** ไม่งั้นใครก็เลื่อน task เป็น `deployed` ปลอมได้
- เทียบด้วย `hmac.compare_digest` แบบ **bytes** — เวอร์ชัน str รับเฉพาะ ASCII ทำให้ secret
  ที่มีอักษรไทยกลายเป็น 500 แทน 401 (เจอตอนเขียนเทสต์)
- template workflow + runbook §3 เพิ่มขั้นตอนตั้ง `DEP_PM_CALLBACK_SECRET` ในรีโปเป้าหมาย
- pytest 97 → **103**

## 2026-08-03 — Phase 3a: agent ได้เห็น "ผลงานจริง" ของงานก่อนหน้า + รายงานแนบตัวชิ้นงาน

สองข้อนี้มาจากคำตัดสิน `rejected` ของ QC ฝั่ง d_CEO ในรอบ UAT วันเดียวกัน

- **งานที่ทำต่อจากของเดิมทำได้จริงแล้ว** — orchestrator ส่ง **ผลงานล่าสุดของ task ที่อยู่เหนือ
  ทั้งกราฟ** (ไม่ใช่แค่ dependency ตรง) ไปกับ prompt · เดิม agent เห็นแค่ title/spec ของตัวเอง
  งาน "รวมเนื้อหาจาก T2/T3/T4" จึงผลิตได้แค่โครงที่มี `[[placeholder]]` แล้วถูก reviewer
  ปฏิเสธจน escalated — **นี่คือสาเหตุจริงของปัญหา "งานรวมเล่มไม่เคยผ่าน"** ไม่ใช่ reviewer เข้มเกิน
  · เพดาน 6,000 ตัวอักษร/ชิ้น · 24,000 รวม — เกินแล้วตัดตัวเก่าสุดก่อน **พร้อมบอกว่าตัด**
- **รายงานถึงเลขาแนบตัวชิ้นงานจริงของทุก task ที่เสร็จ** (หัวข้อใหม่ "## ผลงาน (ตัวชิ้นงานจริง)")
  · QC ปฏิเสธรอบก่อนด้วยเหตุผล *"ไม่มี artifact ให้ตรวจ"* — ผลงานอยู่ใน `agent_messages`
  มาตลอด แค่ไม่เคยถูกหยิบมาใส่ · เพดาน 8,000 ตัวอักษร/task · 40,000 รวม
- **`PersonaExecutor.execute` รับ `context` เพิ่ม** (breaking สำหรับผู้ที่ implement เอง) —
  provider ทุกตัวต้องส่งต่อให้โมเดล ไม่งั้นอาการเดิมกลับมา
- ตัวอ่านผลงานอยู่ที่ `bus.latest_work_by_task` ที่เดียว (orchestrator + ceo_sync ใช้ร่วมกัน)
- pytest 90 → **97** · ruff clean · `npm run build` ผ่าน

## 2026-08-03 — Phase 2: Run Agents เป็นงานเบื้องหลัง (ไม่ block ผู้เรียกอีกต่อไป)

- **⚠️ Breaking (API):** `POST /api/projects/:id/run` ตอบ **202 + `run_id`** ทันที
  (เดิม 200 พร้อมผลครบเมื่องานจบ) — ผลจริงอ่านที่ endpoint ใหม่ `GET /api/projects/:id/run`
  · `frontend/src/lib/types.ts` (`RunSummary`, `RunState`) แก้ในคอมมิตเดียวกันตามกติกา
- **เหตุ:** UAT 2026-08-02 วัดได้ **6 tasks = 297 วินาที** ใน request เดียว ขณะที่ d_Jarvis
  ตั้ง timeout ไว้ 5 นาที — ใช้งานประจำไม่ได้ถ้าไม่แก้ (Risk #3) · ตอนนี้ request ตอบใน ~10 ms
- **1 โปรเจกต์ = 1 รอบรันพร้อมกัน** — ยิงซ้อนโปรเจกต์เดิมได้ **409** พร้อมบอก `run_id`
  ที่ค้างอยู่ (คนละโปรเจกต์รันพร้อมกันได้ตามปกติ) — ปิดช่อง "ยิงซ้อนแล้วสถานะเพี้ยน"
- **UI:** กด Run แล้วปุ่มตอบทันที · แถบความคืบหน้าใช้ตัวเลขจริงจาก backend (`processed/total`)
  · **ปิดแท็บ/รีเฟรชหน้าได้ งานไม่หยุด** — เปิดหน้าบอร์ดใหม่แล้วเห็นความคืบหน้าต่อ
  · เจอ 409 = สลับไปแสดงรอบที่ค้างอยู่แทนการขึ้น error ดิบ
- **รอบรันล้ม** (exception หลุด) → `status: "failed"` + `error` และ **ปลด lock เสมอ**
  (ผลงานที่ commit แล้วก่อนพังยังอยู่ — engine commit ต่อ task)
- **รายงานกลับ d_CEO อัตโนมัติ** ย้ายไปอยู่ท้ายรอบรันเบื้องหลัง — ผลอยู่ใน `ceo_report`
  ของ `GET /run` (ไม่ใช่ response ของ `POST /run` ที่ตอบไปก่อนแล้ว) · ปลายทางล่ม
  **ไม่ทำให้รอบรันเป็น failed**
- **ข้อจำกัดที่ยังอยู่:** ทะเบียนรอบรันอยู่ในหน่วยความจำโปรเซสเดียว (restart backend =
  ประวัติรอบรันหาย ผลงานใน DB ไม่หาย) · ยังไม่มีปุ่มยกเลิกรอบรัน
- ไฟล์ใหม่ `backend/app/services/runs.py` + `backend/tests/test_runs.py` ·
  pytest 82 → **90 tests** · ruff clean · `npm run build` ผ่าน
  · smoke test กับ uvicorn จริง (DB ชั่วคราว): 20 tasks รันเบื้องหลังจบครบ, 409 ทำงาน, progress สด

## 2026-08-02 — Fix: ย้ายพอร์ตอีกครั้ง 8400 → **8500** (8400 เป็นของ d_Jarvis)

- **⚠️ Breaking (dev) ทับของเมื่อเช้า:** พอร์ต backend ที่ถูกต้องคือ **8500**
  `uvicorn app.main:app --reload --port 8500` · ต้องแก้ `NEXT_PUBLIC_API_URL` ตาม
- **เหตุ:** ตอนเลือก 8400 อ่าน `.env.example` ของ Jarvis เฉพาะบรรทัด base URL ของ client
  (8000/8100/8200/8300) แล้ว**พลาดบรรทัด `WEB_PORT=8400`** ซึ่งเป็น web channel ของ Jarvis
  ที่รันค้างผ่าน Task Scheduler · Windows ยอมให้ bind `127.0.0.1:8400` ซ้อน `0.0.0.0:8400`
  ได้โดยไม่ error → ระหว่างทดสอบ **DEP-PM บังหน้าเว็บ Jarvis บน localhost เงียบ ๆ**
  (ไม่กระทบข้อมูล และหยุด process ของเราแล้ว Jarvis กลับมาปกติทันที)
- **ทะเบียนพอร์ตฉบับถูกต้อง:** `8000` d_CEO API · `8100` d_OCR · `8200` d_STT ·
  `8300` d_InnoHub · `8400` **d_Jarvis web** · **`8500` DEP-PM**
- **กติกาใหม่ใน AGENTS.md + runbook:** ตรวจพอร์ตด้วย
  `Get-NetTCPConnection -LocalPort <port> -State Listen` ก่อนจองเสมอ **อย่าเชื่อเอกสารอย่างเดียว**

## 2026-08-02 — Fix: งานที่ escalate แล้วเคยเงียบหาย ไม่ถูกรายงานกลับเลขา

- **บั๊กที่พบจาก UAT จริง:** เกณฑ์ "รายงานเมื่องานจบครบ" นับ task สถานะ `planned` เป็น
  "ยังเดินอยู่" — แต่ task ที่ dependency ติด `escalated` จะค้าง `planned` **ถาวร**
  (พฤติกรรมถูกต้องของ orchestrator: หยุดเดินเอง ไม่ deadlock) ผลคือเงื่อนไขไม่มีวันเป็นจริง
  → **เคสที่ต้องรีบบอกคนที่สุด (มีงาน escalate) กลับเป็นเคสเดียวที่ไม่เคยรายงาน** และ
  task ฝั่ง d_CEO ค้าง `in_progress` ตลอดกาล
- **แก้:** เกณฑ์ใหม่ตรงกับเงื่อนไขที่ orchestrator หยุดเดินเอง — พร้อมรายงานเมื่อ
  ไม่มี task ที่ agent ถืออยู่ **และ** ไม่มี `planned` ที่ dependency จบครบแล้ว (รันต่อได้)
  **และ** ไม่มี `backlog` ค้าง (ยังไม่ยืนยัน scope) · แต่ละกรณีบอกเหตุผลต่างกันชัดเจน
- **รายงานบอกความจริงครบขึ้น:** เพิ่มหัวข้อ "งานที่ค้างเพราะรองานข้างบน" (ระบุว่าติดเพราะ
  task ไหน) + แถบเตือน "⚠️ งานรอบนี้ยังไม่จบสมบูรณ์ ต้องให้คนเข้ามาตัดสิน" ท้ายหัวเรื่อง
- pytest 79 → **82 tests** (เพิ่มเคส escalated-บล็อก-dependent, runnable-ยังไม่รายงาน, backlog)

## 2026-08-02 — Phase 1: รับงานจากเลขา (d_CEO) ในฐานะ Team Lead R&D

- **📥 กล่อง "งานจากเลขา" บนหน้า Portfolio** — เห็นงานที่ d_CEO มอบให้ทีม R&D พร้อมปุ่ม
  "ดึงงานทั้งหมด" / "รับงานนี้" · กล่องนี้ซ่อนเองถ้ายังไม่ตั้ง `CEO_API_BASE`
  · d_CEO ปิดอยู่ = แสดง "🧠 สมองออฟไลน์" ระบบส่วนอื่นใช้ได้ปกติ
- **ดึงงาน 1 ครั้ง = 1 โปรเจกต์** — สร้างโปรเจกต์ผูก `ceo_task_id` (unique) → PM Agent แตกงาน
  ให้เลย → แจ้ง d_CEO เป็น `in_progress` · ดึงงานเดิมซ้ำไม่ได้ · **ผู้ใช้ยืนยัน scope + กด Run เอง**
- **รายงานผลกลับอัตโนมัติ** เมื่องานในโปรเจกต์จบครบ (หลัง Run Agents) — ส่งสรุป markdown
  (งานที่เสร็จ / งานที่ต้อง escalate พร้อมเหตุผล / token ที่ใช้) เข้า **QC gate** ของ d_CEO
  · ปุ่ม "📤 ส่งผลกลับเลขา" บนหน้าบอร์ดไว้ยิงซ้ำเมื่อรอบอัตโนมัติล้มเหลว
- 🔴 **ระบบปิดงานฝั่ง d_CEO เองไม่ได้** — ส่งได้แค่ `in_progress`/`qc_review` เท่านั้น
  (`done`/`awaiting_approval`/`rejected` = ValueError ก่อนยิง HTTP) ตามมติ Vinit 2026-08-02
  ว่าทุกงานต้องผ่าน QC gate — QC ของ d_CEO เป็นคนเคาะ
- **Endpoints ใหม่:** `GET /api/projects/:id` · `GET /api/ceo/status` · `GET /api/ceo/inbox` ·
  `POST /api/ceo/pull` · `POST /api/ceo/report/:project_id` — `/api/projects/:id/run` เพิ่ม
  field `ceo_report` · `/health` เพิ่ม `ceo_enabled`
- **Schema:** `projects.ceo_task_id` (VARCHAR(36), nullable, **unique**) — migration `e5a91c73b204`
- **เอกสารใหม่:** `docs/INTEGRATION_CEO.md` (contract ฝั่ง consumer + สิ่งที่ต้องขอจาก d_CEO)
  · runbook §4.1 วิธีใช้งานประจำวัน
- pytest 60 → **79 tests** · ตรวจกับ d_CEO ตัวจริงแล้ว: resolve ทีม R&D ได้, `online: true`

## 2026-08-02 — Phase 0: ย้ายพอร์ตเป็น 8400 + AGENTS.md เป็นต้นฉบับ + จัดเอกสาร

- **⚠️ Breaking (dev):** backend ย้ายจากพอร์ต **8000 → 8400** — `uvicorn app.main:app --reload --port 8400`
  เหตุผล: `:8000` เป็นของ **d_CEO / Solo_CEO API** ที่รันค้างตลอดผ่าน Task Scheduler และ d_Jarvis
  พึ่งพาอยู่ (ห้ามหยุด) — เดิมเอกสารบอกให้รันที่ 8000 ซึ่ง**รันไม่ขึ้นจริง** · ต้อง `cp .env.local.example
  .env.local` ใหม่ หรือแก้ `NEXT_PUBLIC_API_URL` เป็น `http://127.0.0.1:8400`
  · ตารางพอร์ตของ ecosystem จดไว้ใน `AGENTS.md` §3.1 และ `docs/runbook.md` §1
- **`AGENTS.md` = single source of truth** ของกติกา AI agent (ตรงกับ convention ของ d_Jarvis/d_CEO/d_InnoHub)
  — ย้ายเนื้อหาจริงจาก `CLAUDE.md` เข้ามาครบ + เพิ่ม **§3.1 ตำแหน่งใน ecosystem** (สายบังคับบัญชา
  Vinit→Jarvis→d_CEO→DEP-PM = Team Lead R&D) · `CLAUDE.md`/`GEMINI.md` เหลือเป็น pointer
  · แก้ลิงก์ `WORKING_RULES.md` ที่เคยชี้ไฟล์ที่ไม่มีอยู่จริง → ชี้ `_CANON`
- **`README.md`** เขียนใหม่เป็นของ DEP-PM (เดิมเป็น README ของ Project Starter Kit ที่หลงเข้ามา)
- **`docs/PROJECT_OVERVIEW.md` + `docs/RISK_REGISTER.md`** เติมเนื้อหาจริง (เดิมเป็นเทมเพลตเปล่า)
  — 14 active risks + 6 closed + security/performance checklist ตามสถานะจริง
- commit งานค้างของ 2026-07-07 ที่ตกค้างใน working tree มา ~1 เดือน (`9cd76d6`)
- `.gitignore`: เพิ่ม `BackUp/` (สำเนาก่อนแก้ตาม WORKING_RULES — มีข้อมูลจริง ห้ามขึ้น remote)
- ตรวจแล้ว: pytest 60/60 · ruff clean · `npm run build` ผ่าน · DEP-PM `:8400` กับ d_CEO `:8000`
  รันคู่กันได้จริง (health ตอบทั้งคู่)

## 2026-07-07 — เคลียร์ technical debt #3/#5/#7 + หน้า Deployments + ruff

- **Reviewer fail-safe (debt #3):** review ที่ parse ไม่ได้ → retry 1 ครั้ง → ยังไม่ได้ =
  **reject** (เดิม auto-approve — งานไม่ถูกตรวจจริงอาจหลุดเป็น done) → เข้า revision loop
  ปกติ ครบ MAX_REVISIONS แล้ว escalate ให้คน; logic รวมที่ `runtime._review_with_retry`
  ใช้ทั้ง Solo และ Team Mode
- **Token-usage tracking (debt #7):** คอลัมน์ใหม่ `tasks.tokens_input/tokens_output`
  (migration `c7d4e2a9b1f3`) สะสมจากทุก execute/review call ทุก provider
  (Anthropic/OpenAI/Gemini คืน `LLMReply` พร้อม usage) — โชว์ใน task detail panel
- **depends_on referential integrity (debt #5):** สร้าง task ที่อ้าง id นอกโปรเจกต์/ไม่มีจริง
  → 400 | endpoint ใหม่ `DELETE /api/tasks/:id` — มีตัวอ้างค้าง → 409; ลบสำเร็จเก็บ audit
  + ลบ messages (CASCADE) + deployments.task_id → NULL (ทำที่ API layer เพราะ SQLite
  dev ไม่ enforce FK)
- **หน้า Deployments ใหม่** (`/deployments` + ลิงก์ nav): ตารางประวัติ deploy ทุกโปรเจกต์
  ใหม่ล่าสุดก่อน พร้อมสถานะสี/environment/trigger/commit — ใช้ endpoint ใหม่
  `GET /api/deployments` (filter `project_id` ได้, เติม project_name/task_title ให้)
- **ruff:** config `backend/ruff.toml` (E,F,I,B,UP; ignore E501,B008) + แก้ของเดิมทั้งหมด
  (ส่วนใหญ่ import order) — suite สะอาด
- pytest 48 → **60 tests** (review fail-safe, token accumulation, depends_on guards,
  deployments list)

## 2026-07-06 — UI: ai-dev-team theme + Agent Office + Run progress

- **Restyle ทั้งระบบตาม `ai-dev-team-complete.html`**: โทนสว่าง #f4f5fb + dot grid,
  การ์ดขาว r14, สีทีม Claude ม่วง / Codex เขียว / Gemini ฟ้า (utilities ใน globals.css)
- **🏢 Agent Office** (หน้าบอร์ด): ตัวการ์ตูน PM/Dev/SR/Reviewer เดินไปมาเมื่อ role นั้น
  มีงาน active (พร้อมป้ายชื่องาน) / ยืนจิบกาแฟเมื่อว่าง — สถานะจริงจาก task ที่ poll
- **Run progress bar**: ตัวนับงานเสร็จ/ทั้งหมด, สถานะเฟสงานปัจจุบัน (มอบหมาย/เขียน/ตรวจ
  + รอบแก้), เวลาที่ใช้ (เดินสดทุกวิ), ETA จากค่าเฉลี่ยต่องานที่จบ; poll ถี่ขึ้นเป็น 2 วิระหว่างรัน
- Fix ระหว่างใช้งานจริง: เผลอลบ dep_pm.db ระหว่าง cleanup ทำให้โปรเจกต์ผู้ใช้หาย —
  กู้ด้วยโปรเจกต์เดโมใหม่ + บันทึกกติกาถาวร "ห้ามลบ dep_pm.db" (memory + runbook)


## 2026-07-06 — UAT กับของจริง (Anthropic API + GitHub) + bugfixes

- **UAT ผ่าน 3 รายการ:** (1) PM Agent จริง — requirement ไทย → 16 tasks มี priority/points/deps
  (2) Solo Mode จริง — escalation ครบวงจร (reviewer ปฏิเสธ 2 → escalated → human takeover →
  done) + happy path งานออกแบบ schema → done รอบเดียว (3) Deploy dispatch จริง —
  `repository_dispatch` → workflow รันบน GitHub Actions, Build & Deploy step ผ่าน
- **Fix:** `MAX_TOKENS_PER_TASK` default 4096 → 16000 — adaptive thinking ของ claude-sonnet-5
  กินโควตาจนได้ text ว่างในรอบ revision (พบจริงใน UAT); `_call` คืน marker ชัดเจนเมื่อ text ว่าง
- **Fix:** test suite ไม่ hermetic เมื่อ `.env` มี key จริง — Windows ลบ env var ที่ตั้งเป็นค่าว่าง
  ทำให้ override ไม่ทำงาน → conftest เพิ่ม autouse fixture monkeypatch Settings (48/48, 0.96s)
- Push repo ขึ้น GitHub: `ohho2518/d_DEP-PM_Platform` (branch main) + workflow receiver
- บทเรียน UAT บันทึกใน `docs/runbook.md` §7

## 2026-07-06 — Sprint 4: Deploy Pipeline + Team Mode + PostgreSQL-ready

- **Deploy pipeline (Blueprint §12):** `services/deploy.py` ยิง GitHub `repository_dispatch`
  (event `dep-pm-deploy`) เมื่อตั้ง `GITHUB_TOKEN`+`GITHUB_REPO`; ไม่ตั้ง = stub mode
  (record `queued`, ไม่ error) | endpoints: `POST /api/deployments` (manual — production
  มาทางนี้เท่านั้น = Manual Approval Gate), `GET /:id`, `PATCH /:id` (CI callback —
  success เลื่อน task done→deployed อัตโนมัติ, terminal status ห้ามแก้ → 409)
- **Auto-deploy:** task done ระหว่าง orchestrator run + `AUTO_DEPLOY_ENABLED=true` →
  staging deployment อัตโนมัติ (auto path hardcode staging)
- **Team Mode (Blueprint §8-9):** `AGENT_MODE=team` → `TeamExecutor` map role→provider
  (Dev=OpenAI/Codex, SR=Gemini, PM+Reviewer=Claude) + fallback chain ต่อ role
  (provider→anthropic→deterministic); orchestrator ไม่แก้แม้แต่บรรทัดเดียว (DoD)
- **PostgreSQL-ready:** `psycopg[binary]` ใน requirements + ขั้นตอนย้ายใน `docs/runbook.md`
  (การรัน test จริงบน PG รอ infrastructure — ไม่มี Docker/PG บนเครื่องนี้)
- **ตัดสินใจ: ข้าม Redis** — ADR-03 ระบุ "ถ้าทัน"; single-user ยังไม่มีเหตุ cross-process
- **Handover:** `docs/runbook.md` (รัน/เปิด features/troubleshooting/UAT checklist) +
  `docs/github-workflow-example.yml` (template สำหรับ repo เป้าหมาย)
- pytest 48 เคสผ่าน (เพิ่ม 14: deployments + team mode)

## 2026-07-06 — Engineering Documentation Set (ตาม MASTER PROMPT)

- สร้างชุดเอกสารวิศวกรรมใน `docs/` ครอบคลุม 25 sections ของ
  "MASTER PROMPT: Complete Software Engineering Documentation Generator":
  - `ARCHITECTURE.md` (§1-4) — overview/non-goals/constraints, HLA + Mermaid 3 diagrams,
    tech stack พร้อม WHY/tradeoffs/ทางเลือกที่ไม่เลือก, folder structure + dependency direction
  - `SYSTEM_DOCUMENTATION.md` (§5-9, 13-14, 16-22, 24) — วิเคราะห์ทุกโมดูล, algorithms,
    business logic + state diagram, frontend/backend, performance/testing/deployment/maintenance,
    technical debt จัดอันดับ, glossary
  - `API.md` (§12) — 12 endpoints พร้อม request/response ตัวอย่าง + error codes
  - `DATABASE.md` (§10-11) — ER diagram, ทุกตาราง/index/query pattern, migration history + กติกา
  - `SECURITY.md` (§15) — threat model, OWASP mapping, สถานะตรงไปตรงมา (ยังไม่มี auth)
    + security gate ก่อน production
  - `AI_AGENT_GUIDE.md` (§23) — architecture rules, forbidden changes, safe refactoring,
    documentation rules, common mistakes จากประสบการณ์จริง
- อัปเดต `CLAUDE.md` ให้ index เอกสารชุดนี้

## 2026-07-06 — Sprint 3: Kanban Dashboard + Message Log + Portfolio

- **Backend:** เพิ่ม `GET /api/portfolio` — task counts ต่อสถานะทุกโปรเจกต์, รายชื่อ agents,
  deploy ล่าสุด (ตาราง deployments พร้อมแล้ว ค่าจริงเริ่ม Sprint 4); pytest 34 เคสผ่าน
- **Frontend scaffold:** Next.js **16.2.10** (create-next-app@latest — ใหม่กว่าแผนที่ระบุ 15)
  + TypeScript + Tailwind, App Router, `src/` layout
- **Portfolio page** (`/`): การ์ดโปรเจกต์ + แถบสัดส่วนสถานะ + agent pills
- **New Project page** (`/projects/new`): ครบวงจร STEP 1-4 ของ Blueprint §6 —
  กรอก requirement → PM Agent แตกงาน (หรือ scan mock สำหรับ existing) → เห็น plan → ยืนยัน scope
- **Kanban Board** (`/projects/[id]`): 8 คอลัมน์ตาม status, การ์ดแสดง assignee pill
  (🤖 agent role / 👤 human) + revision count, ปุ่มเปลี่ยนสถานะเฉพาะ transition ที่ถูกต้อง
  (mirror State Machine — backend ยังบังคับ 409 อีกชั้น), ปุ่ม "Run Agents" เรียก orchestrator
- **Message Log Viewer**: task detail panel แสดงบทสนทนา agent (handoff/result/review_comment/question)
- **Polling refresh (ADR-04)**: `usePolling` hook — refetch ทุก 4 วิ เฉพาะแท็บ active
- **E2E verified:** create → breakdown → confirm → run → done ผ่าน API + ทุกหน้า (/, /projects/new,
  /projects/[id]) ตอบ 200 บน production build

## 2026-07-06 — Sprint 2: Task Orchestration Engine + Solo Mode Runtime

- **State Machine** (`app/orchestrator/state_machine.py`): บังคับ transition ตาม Blueprint §5
  เท่านั้น — ผิด transition ตอบ **409**; ทุก transition เขียน `audit_log` อัตโนมัติ
  (`PATCH /api/tasks/:id` และ confirm-scope เปลี่ยนมาใช้เส้นทางนี้ทั้งหมด)
- **Routing Rules** (`app/agents/routing.py`): keyword heuristic → Senior Architect / Developer
  พร้อม log ทุก routing decision ลง audit (Risk #5)
- **Solo Mode Agent Runtime** (`app/agents/runtime.py`): `ClaudeExecutor` (persona prompt ตาม role)
  + `FallbackExecutor` (deterministic, ไม่มี network) — เพิ่ม personas DEV / ARCHITECT / REVIEWER
- **Orchestrator** (`app/orchestrator/engine.py`): planned → assigned → in_progress → review →
  done | revision loop | escalated; เคารพ dependency (`depends_on` ต้อง done ก่อน);
  Escalation Rule: review fail ครบ MAX_REVISIONS (2) → `escalated` + broadcast แจ้งผู้ใช้
- **Message Bus in-process** (`app/bus/` — ADR-03): ทุก handoff/result/review_comment/question
  ลงตาราง `agent_messages` เสมอ + fan-out ไป subscriber ใน process
- Endpoints ใหม่: `POST /api/projects/:id/run` (รัน orchestrator), `POST /api/agent-messages`
- pytest 32 เคสผ่าน (เพิ่ม 17: transition matrix, routing, bus, E2E happy path,
  revision loop, escalation, dependency ordering)

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
