"""add tasks.token_usage (โทเคนแยกตามผู้ให้บริการ)

Revision ID: f3a9c1d7e2b8
Revises: e5a91c73b204
Create Date: 2026-08-14

§5 ของใบสั่งงาน 2026-08-06: ราคาต่อโทเคนของแต่ละเจ้าไม่เท่ากัน เพดานก้อนเดียวจึงคุมไม่อยู่
เมื่อสลับเจ้า — ต้องนับแยกก่อนถึงจะมีถังให้แยก

`tokens_input`/`tokens_output` เดิม **ไม่ถูกแตะ** (ยังเป็นยอดรวมของ task เหมือนเดิม) ·
คอลัมน์ใหม่เป็น nullable เพราะ task ที่มีอยู่ก่อนวันนี้แยกที่มาไม่ได้จริง ๆ — ปล่อยเป็น NULL
แล้วให้รายงานนับเป็น "ไม่ทราบผู้ให้บริการ" ดีกว่าเดาย้อนหลังว่าเป็นของ Anthropic

⚠️ ต้อง `import app.db.types` เสมอ ไม่งั้น JSONType ที่เขียนใน migration หา type ไม่เจอ
(บทเรียนจริง Sprint 1 — autogenerate ลืม import แล้ว upgrade ตายทั้งชุด)
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.db.types  # noqa: F401 — ลงทะเบียน type decorator ให้ JSONType ข้างล่างใช้ได้
from app.db.types import JSONType

revision: str = "f3a9c1d7e2b8"
down_revision: str | None = "e5a91c73b204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("token_usage", JSONType(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "token_usage")
