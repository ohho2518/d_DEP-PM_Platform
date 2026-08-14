"""scaffold.py — แกน deterministic (AI-free) ของ new-project-studio

ทำงานเสมอ ไม่ง้อ AI (สอดคล้อง d_OS ADR-2): copy kit, git init, .gitignore,
requirements.txt, .env.example, reset สถานะ, และเติมช่องพื้นฐานของ AGENTS.md
จาก input ที่ผู้ใช้กรอกในฟอร์ม

ทุกไฟล์เขียนด้วย UTF-8 ผ่าน pathlib.write_text(encoding="utf-8") — ห้ามใช้ทางอื่น (กันไทยพัง)
"""
from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
from pathlib import Path

from app.config import get_settings


def _allowed_root() -> Path:
    """รากที่อนุญาตให้ scaffold ลงไปได้ — กันสร้างโฟลเดอร์นอกพื้นที่งานโดยไม่ตั้งใจ."""
    return Path(get_settings().scaffold_allowed_root).resolve()


def _kit() -> Path:
    """Project Starter Kit — ค่าปริยายคือชุดที่มากับรีโปนี้ (`app/scaffold_kit/`).

    ย้ายมาจาก `new-project-studio` ตอน ADR-05 · รีโปนั้นหยุดพัฒนาแล้ว
    **เจ้าของแม่แบบคือที่นี่** — แก้ที่นี่ที่เดียว
    """
    configured = get_settings().scaffold_kit_path.strip()
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[1] / "scaffold_kit"

# ไฟล์เอกสารราก (active kit) ที่คัดลอกเข้าโปรเจ็คใหม่ — ยกเว้น _archive/ และ README ของ kit
# WORKING_RULES.md / ENVIRONMENT.md ไม่อยู่ในนี้แล้ว — ย้ายเป็น canon (ดู inject_canon_pointer)
KIT_ROOT_DOCS = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
]
KIT_DIRS = ["docs", "prompts"]

# ---------------------------------------------------------------------------
# คลังเอกสารกลาง (Canon) — ต้นฉบับเดียวของทั้ง Dev_Proj
# โปรเจกต์ใหม่ต้องได้ "ตัวชี้" ไปที่นี่เสมอ ห้ามได้สำเนา
# ถ้าย้าย _CANON ให้แก้ CANON_ROOT ที่เดียว
# ---------------------------------------------------------------------------
CANON_ROOT = Path(os.environ.get("CANON_ROOT", r"D:\Dev_Proj\6_KM\d_InnoHub\_CANON"))

# ที่อยู่เอกสาร contract ของ d_CEO — เขียนเป็นตัวแปร ไม่ hardcode ในเทมเพลต
#
# ⚠️ เคย hardcode เป็น `D:\Dev_Proj\d_CEO\docs` ซึ่งตายไปตั้งแต่ reorg 2026-07-25
# (Dev_Proj จัดใหม่เป็น 7 โฟลเดอร์ทีม → d_CEO ย้ายเข้า 0_CORE) ทุกโปรเจ็คที่ bootstrap
# หลังจากนั้นจึงได้ INTEGRATION_CEO.md ที่ชี้ไปโฟลเดอร์ที่ไม่มีอยู่จริง — เจอกับ
# d_Researcher 2026-07-26 · แก้ที่นี่ที่เดียวแล้วโปรเจ็คใหม่ทุกตัวได้ path ที่ถูก
# (override ได้ด้วย env CEO_DOCS ถ้าโครงสร้างเปลี่ยนอีก)
CEO_DOCS = os.environ.get("CEO_DOCS", r"D:\Dev_Proj\0_CORE\d_CEO\docs")
CANON_POINTER_FILE = CANON_ROOT / "POINTER_BLOCK.md"
CANON_MARK_START = "<!-- CANON-POINTER:START"
CANON_MARK_END = "<!-- CANON-POINTER:END -->"

_CANON_POINTER_FALLBACK = r"""<!-- CANON-POINTER:START — สร้างโดย new-project-studio · แก้ต้นฉบับที่ 6_KM\d_InnoHub\_CANON\POINTER_BLOCK.md -->
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
<!-- CANON-POINTER:END -->"""

