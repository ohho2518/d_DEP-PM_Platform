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
from app.agents.runtime import _parse_review
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


def test_rule_forbids_claiming_actions_the_agent_cannot_perform():
    """กุ "การกระทำ" ก็คือกุหลักฐาน — รอบ 3 agent เขียนว่า "escalate ไปแล้ว" ทั้งที่ทำไม่ได้."""
    assert "escalate" in NO_FABRICATION_RULE
    assert "ห้ามอ้างว่าได้ลงมือทำสิ่งที่คุณทำไม่ได้" in NO_FABRICATION_RULE


# ---------------------------------------------------------------------------
# งานที่ติดเพราะต้องให้คนป้อนข้อมูล — reviewer ต้องส่งต่อให้คน ไม่ approve และไม่วน revision
# (UAT รอบ 3 2026-08-03: task เดียวกันสองตัว ตัวหนึ่งถูก approve ทั้งที่ไม่มีเนื้อหา
#  อีกตัวถูกตีกลับ 2 รอบด้วยคำสั่งที่ agent ทำตามไม่ได้ → escalate · QC ปลายทางจับได้ทั้งคู่)
# ---------------------------------------------------------------------------
def test_reviewer_has_a_needs_human_verdict_for_work_blocked_on_a_person():
    assert "needs_human" in REVIEWER_SYSTEM_PROMPT
    assert "ต้องการข้อมูลจากคน" in REVIEWER_SYSTEM_PROMPT
    # ห้ามปล่อยผ่านเป็น "เสร็จ" — รายงานถึง d_CEO จะนับเป็นงานที่ทำเสร็จทั้งที่ไม่มีชิ้นงาน
    assert "ห้าม approve งานแบบนี้ว่าเสร็จ" in REVIEWER_SYSTEM_PROMPT


def test_reviewer_must_not_ask_for_things_the_agent_cannot_do():
    """คำสั่งแบบ "ยืนยันว่าส่งเรื่องไปแล้ว" คือการบีบให้ agent กุการกระทำ."""
    assert "ห้ามสั่ง revision ที่ agent ทำไม่ได้ในบทสนทนานี้" in REVIEWER_SYSTEM_PROMPT


def test_parser_understands_the_verdict_the_prompt_promises():
    """prompt สัญญาว่ามีฟิลด์ `needs_human` — parser ต้องอ่านได้จริง ไม่งั้นกติกาไม่มีผล."""
    parsed = _parse_review('{"approved": false, "needs_human": true, "comment": "ขอไฟล์ก่อน"}')
    assert parsed is not None and parsed.needs_human is True and parsed.approved is False
    # ของเดิมที่ไม่มีฟิลด์นี้ต้องยังทำงานเหมือนเดิม (revision loop ปกติ)
    legacy = _parse_review('{"approved": false, "comment": "แก้ตรงนี้"}')
    assert legacy is not None and legacy.needs_human is False


def test_reviewer_sees_the_same_source_material_as_the_worker(db_session):
    """reviewer ต้องได้ `description` ด้วย ไม่ใช่แค่ title+spec.

    เจอจริง 2026-08-14: reviewer ปฏิเสธงานที่ถูกต้อง 2 รอบติดด้วยเหตุผลว่า "ไม่มี description
    ต้นฉบับให้เทียบ จึงยืนยันไม่ได้ว่าไม่ได้กุ" — กติกาห้ามกุหลักฐานทำให้ช่องโหว่นี้กลายเป็น
    ค่าใช้จ่ายจริงทุกรอบ (อาการเดียวกับบั๊ก upstream context ของ Phase 3a)
    """
    from app.agents.runtime import _review_prompt
    from app.models.project import Project
    from app.models.task import Task

    project = Project(name="RP", type="new")
    db_session.add(project)
    db_session.flush()
    task = Task(
        project_id=project.id,
        title="เขียนสรุป",
        description="ข้อมูลต้นฉบับที่คนทำงานได้รับ",
        spec="สรุปจาก description เท่านั้น",
        depends_on=[],
    )

    prompt = _review_prompt(task, "ผลงาน")

    assert "ข้อมูลต้นฉบับที่คนทำงานได้รับ" in prompt
    assert "สรุปจาก description เท่านั้น" in prompt


def test_pm_prompt_still_ends_with_the_json_only_instruction():
    """กติกาถูกแทรก **ก่อน** บล็อกรูปแบบผลลัพธ์ — คำสั่ง JSON ต้องยังเป็นสิ่งสุดท้ายที่โมเดลอ่าน."""
    tail = PERSONA_PROMPTS[AgentRole.PM].rstrip()[-200:]
    assert "depends_on" in tail and "ref" in tail
