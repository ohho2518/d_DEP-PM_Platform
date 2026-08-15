"""add projects.kind (ชนิดงาน: code | doc | idea)

Revision ID: b6e2f4a81c39
Revises: a1c8e5f92d47
Create Date: 2026-08-15

เส้นทาง 6 ขั้น (ไอเดีย → โครงสร้าง → แผนงาน → ลงมือ → ส่งขึ้นระบบ → การตลาด) ไม่ได้เปิดครบ
ทุกชนิดงาน: งานเอกสารข้ามขั้นโครงสร้าง · ไอเดียเดินแค่สองขั้นแรกแล้วรอ "ยกระดับ"
⇒ ต้องรู้ชนิดงานก่อนถึงจะรู้ว่าเส้นทางของโปรเจกต์นั้นมีขั้นอะไรบ้าง

**ขั้น (stage) ไม่ได้เก็บเป็นคอลัมน์** โดยตั้งใจ — คำนวณจากของจริงทุกครั้งที่อ่าน
(โฟลเดอร์ · task · deployment) เพื่อไม่ให้มีสถานะที่ค้างไม่ตรงกับความจริง ดู `services/stages.py`

``server_default='code'`` เพื่อให้แถวเดิมทั้งหมดยังหมายความเหมือนเดิมเป๊ะ (ทุกโปรเจกต์ที่มีอยู่
ก่อนวันนี้คืองานที่มีโค้ด) — ไม่ต้องไล่เดาย้อนหลัง
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b6e2f4a81c39"
down_revision: str | None = "a1c8e5f92d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="code"),
    )


def downgrade() -> None:
    op.drop_column("projects", "kind")