# .gitignore แม่แบบ secrets-first (จาก d_OS Lite) + Python + _design_input/
GITIGNORE = """\
# --- ความลับ — ห้ามหลุดขึ้น git เด็ดขาด ---
.env
.env.*
!.env.example
*.env
service_account.json
*service_account*.json
*credentials*.json
*-key.json
# OAuth (บัญชีผู้ใช้)
credentials.json
token.json
*token*.json

# --- Python ---
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/

# --- ไฟล์ดีไซน์ที่อัปโหลดเข้ามา (input อ่านอย่างเดียว ไม่เก็บเข้า repo) ---
_design_input/

# --- ของสำรอง / local ---
BackUp/
.claude/settings.local.json
"""

ENV_EXAMPLE = """\
# ห้าม commit ค่าจริง — ไฟล์นี้เป็นแม่แบบเท่านั้น (WORKING_RULES Rule 8)
# API_KEY=required, secret, do not commit
"""

# --- ความเกี่ยวข้องกับ ecosystem (เลือกจากฟอร์มตอน bootstrap) ---
# ลำดับชั้น ecosystem: d_CEO >> d_Jarvis >> Team >> เครื่องมือของทีม >> Product/Services
# ชั้นขวาง: Middleware/Engine กลาง (OCR, STT, PDF ฯลฯ) ให้ทุกชั้นเรียกใช้ — และขายเป็น Product ได้
# (Product/Services = ระดับสุดท้าย เป็นงานของ Dev Team · เครื่องมือของทีม/middleware เป็น Product/Service ได้ด้วย)
RELATION_LABELS = {
    "eco-core": "Ecosystem d_PROaiInnotech — แกนกลาง (ระดับ d_CEO / d_Jarvis)",
    "eco-team": "Ecosystem d_PROaiInnotech — เครื่องมือของทีม",
    "middleware": "Ecosystem d_PROaiInnotech — Middleware/Engine กลาง (เช่น OCR, STT, PDF)",
    "product": "Product (ระดับสุดท้ายของ ecosystem — งาน Dev Team)",
    "service": "Service — งานบริการลูกค้า tailor-made (ระดับสุดท้ายของ ecosystem — งาน Dev Team)",
    "general": "งานทั่วไป (ไม่ใช่งานพัฒนาโค้ด)",
}
# ชั้นที่เชื่อม d_CEO โดยตรง → ได้ INTEGRATION_CEO.md เพิ่มจากชุดเอกสาร dev มาตรฐาน
# (middleware ไม่ได้ contract กับ d_CEO — ตัวมันเป็น provider ของ API ตัวเอง = docs/API.md)
_CONTRACT_RELATIONS = {"eco-core", "eco-team"}
# งาน dev ทุกประเภท → ได้ชุดเอกสาร dev มาตรฐาน (API/DATABASE/SECURITY) โครงเดียวกันทุกโปรเจ็ค
_DEV_RELATIONS = {"eco-core", "eco-team", "middleware", "product", "service"}
# ชั้นที่ติ๊ก "เป็น Product/Service ด้วย" ได้
_DUAL_PS_RELATIONS = {"eco-team", "middleware"}

# โครงเอกสารมาตรฐาน ecosystem — แบบเดียวกับ d_CEO (docs/API.md ฯลฯ) · ช่องที่ไม่รู้ = Need confirmation
_API_DOC = """\
# API — {name}

> อัปเดต: {today} — Phase 0 (scaffold — ยังไม่มี endpoint จริง)
> มาตรฐาน ecosystem (ตาม d_CEO): ทุก endpoint รับ org context ผ่าน header `X-Org-Id`
> (ไม่ส่ง = org default) · เวลาเก็บ/คืนเป็น UTC

## Health
| method | path | คำอธิบาย |
|---|---|---|
| GET | `/health` | `{{"status":"ok"}}` — Need confirmation |

## Endpoints

_Need confirmation — เติมเมื่อออกแบบ API จริง (ใช้ตารางรูปแบบเดียวกับ Health)_
"""

