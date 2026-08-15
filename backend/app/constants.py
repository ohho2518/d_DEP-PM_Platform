"""Shared enums/constants for the domain model (Blueprint §4-5).

Stored as plain strings in the DB (portable across SQLite/PostgreSQL — ADR-01) but
exposed as ``str, Enum`` so both Pydantic and business logic can validate against them.
"""
from __future__ import annotations

from enum import Enum


class ProjectType(str, Enum):
    NEW = "new"
    EXISTING = "existing"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ProjectKind(str, Enum):
    """ชนิดงาน — ตัดสินว่า "เส้นทาง 6 ขั้น" เปิดขั้นไหนบ้าง (ผู้ใช้เลือกเอง เดาจากข้อมูลไม่ได้).

    คนละเรื่องกับ ``ProjectType`` (new/existing) ซึ่งบอกว่า *มาจากไหน* —
    ตัวนี้บอกว่า *ผลลัพธ์เป็นอะไร* : โค้ดที่ deploy ได้ · เอกสารที่ส่งมอบ · หรือไอเดียที่ยังไม่ลงมือ
    """

    CODE = "code"  # มีโค้ด → ครบทุกขั้น (ขั้น 5 = commit + deploy)
    DOC = "doc"  # งานเอกสาร → ข้ามขั้นโครงสร้าง · ขั้น 5 = ส่งมอบไฟล์
    IDEA = "idea"  # เก็บไว้ต่อยอด → เส้นสั้น จบที่ "ยกระดับเป็นโปรเจกต์จริง"


class ProjectStage(str, Enum):
    """ขั้นบนเส้นทางงาน — **คำนวณจากของจริง ไม่ได้เก็บในฐานข้อมูล** (ดู services/stages.py).

    เจตนา: ไม่มีใครต้องมากดอัปเดตสถานะให้ตรง — ระบบอ่านจากโฟลเดอร์/task/deployment ที่มีอยู่จริง
    จึงโกหกไม่ได้ (บทเรียนเดียวกับ "รายงานเกินจริง" ที่ QC จับได้ 3 ส.ค.)
    """

    IDEA = "idea"  # 1 ไอเดีย — มีโจทย์แล้ว
    STRUCTURE = "structure"  # 2 โครงสร้าง — มีโฟลเดอร์จริงบนดิสก์
    PLAN = "plan"  # 3 แผนงาน — มี task รอยืนยัน scope
    BUILD = "build"  # 4 ลงมือ — มีงานที่ agent ทำได้แล้ว
    SHIP = "ship"  # 5 ส่งขึ้นระบบ / ส่งมอบ — งานพัฒนาเสร็จครบ
    MARKET = "market"  # 6 การตลาด — ส่งร่างเข้า d_MOS แล้ว


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    DEPLOYED = "deployed"
    ESCALATED = "escalated"  # revision failed MAX_REVISIONS times (Blueprint §5)


class AssigneeType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"


class AgentRole(str, Enum):
    PM = "pm"
    DEV = "dev"
    SENIOR_ARCHITECT = "senior_architect"
    REVIEWER = "reviewer"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class AgentProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class AgentMode(str, Enum):
    SOLO = "solo"
    TEAM = "team"


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"


class MessageType(str, Enum):
    HANDOFF = "handoff"
    QUESTION = "question"
    RESULT = "result"
    REVIEW_COMMENT = "review_comment"


class DeploymentTrigger(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class DeploymentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ActorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"


class RunStatus(str, Enum):
    """สถานะของ **รอบรัน orchestrator** (Phase 2) — อยู่ในหน่วยความจำ ไม่ใช่คอลัมน์ใน DB.

    คนละเรื่องกับ ``DeploymentStatus`` ที่บังเอิญมีค่าใกล้กัน: อันนั้นคือ CI ปลายทาง
    """

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    # ผู้ใช้สั่งหยุด — orchestrator หยุด "ระหว่างช่อง" ระหว่าง task ไม่ตัดกลาง task
    CANCELLED = "cancelled"


# Escalation Rule — Max Revision = 2 (Blueprint §5 / DEVELOPMENT_PLAN §4).
MAX_REVISIONS = 2
