"""กติกาที่ต้องมีใน persona prompt — เทสต์กันของหายตอนใครมาแก้ prompt ทีหลัง.

ทำไมต้องล็อกไว้: 2026-08-03 QC ของ d_CEO จับได้ว่า agent **กุหลักฐานขึ้นมาเอง**
(ชื่อคน + quote + timestamp + ภาพหน้าจอที่ไม่มีอยู่จริง) และ **reviewer ของเราอนุมัติผ่าน**
— คนที่จับได้คือด่านนอก ซึ่งไม่ควรเป็นด่านแรก
"""
from __future__ import annotations

import pytest

from app.agents.personas import (
    NO_FABRICATION_RULE,
    PERSONA_PROMPTS,
    REVIEWER_SYSTEM_PROMPT,
)
from app.constants import AgentRole

#: บทบาทที่ **ผลิตงาน** (reviewer ไม่ผลิต — มีเกณฑ์ "จับการกุ" ของตัวเองแทน)
PRODUCER_ROLES = [AgentRole.PM, AgentRole.DEV, AgentRole.SENIOR_ARCHITECT]


@pytest.mark.parametrize("role", PRODUCER_ROLES)
def test_every_producer_persona_carries_the_no_fabrication_rule(role):
    assert NO_FABRICATION_RULE in PERSONA_PROMPTS[role], (
        f"persona {role.value} ไม่มีกติกาห้ามกุข้อมูล — "
        "งานที่ส่งออกไปถึงผู้บริหารต้องเชื่อถือได้"
    )


@pytest.mark.parametrize(
    "kind",
    ["ชื่อคน", "เครื่องหมายคำพูด", "วันที่/เวลา", "ภาพหน้าจอ", "ตัวเลขผลวัด", "endpoint"],
)
def test_rule_names_every_kind_of_evidence_that_was_faked(kind):
    """ระบุประเภทให้ครบตามที่เคยเจอจริง — เขียนลอย ๆ ว่า "ห้ามโกหก" ไม่พอ."""
    assert kind in NO_FABRICATION_RULE


def test_rule_gives_a_way_out_instead_of_only_forbidding():
    """ต้องบอกด้วยว่าไม่มีข้อมูลแล้วให้ทำอะไร ไม่งั้น agent จะแต่งเพื่อให้งานดูครบ."""
    assert "ต้องการข้อมูลจากคน" in NO_FABRICATION_RULE
    assert "[ตัวอย่างสมมติ]" in NO_FABRICATION_RULE  # ยกตัวอย่างได้ถ้าติดป้าย


def test_reviewer_must_reject_fabricated_evidence():
    assert "[ตัวอย่างสมมติ]" in REVIEWER_SYSTEM_PROMPT
    assert "reject" in REVIEWER_SYSTEM_PROMPT
    # ต้องบอกลำดับความสำคัญ ไม่งั้น reviewer จะปล่อยผ่านเพราะ "เนื้อหาครบตาม spec"
    assert "สำคัญกว่าความครบของเนื้อหา" in REVIEWER_SYSTEM_PROMPT


def test_pm_prompt_still_ends_with_the_json_only_instruction():
    """กติกาถูกแทรก **ก่อน** บล็อกรูปแบบผลลัพธ์ — คำสั่ง JSON ต้องยังเป็นสิ่งสุดท้ายที่โมเดลอ่าน."""
    tail = PERSONA_PROMPTS[AgentRole.PM].rstrip()[-200:]
    assert "depends_on" in tail and "ref" in tail