_DATABASE_DOC = """\
# DATABASE — {name}

> อัปเดต: {today} — Phase 0 · Source of truth: _Need confirmation (ชี้ไฟล์ models จริง)_

## หลักการบังคับ (มาตรฐาน ecosystem — ตาม d_CEO)

- ทุกตารางมี `org_id` (platform from day one) — FK → `orgs.id`
- status/verdict/category เก็บเป็น string (ค่าคงที่ใน constants) — ไม่ใช้ DB enum
- id เป็น UUID (portable: Postgres = UUID, SQLite = CHAR(32))
- timestamps เป็น UTC
- schema จัดการด้วย Alembic ทั้ง dev และ prod — startup ต้อง**ไม่**สร้างตารางเอง

## ตาราง

| ตาราง | คอลัมน์หลัก | หมายเหตุ |
|---|---|---|
| _Need confirmation_ | | |
"""

_SECURITY_DOC = """\
# SECURITY — {name}

> อัปเดต: {today} · อยู่ภายใต้ SOP_Secret_Management (มาตรฐาน ecosystem)

## หลักการ

- Commit ได้เฉพาะ `.env.example` — `.gitignore` ครอบ `.env*` ตั้งแต่ commit แรก
- อ่าน secret ผ่าน config กลางตัวเดียว — ห้าม `os.environ` กระจายทั่วโค้ด
- ห้ามส่ง key ทาง URL query string · ห้าม log ค่า secret
- credential ของ integration ภายนอกเก็บแบบ encrypted + scope ต่อ org — ไม่ใช้ env รวมก้อน

## ทะเบียน key (Key Registry)

> คอลัมน์ "ที่อยู่" คือ *ตำแหน่ง* ไม่ใช่ค่า secret

| ชื่อ key | วัตถุประสงค์ | ที่อยู่ | สถานะ |
|---|---|---|---|
| _Need confirmation_ | | | |

## Checklist ก่อน commit แรก

- [ ] `.gitignore` ครอบ `.env*` (ยกเว้น `.env.example`)
- [ ] `.env.example` ครบทุก key ที่แอปอ่าน พร้อมคำอธิบาย ไม่มีค่าจริง
- [ ] ไม่มีค่า secret ใน source/config/test/docs
"""

_INTEGRATION_CEO_DOC = """\
# INTEGRATION_CEO.md — Contract ร่วม {name} ↔ d_CEO

> **Provider (เจ้าของ contract ฝั่งสมอง) = d_CEO** — สเปคเต็ม:
> `{ceo_docs}\\INTEGRATION_JARVIS.md` + `{ceo_docs}\\API.md`
> **Contract version:** v0 (ยังไม่เชื่อมจริง — Need confirmation) · **Last synced:** {today}

## การเชื่อมต่อ (Connection)

| เรื่อง | ค่า |
|---|---|
| Base URL | `http://127.0.0.1:8000` (bind 127.0.0.1 เท่านั้น — API ไม่มี auth ใน Phase 1) |
| `X-Org-Id` | ไม่ส่ง = org default `dproai-innotech` · ถ้าส่งต้องเป็น UUID (ไม่งั้น 400) |
| Timezone | d_CEO เก็บ/คืน **UTC** — ฝั่งนี้ต้อง convert → Asia/Bangkok ก่อนแสดงผล |
| Content-Type | `application/json` |

## Endpoints ของ d_CEO ที่ใช้ได้ (contract v2 ณ วันที่ scaffold)

`GET /health` · `GET /teams` · `POST /tasks` · `GET /tasks?status=&limit=` ·
`GET /tasks/{{id}}` · `GET /tasks/summary` · `PATCH /tasks/{{id}}` (เลื่อนสถานะ + เขียน output)

> Task statuses: `queued` · `in_progress` · `qc_review` · `awaiting_approval` · `done` · `rejected`
> (ยึดตาม `app/constants.py` ของ d_CEO — ห้าม hardcode ซ้ำโดยเดาเอง)

## กฎเมื่อเปลี่ยน contract (มาตรฐาน ecosystem)

1. เปลี่ยนแบบ **additive / backward-compatible เท่านั้น** (เพิ่ม field/endpoint · ห้ามลบ/เปลี่ยนความหมายของเดิม)
2. **Provider แก้เสมอ → แล้วค่อยฝั่ง consumer**
3. bump `Contract version` + `Last synced` + อัปเดต `PROJECT_STATUS.md` ทั้งสอง repo
4. ฝั่งนี้เรียกผ่าน client เดียว (เช่น `ceo_client`) — ห้ามยิง d_CEO ตรงกระจายทั่วโค้ด
5. error ทุกชนิด (timeout/connect/5xx) → degrade graceful — ระบบฝั่งนี้ต้องไม่ crash

## จุดที่โปรเจ็คนี้จะใช้ (เติมเมื่อออกแบบจริง)

_Need confirmation_
"""

