# AGENTS.md

> **Single source of truth for every AI coding agent working in this repository.**
> Claude Code, Gemini CLI, Codex, Cursor, and any other agent read this file.
> `CLAUDE.md` and `GEMINI.md` are pointers to this file — do not duplicate content there.

---

## 1. Role

You are an AI coding agent working inside this repository.

Your job: develop, maintain, debug, refactor, document, and improve this project — while **preserving existing behavior** unless the user explicitly asks for a change.

---

## 2. Read Before Every Task

| Order | File | When |
|---|---|---|
| 1 | `AGENTS.md` (this file) | Always |
| 2 | `PROJECT_STATUS.md` | Always — this is the continuity file |
| 3 | `WORKING_RULES.md` | Before touching code, DB, or UI |
| 4 | `CHANGELOG.md` | Only for history, release notes, or debugging past decisions |

**Do not scan the whole repository** unless the task genuinely requires it.

---

<!-- CANON-POINTER:START — สร้างโดย new-project-studio · แก้ต้นฉบับที่ 6_KM\d_InnoHub\_CANON\POINTER_BLOCK.md -->
## 📌 เอกสารกลาง (Canon) — อ่านจากต้นฉบับ ห้ามคัดลอกมาไว้ในโปรเจกต์นี้

ไฟล์ด้านล่างมี **ต้นฉบับเดียวของทั้ง Dev_Proj** อยู่ที่ `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\`
ถ้าต้องใช้ ให้เปิดอ่านจาก path นั้นตรงๆ — **ห้ามสร้างสำเนาไว้ในโปรเจกต์นี้**

| ต้องรู้เรื่อง | เปิดไฟล์นี้ |
|---|---|
| กฎความปลอดภัยตอนแก้โค้ด / ฐานข้อมูล / UI | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\WORKING_RULES.md` |
| สภาพแวดล้อมเครื่องที่ใช้พัฒนา | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\ENVIRONMENT.md` |
| ตัวเลข / ชื่อลูกค้า / อีเมล ที่ใช้ในเอกสารส่งออก | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\CANONICAL_FACTS.md` |
| พรอมป์ต์มาตรฐาน (สร้างเอกสาร / วิเคราะห์ระบบเดิม) | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\prompts\` |
| กติกาของคลังกลางเอง | `D:\Dev_Proj\6_KM\d_InnoHub\_CANON\README.md` |

**กฎเหล็ก 3 ข้อ**

1. ตัวเลข ชื่อลูกค้า อีเมล และวันที่ ที่จะปรากฏในเอกสารส่งออกภายนอก — ดึงจาก `CANONICAL_FACTS.md` เท่านั้น **ห้ามพิมพ์ใหม่จากความจำ**
2. เจอข้อมูลผิด → ไปแก้ที่ `_CANON/` **ห้ามแก้เฉพาะที่นี่**
3. **ห้ามก๊อบไฟล์ canon กลับเข้ามาในโปรเจกต์นี้** ไม่ว่าด้วยเหตุผลใด
<!-- CANON-POINTER:END -->

---

## 3. Project Overview

<!-- FILL THIS IN. Delete the placeholder once known. -->

- **Project name:** _Need confirmation_
- **Purpose:** _Need confirmation_
- **Target users:** _Need confirmation_
- **Main features:** _Need confirmation_
- **Current status:** Initializing

> Rule: if information is unclear, write `Need confirmation`. **Never guess.**

---

## 4. Tech Stack

<!-- Fill from actual repo inspection. Write "Not found" if absent. -->

| Item | Value |
|---|---|
| Language | _Not found_ |
| Framework | _Not found_ |
| Runtime | _Not found_ |
| Package manager | _Not found_ |
| Database | _Not found_ |
| ORM | _Not found_ |
| Authentication | _Not found_ |
| UI library | _Not found_ |
| Testing | _Not found_ |
| Deployment target | _Not found_ |

---

## 5. Project Structure

```text
src/            Main source code
app/            Routes / pages
components/     Reusable UI components
lib/            Shared utilities
api/            API handlers
database/       Schema, migrations, seed
tests/          Test files
docs/           Project documentation
```

> Replace with the real structure after inspecting the repo.

---

## 6. Commands

Only document commands that actually exist in the project. If absent, write `Not found. Need confirmation.`

```bash
# Install
_Not found_

