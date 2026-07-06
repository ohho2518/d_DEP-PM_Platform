# AI_AGENT_GUIDE.md — DEP-PM Platform

> คู่มือสำหรับ AI Coding Agent (MASTER PROMPT §23) | อัปเดต: 2026-07-06 (หลัง Sprint 3)
> อ่านคู่กับ `CLAUDE.md` (workflow ต่อ session) — ไฟล์นี้เจาะกติกา "แตะโค้ดยังไงไม่พัง"

---

## ลำดับการอ่านก่อนเริ่มงาน
1. `CLAUDE.md` → 2. `PROJECT_STATUS.md` → 3. เอกสารเฉพาะทางตามงาน:
   - แตะ API → `docs/API.md` | แตะ schema/migration → `docs/DATABASE.md`
   - แตะ orchestrator/state → `docs/SYSTEM_DOCUMENTATION.md` §9 | แตะ frontend → §13 + `frontend/AGENTS.md`

## Architecture Rules (ห้ามฝ่าฝืน)

1. **ห้าม set `task.status` ตรง ๆ** — ผ่าน `app/orchestrator/state_machine.transition()` เท่านั้น
   (validate + audit ให้; ผิด transition ให้ API แปลงเป็น 409)
2. **ห้าม INSERT `agent_messages` ตรง ๆ** — ผ่าน `app/bus.publish()` เท่านั้น (ADR-03: persist เสมอ)
3. **`transition()` / `publish()` / `record_audit()` ไม่ commit** — router commit ต่อ request, engine commit ต่อ task
4. **Dependency direction** (ARCHITECTURE.md §4): `api → orchestrator/services → models → db` —
   ห้าม orchestrator import api, ห้าม models import schemas, ห้าม runtime import orchestrator
5. **ADR-01 (DB portability):** ห้าม raw SQL เฉพาะ dialect, UUID ผ่าน `GUID`, JSON ผ่าน SQLAlchemy `JSON`,
   ห้าม PostgreSQL array type
6. **จุดเสียบ (อย่า bypass):** provider ใหม่ = implement `PersonaExecutor` protocol; metadata จริง =
   implement `MetadataProvider`; อย่าแก้ orchestrator เพื่อ special-case provider ใดprovider หนึ่ง
7. **Frontend↔Backend sync:** แก้ status/transition/response shape ฝั่ง backend →
   แก้ `frontend/src/lib/types.ts` (type + `ALLOWED_TRANSITIONS` + `STATUS_ORDER`) **ในคอมมิตเดียวกัน**

## Forbidden Changes
- ❌ แก้/ลบไฟล์ `*.html` 3 ไฟล์ (read-only spec)
- ❌ แก้ migration ที่ apply แล้ว (`a14314b6f9a2`, `b2f1c0d3e4a5`) — สร้าง revision ใหม่เสมอ
- ❌ ใส่ secrets จริงในโค้ด/เอกสาร/commit (`.env` เท่านั้น)
- ❌ เปลี่ยน `MAX_REVISIONS` semantics โดยไม่อัปเดต SYSTEM_DOCUMENTATION §9 + tests
- ❌ ลบ fallback paths (no-key → fallback) — เป็นคุณสมบัติเชิงสัญญา ไม่ใช่โค้ดชั่วคราว
- ❌ major architecture change โดยไม่ผ่านผู้ใช้ (ต้องเป็น ADR ใหม่ใน DEVELOPMENT_PLAN §2)

## Safe Refactoring Rules
- เปลี่ยน internal ของ module ได้อิสระถ้า: (a) public signature คงเดิม (b) pytest 34 เคสผ่าน (c) กติกา 1-7 ข้างบนไม่แตก
- เพิ่ม endpoint: router บาง (HTTP↔service เท่านั้น) + Pydantic schema + test + อัปเดต `docs/API.md`
- เพิ่ม status ใหม่: ตามสูตรใน SYSTEM_DOCUMENTATION §21 (6 จุดต้องแก้พร้อมกัน)
- แตะ autogenerate migration: **ตรวจมือเสมอ** — เคยขาด `import app.db.types` (บทเรียนจริง Sprint 1)

## Coding Style / Naming
- Python: type hints ทุก signature, docstring ไทย+อังกฤษผสมตาม codebase เดิม, `from __future__ import annotations`
- Enums กลางอยู่ `constants.py` ที่เดียว — ห้าม string literal ของ status/role ในโค้ดใหม่ (ใช้ Enum.value)
- actor id ที่ใช้ใน audit/bus: `"orchestrator"`, `"pm-agent"`, `"stub-metadata"`, role values, `SOLO_AGENT_ID` — ใช้ค่าที่มีอยู่ อย่าประดิษฐ์ใหม่โดยไม่จำเป็น
- TS: types จาก `lib/types.ts` เท่านั้น อย่านิยาม interface ซ้ำในหน้า

## Testing Requirements
- ทุก endpoint ใหม่ → integration test ผ่าน TestClient (ดู conftest.py pattern)
- ทุกกติกา business ใหม่ → test เฉพาะ (ดู test_state_machine transition matrix เป็นแบบ)
- ห้าม mock HTTP ของ anthropic — inject executor ผ่าน `run_project(executor=…)` แทน
- รัน `pytest` เต็มก่อน commit เสมอ; frontend แตะแล้วรัน `npm run build` (คือ typecheck)

## Documentation Rules (ท้ายทุกงาน)
| งานที่ทำ | ต้องอัปเดต |
|----------|-----------|
| ทุกงาน meaningful | `PROJECT_STATUS.md` (7 หัวข้อตาม CLAUDE.md) |
| feature/behavior change | `CHANGELOG.md` |
| commands/structure/rules เปลี่ยน | `CLAUDE.md` |
| endpoint เปลี่ยน | `docs/API.md` |
| schema/migration | `docs/DATABASE.md` |
| state machine / business rule | `docs/SYSTEM_DOCUMENTATION.md` §9 |
| การตัดสินใจสถาปัตยกรรมใหม่ | ADR ใน `docs/DEVELOPMENT_PLAN.md` §2 + `docs/ARCHITECTURE.md` |

## Common Mistakes (จากประสบการณ์จริงในโปรเจกต์นี้)
1. ลืมว่า `params` ใน Next 16 เป็น `Promise` → ใช้ `React.use()` (ดู frontend/AGENTS.md)
2. commit เฉพาะเมื่อ `changes` ไม่ว่างใน PATCH — status-only PATCH เคยเกือบไม่ commit (แก้แล้ว — ระวังถ้า refactor)
3. Windows shell: Bash tool = Git Bash (POSIX), PowerShell แยกต่างหาก — `$_` ใน PowerShell ผ่าน bash จะโดนกิน
4. `confirm_scope` เคย set status ตรง ๆ (Sprint 1) — ถูกแก้เป็น transition แล้ว; อย่าถอยหลัง