DEV_DOCS = {
    "docs/API.md": _API_DOC,
    "docs/DATABASE.md": _DATABASE_DOC,
    "docs/SECURITY.md": _SECURITY_DOC,
}
CONTRACT_DOC = {"docs/INTEGRATION_CEO.md": _INTEGRATION_CEO_DOC}


class ScaffoldError(RuntimeError):
    """ข้อผิดพลาดของส่วน deterministic — ถ้าเกิดถือว่า bootstrap ล้มเหลวจริง"""


def _today() -> str:
    return dt.date.today().isoformat()


# ---------------------------------------------------------------------------
# โฟลเดอร์ทีมใต้ ALLOWED_ROOT — ปลายทางมาตรฐานของโปรเจกต์ใหม่
# (จัดระเบียบ Dev_Proj 2026-07-25: หนึ่งโปรเจกต์ = หนึ่งทีมเจ้าของ · ห้ามวางที่ราก)
# อ่านรายชื่อจากดิสก์จริง ไม่ hardcode — เพิ่ม/เปลี่ยนชื่อทีมแล้วฟอร์มตามเองโดยไม่ต้องแก้โค้ด
# ---------------------------------------------------------------------------
_TEAM_DIR_RE = re.compile(r"^\d+_")
INBOX_DIR = "_INBOX"
TEAM_HINTS = {
    "0_CORE": "เลขา/Orchestrator + ระบบกลาง",
    "1_SALES_MKT": "ขาย + การตลาด",
    "2_FINANCE": "การเงิน / บัญชี",
    "3_DELIVERY": "ส่งมอบ + งานลูกค้าที่ใช้จริง",
    "4_RND": "วิจัยและพัฒนา",
    "5_QC": "ควบคุมคุณภาพ",
    "6_KM": "คลังความรู้",
    INBOX_DIR: "ยังไม่จัดทีม — ต้องย้ายออกภายใน 7 วัน",
}


def list_teams() -> list[dict]:
    """คืนโฟลเดอร์ทีมใต้ ALLOWED_ROOT เรียงตามเลขนำหน้า (+ _INBOX ท้ายสุดถ้ามี)

    คืน [] ถ้าไม่มีโฟลเดอร์ทีมเลย → UI กลับไปเป็นแบบพิมพ์ path เองเหมือนเดิม
    """
    root = _allowed_root()
    try:
        names = sorted(
            d.name for d in root.iterdir() if d.is_dir() and _TEAM_DIR_RE.match(d.name)
        )
    except OSError:
        return []
    if (root / INBOX_DIR).is_dir():
        names.append(INBOX_DIR)
    return [{"name": n, "hint": TEAM_HINTS.get(n, "")} for n in names]


def resolve_target(target: str) -> Path:
    """คืน Path ที่ resolve แล้ว พร้อม validate ว่าอยู่ใต้ allowed_root (กัน scaffold โฟลเดอร์มั่ว)"""
    t = target.strip()
    # ซ่อม path แบบ drive-relative ("D:Dev_Proj\x" — backslash หลัง drive หาย
    # เช่นจากค่าเก่าที่ browser จำไว้) — ไม่งั้น resolve จะพาไปใต้ cwd แบบเงียบ ๆ
    if re.match(r"^[A-Za-z]:(?![\\/])", t):
        t = t[:2] + "\\" + t[2:]
    p = Path(t).resolve()
    root = _allowed_root()
    if root not in p.parents and p != root:
        raise ScaffoldError(
            f"target ต้องอยู่ใต้ {root} เท่านั้น — ได้ {p}"
        )
    return p