# Development
_Not found_

# Build
_Not found_

# Test
_Not found_

# Lint / Format
_Not found_
```

---

## 7. Environment Variables

From `.env.example`, config files, or README. **Never write real secrets.**

```env
DATABASE_URL=required
PUBLIC_APP_URL=required
API_KEY=required, secret, do not commit
```

---

## 8. Architecture Notes

<!-- Fill after inspection -->

- Frontend structure: _Not found_
- Backend structure: _Not found_
- API structure: _Not found_
- Database structure: _Not found_
- Auth flow: _Not found_
- External services: _Not found_
- Key decisions and why: _Not found_

---

## 9. Coding Rules

1. Read the relevant files **before** editing.
2. Make the **smallest safe change**.
3. Do not rewrite whole files unless necessary.
4. Preserve existing behavior.
5. Match the existing code style.
6. Do not add dependencies without a stated reason.
7. Do not remove features without user approval.
8. Never hardcode secrets.
9. Prefer clear and maintainable over clever.
10. State your assumption **before** making any major change.

---

## 10. Task Workflow

For **every** task:

1. Read `AGENTS.md` + `PROJECT_STATUS.md`.
2. Identify **only** the files needed for this task.
3. Inspect those files before editing.
4. Back up per `WORKING_RULES.md` if the file is being modified.
5. Make minimal changes.
6. Run tests / lint / build if available.
7. Update `PROJECT_STATUS.md`.
8. Update `CHANGELOG.md` if user-facing behavior changed.
9. Update `AGENTS.md` if architecture, commands, structure, or rules changed.

---

## 11. Context Efficiency

To keep sessions cheap and continuable:

- Do not scan the whole project by default.
- Do not open unrelated files.
- Prefer targeted reads.
- `PROJECT_STATUS.md` is the **main continuity file** — keep it current and concise.
- Move long history to `CHANGELOG.md`.
- Keep `AGENTS.md` about stable rules, **not** daily progress.

---

## 12. Domain Rules

### Database

1. Inspect the schema before changing DB code.
2. Never change schema without a migration strategy.
3. No destructive migrations or data deletion unless explicitly requested.
4. Keep schema, API, types, and UI aligned.
5. Update docs after schema changes.
6. **Back up before any DB change** — see `WORKING_RULES.md`.

### UI

1. Reuse existing components.
2. Keep design and responsive behavior consistent.
3. No redesign unless requested.
4. Log visible behavior changes in `CHANGELOG.md`.

### API

1. Preserve existing request/response contracts unless asked.
2. Validate all input.
3. Handle errors safely; never leak internal errors to users.
4. Update related frontend calls when an API changes.

---

## 13. Common Tasks

**New feature:** understand current flow → locate related files → implement the smallest complete version → add validation + error handling → run checks → update status files.

**Bug fix:** reproduce or understand → find the root cause → fix only the related code → check for side effects → update status.

**Refactor:** preserve behavior → keep it small → never mix refactor with feature changes → run checks.

---

## 14. Never Do

- Commit secrets, API keys, tokens, private keys, or customer data.
- Delete important files.
- Rewrite the whole project.
- Change business logic outside the requested task.
- Upgrade major dependencies without approval.
- Format the entire repository unless requested.
- Guess a command that does not exist in the project.

---

## 15. End-of-Task Report

Always close with:

1. **Files changed**
2. **What changed**
3. **Why**
4. **Checks run** (test / lint / build) and results
5. **Not completed / known issues**
6. **Recommended next step**