def copy_kit(target: Path) -> list[str]:
    """คัดลอก active kit เข้า target — ยกเว้น _archive/ และ README ของ kit · คืนรายชื่อไฟล์ที่สร้าง"""
    kit = _kit()
    if not kit.is_dir():
        raise ScaffoldError(f"ไม่พบ Project Starter Kit ที่ {kit}")
    created: list[str] = []
    for name in KIT_ROOT_DOCS:
        src = kit / name
        if src.is_file():
            shutil.copy2(src, target / name)
            created.append(name)
    for d in KIT_DIRS:
        src = kit / d
        if src.is_dir():
            shutil.copytree(src, target / d, dirs_exist_ok=True)
            created.append(f"{d}/")
    return created


def git_init(target: Path) -> str:
    """git init -b main (ข้ามถ้าเป็น repo แล้ว) · คืนข้อความสถานะ"""
    if (target / ".git").is_dir():
        return "git: เป็น repo อยู่แล้ว (ข้าม)"
    try:
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=target, check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise ScaffoldError(f"git init ล้มเหลว: {e}") from e
    return "git: init branch main"


def git_commit_initial(target: Path) -> str:
    """git add -A + commit แรก (ปุ่ม commit ใน UI หลัง bootstrap) · คืนข้อความสถานะ

    ใช้ git identity ของเครื่อง · ไม่มีอะไรให้ commit = ไม่ error (คืนข้อความเฉย ๆ)
    """
    if not (target / ".git").is_dir():
        raise ScaffoldError("ยังไม่เป็น git repo — ต้อง bootstrap ก่อน")
    try:
        subprocess.run(["git", "add", "-A"], cwd=target,
                       check=True, capture_output=True, text=True)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=target,
                            check=True, capture_output=True, text=True)
        if not st.stdout.strip():
            return "git: ไม่มีอะไรให้ commit (clean อยู่แล้ว)"
        subprocess.run(
            ["git", "commit", "-m", "chore: initial bootstrap (new-project-studio)"],
            cwd=target, check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        detail = (getattr(e, "stderr", "") or str(e)).strip()
        raise ScaffoldError(f"git commit ล้มเหลว: {detail}") from e
    return "git: commit แรกเรียบร้อย"


def write_gitignore(target: Path) -> None:
    (target / ".gitignore").write_text(GITIGNORE, encoding="utf-8")


def write_requirements(target: Path, name: str) -> None:
    """requirements.txt สำหรับงาน Python — pinned >= ตาม convention d_OS"""
    content = (
        f"# {name} — Python dependencies (pin ด้วย >=, ตาม convention d_OS)\n"
        "python-dotenv>=1.0\n"
    )
    (target / "requirements.txt").write_text(content, encoding="utf-8")


def write_env_example(target: Path) -> None:
    (target / ".env.example").write_text(ENV_EXAMPLE, encoding="utf-8")


def write_ecosystem_docs(target: Path, name: str, include_contract: bool) -> list[str]:
    """สร้างชุดเอกสาร dev มาตรฐาน (โครงเดียวกันทุกโปรเจ็ค) · contract เฉพาะชั้นที่เชื่อม d_CEO
    · ไม่ทับไฟล์ที่มีอยู่"""
    docs = dict(DEV_DOCS)
    if include_contract:
        docs.update(CONTRACT_DOC)
    created: list[str] = []
    for rel, template in docs.items():
        p = target / rel
        if p.exists():
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            template.format(name=name, today=_today(), ceo_docs=CEO_DOCS), encoding="utf-8"
        )
        created.append(rel)
    return created


def inject_canon_pointer(target: Path) -> bool:
    """แทรกบล็อกชี้ไปคลังเอกสารกลาง (_CANON) ลงใน AGENTS.md

    อ่านต้นฉบับจาก CANON_POINTER_FILE ถ้าเปิดได้ ไม่งั้นใช้สำเนา fallback ในไฟล์นี้
    (fallback มีไว้กันกรณีไดรฟ์กลางไม่ว่าง — โปรเจกต์ใหม่ต้องได้ pointer เสมอ)
    idempotent: ถ้ามีบล็อกอยู่แล้วจะแทนที่ของเดิม ไม่ต่อท้ายซ้ำ
    """
    f = target / "AGENTS.md"
    if not f.is_file():
        return False

    block = _CANON_POINTER_FALLBACK
    try:
        src = CANON_POINTER_FILE.read_text(encoding="utf-8")
        if CANON_MARK_START in src and CANON_MARK_END in src:
            block = src[src.index(CANON_MARK_START): src.index(CANON_MARK_END) + len(CANON_MARK_END)]
    except OSError:
        pass  # ไดรฟ์กลางไม่ว่าง — ใช้ fallback

    text = f.read_text(encoding="utf-8")
    if CANON_MARK_START in text and CANON_MARK_END in text:
        head = text[: text.index(CANON_MARK_START)]
        tail = text[text.index(CANON_MARK_END) + len(CANON_MARK_END):]
        f.write_text(head + block + tail, encoding="utf-8")
        return True

    # แทรกก่อนหัวข้อ "## 3." (Project Overview) ถ้าหาเจอ ไม่งั้นต่อท้ายไฟล์
    anchor = "\n## 3. "
    if anchor in text:
        i = text.index(anchor)
        text = text[:i] + "\n" + block + "\n\n---\n" + text[i:]
    else:
        text = text.rstrip() + "\n\n---\n\n" + block + "\n"
    f.write_text(text, encoding="utf-8")
    return True


def fill_agents_basics(target: Path, name: str, purpose: str, stack: str,
                       relation: str = "general", team: str = "",
                       dual_ps: bool = False) -> None:
    """เติมช่องพื้นฐานของ AGENTS.md จาก input ฟอร์ม (deterministic) — ที่เหลือ AI/ผู้ใช้เติมต่อ"""
    f = target / "AGENTS.md"
    if not f.is_file():
        return
    text = f.read_text(encoding="utf-8")
    label = RELATION_LABELS.get(relation, RELATION_LABELS["general"])
    if team:
        label += f" — {team}"
    if dual_ps and relation in _DUAL_PS_RELATIONS:
        label += " · เป็น Product/Service ด้วย"
    repl = {
        "- **Project name:** _Need confirmation_":
            f"- **Project name:** {name}\n- **Ecosystem:** {label}",
    }
    if purpose:
        repl["- **Purpose:** _Need confirmation_"] = f"- **Purpose:** {purpose}"
    if stack:
        repl["| Language | _Not found_ |"] = f"| Language | {stack} |"
    for old, new in repl.items():
        text = text.replace(old, new)
    f.write_text(text, encoding="utf-8")


def reset_status_changelog(target: Path, name: str) -> None:
    """PROJECT_STATUS.md / CHANGELOG.md → initial state พร้อมวันที่วันนี้"""
    today = _today()
    status = f"""\
# PROJECT_STATUS.md

> **The continuity file.** ทุก AI session อ่านไฟล์นี้ก่อน และอัปเดตเป็นอย่างสุดท้าย
> ประวัติยาวไปไว้ที่ `CHANGELOG.md`

**Last updated:** {today}
**Updated by:** new-project-studio (initial bootstrap)

---

## Current State

Project bootstrapped ({name}). Docs + git in place; code not yet started.

---

## Completed

- [x] Documentation kit installed (จาก Project Starter Kit)
- [x] git initialized (branch main)
- [x] .gitignore + requirements.txt + .env.example scaffolded

---

## In Progress

_Nothing yet._

---

## Next Recommended Task

1. เติมช่อง `Need confirmation` ใน `AGENTS.md` §3/§4 และ `docs/PROJECT_OVERVIEW.md` (โดยเฉพาะ non-goals)
2. Scaffold โค้ด แล้วบันทึกคำสั่งจริงลง `AGENTS.md` §6
3. พร้อมแล้วค่อย `git commit`

---

## Known Issues

_None._

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| {today} | Bootstrapped ด้วย new-project-studio | ลดงานตั้งต้นซ้ำ ๆ ทุกโปรเจ็คใหม่ |
"""
    (target / "PROJECT_STATUS.md").write_text(status, encoding="utf-8")

    changelog = f"""\
# CHANGELOG

ทุกการเปลี่ยนแปลงที่ผู้ใช้เห็นผล บันทึกที่นี่ (Keep a Changelog + SemVer)

## [Unreleased] — {today}

### Added
- ตั้งต้นโปรเจ็ค {name} (docs + git) ด้วย new-project-studio
"""
    (target / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def scaffold(
    target_str: str,
    name: str,
    purpose: str = "",
    stack: str = "",
    is_python: bool = True,
    relation: str = "general",
    team: str = "",
    dual_ps: bool = False,
) -> dict:
    """orchestrate ส่วน deterministic ทั้งหมด · คืน manifest ให้ UI โชว์

    ทำงานเสมอแม้ไม่มี AI — คืน dict {target, created[], steps[], is_python, relation}
    relation: general | product | service | middleware | eco-team | eco-core
      งาน dev ทุกประเภท → เอกสาร dev มาตรฐาน · eco-core/eco-team → + INTEGRATION_CEO.md
    team: ทีมที่สังกัด (ใช้กับ eco-team เช่น "Marketing Team — d_MOS")
    dual_ps: เป็น Product/Service ด้วย (ใช้กับ eco-team / middleware)
    """
    if relation not in RELATION_LABELS:
        raise ScaffoldError(f"relation ไม่รู้จัก: {relation!r} — ต้องเป็น {sorted(RELATION_LABELS)}")
    target = resolve_target(target_str)
    target.mkdir(parents=True, exist_ok=True)

    steps: list[str] = []
    # เตือน (ไม่บล็อก) ถ้าวางไว้ที่รากทั้งที่มีโฟลเดอร์ทีมอยู่แล้ว — กฎจัดระเบียบ 2026-07-25
    if target.parent == _allowed_root() and list_teams():
        steps.append(
            "⚠ วางไว้ที่รากของ Dev_Proj — ตามกฎจัดระเบียบ โปรเจกต์ควรอยู่ใต้โฟลเดอร์ทีม "
            f"(หรือ {INBOX_DIR} ถ้ายังไม่รู้ว่าทีมไหน)"
        )

    created = copy_kit(target)
    steps.append(f"คัดลอก kit: {len(created)} รายการ")

    fill_agents_basics(target, name, purpose, stack, relation, team.strip(), dual_ps)
    steps.append("เติม AGENTS.md §3/§4 จากฟอร์ม")

    if inject_canon_pointer(target):
        steps.append("แทรกตัวชี้ไปคลังเอกสารกลาง (_CANON) ใน AGENTS.md")

    if relation in _DEV_RELATIONS:
        with_contract = relation in _CONTRACT_RELATIONS
        eco = write_ecosystem_docs(target, name, with_contract)
        created += eco
        detail = "รวม INTEGRATION_CEO.md" if with_contract else "API/DATABASE/SECURITY"
        steps.append(f"สร้างเอกสาร dev มาตรฐาน: {len(eco)} ไฟล์ ({detail})")

    reset_status_changelog(target, name)
    steps.append("reset PROJECT_STATUS.md / CHANGELOG.md")

    write_gitignore(target)
    created.append(".gitignore")
    steps.append("เขียน .gitignore (secrets-first)")

    if is_python:
        write_requirements(target, name)
        write_env_example(target)
        created += ["requirements.txt", ".env.example"]
        steps.append("เขียน requirements.txt + .env.example")

    steps.append(git_init(target))

    return {
        "target": str(target),
        "created": created,
        "steps": steps,
        "is_python": is_python,
        "relation": relation,
    }
