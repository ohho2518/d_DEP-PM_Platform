"""เพดานค่าใช้จ่ายต่อโปรเจกต์ (§5 ใบสั่งงาน 2026-08-06).

สิ่งที่ต้องจริงเสมอ:

* ตัวเลขเงินเป็น **ประมาณการ** จากราคาที่ตั้งไว้ ไม่ใช่บิลจริง ⇒ เทสต์ตรึง "สูตร" ไม่ใช่ราคา
  (ราคาปริยายเปลี่ยนได้ตลอด — เทสต์ที่ผูกกับราคาจะพังโดยไม่มีอะไรเสียจริง)
* เกินเพดานแล้ว `stop` = **ไม่เริ่ม task ใหม่** ไม่ใช่ตัดกลาง task ที่จ่ายค่าโทเคนไปแล้ว
* `warn` = เตือนอย่างเดียว งานต้องเดินต่อจนจบ (ค่าปริยาย — ห้ามเปลี่ยนพฤติกรรมเดิมของใคร)
"""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.constants import TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.orchestrator.engine import run_project
from app.services import usage


@pytest.fixture()
def priced(monkeypatch):
    """ราคาที่คำนวณในหัวได้: input $2/ล้าน · output $10/ล้าน."""
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_price_anthropic_in", 2.0)
    monkeypatch.setattr(settings, "llm_price_anthropic_out", 10.0)
    return settings


def _project_with_spend(db, *, input_tokens: int, output_tokens: int, planned: int = 2) -> Project:
    project = Project(name="เพดาน", type="new")
    db.add(project)
    db.flush()
    db.add(
        Task(
            project_id=project.id,
            title="งานที่ทำไปแล้ว",
            status=TaskStatus.DONE.value,
            depends_on=[],
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            token_usage={
                "anthropic": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "calls": 1,
                    "model": "claude-sonnet-5",
                }
            },
        )
    )
    for i in range(planned):
        db.add(
            Task(
                project_id=project.id,
                title=f"งานที่ยังไม่ทำ {i + 1}",
                status=TaskStatus.PLANNED.value,
                depends_on=[],
            )
        )
    db.commit()
    db.refresh(project)
    return project


# --- สูตรคิดเงิน --------------------------------------------------------------


def test_cost_counts_input_and_output_at_different_rates(priced):
    # 1,000,000 input = $2 · 1,000,000 output = $10 (ตาม fixture)
    assert usage.estimate_cost("anthropic", 1_000_000, 0) == pytest.approx(2.0)
    assert usage.estimate_cost("anthropic", 0, 1_000_000) == pytest.approx(10.0)
    assert usage.estimate_cost("anthropic", 500_000, 100_000) == pytest.approx(2.0)


def test_unknown_provider_costs_zero_instead_of_crashing(priced):
    """เจ้าที่ยังไม่มีราคาต้องคืน 0 — ระบบต้องไม่ล้มเพราะยังไม่ได้กรอกตารางราคา."""
    assert usage.estimate_cost("ยังไม่รู้จัก", 1_000_000, 1_000_000) == 0.0


def test_usage_endpoint_reports_estimate_and_limit(client, db_session, priced, monkeypatch):
    monkeypatch.setattr(priced, "llm_budget_usd", 5.0)
    project = _project_with_spend(db_session, input_tokens=1_000_000, output_tokens=100_000)

    body = client.get(f"/api/projects/{project.id}/usage").json()

    assert body["by_provider"][0]["cost_usd"] == pytest.approx(3.0)  # $2 + $1
    assert body["budget"]["spent_usd"] == pytest.approx(3.0)
    assert body["budget"]["limit_usd"] == pytest.approx(5.0)
    assert body["budget"]["over"] is False


def test_untracked_tokens_are_flagged_as_missing_from_the_estimate(client, db_session, priced):
    """งานเก่าที่ระบุเจ้าไม่ได้ไม่ถูกคิดเงิน — ต้องบอกไว้ ไม่ใช่ปล่อยให้อ่านว่า "ใช้น้อย"."""
    project = Project(name="ของเก่า", type="new")
    db_session.add(project)
    db_session.flush()
    db_session.add(
        Task(project_id=project.id, title="เก่า", depends_on=[], tokens_input=900, tokens_output=300)
    )
    db_session.commit()

    budget = client.get(f"/api/projects/{project.id}/usage").json()["budget"]
    assert budget["spent_usd"] == 0.0
    assert budget["excludes_untracked"] is True


# --- ผลต่อรอบรัน --------------------------------------------------------------


def test_no_budget_means_no_limit(db_session, priced):
    """ค่าปริยาย (0 = ไม่จำกัด) ต้องไม่เปลี่ยนพฤติกรรมเดิมแม้ใช้ไปเยอะแค่ไหน."""
    project = _project_with_spend(db_session, input_tokens=9_000_000, output_tokens=9_000_000)
    assert usage.over_budget(db_session, project.id) is None


def test_over_budget_with_stop_halts_before_the_next_task(db_session, priced, monkeypatch):
    monkeypatch.setattr(priced, "llm_budget_usd", 1.0)
    monkeypatch.setattr(priced, "llm_budget_action", "stop")
    project = _project_with_spend(db_session, input_tokens=1_000_000, output_tokens=0)  # = $2

    summary = run_project(db_session, project.id)

    assert summary.outcomes == []  # ไม่หยิบ task ใหม่เลย
    assert summary.stopped_reason is not None
    assert "เพดาน" in summary.stopped_reason
    # งานที่เหลือยังรออยู่ กด Run ใหม่ทำต่อได้ทันทีที่ขยับเพดาน
    remaining = [t for t in db_session.query(Task).all() if t.status == TaskStatus.PLANNED.value]
    assert len(remaining) == 2


def test_over_budget_with_warn_keeps_working(db_session, priced, monkeypatch):
    monkeypatch.setattr(priced, "llm_budget_usd", 1.0)
    monkeypatch.setattr(priced, "llm_budget_action", "warn")
    project = _project_with_spend(db_session, input_tokens=1_000_000, output_tokens=0)

    summary = run_project(db_session, project.id)

    assert len(summary.outcomes) == 2  # เตือนแล้วยังทำงานต่อ
    assert summary.stopped_reason is None


def test_run_api_shows_why_it_stopped(client, db_session, priced, monkeypatch, wait_run):
    """หน้าบอร์ดต้องแยกออกว่า "หยุดเพราะงบ" ไม่ใช่ "ล้มเหลว" — คนละช่องกับ error."""
    monkeypatch.setattr(priced, "llm_budget_usd", 1.0)
    monkeypatch.setattr(priced, "llm_budget_action", "stop")
    project = _project_with_spend(db_session, input_tokens=1_000_000, output_tokens=0)

    run_id = client.post(f"/api/projects/{project.id}/run").json()["run_id"]
    wait_run(run_id)

    body = client.get(f"/api/projects/{project.id}/run").json()
    assert body["status"] == "succeeded"  # ไม่ใช่ความล้มเหลว
    assert body["error"] is None
    assert "เพดาน" in body["stopped_reason"]
    assert body["processed"] == 0


# --- ตั้งเพดานจากหน้า Settings -------------------------------------------------


@pytest.fixture()
def env_at(tmp_path, monkeypatch):
    """`.env` ปลอม — ห้ามให้เทสต์แตะไฟล์จริงหรือถล่มโฟลเดอร์ BackUp ของเครื่อง."""
    from app.services import env_file

    path = tmp_path / ".env"
    path.write_text("LLM_BUDGET_USD=0\nLLM_BUDGET_ACTION=warn\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(env_file, "env_path", lambda: path)
    monkeypatch.setattr(env_file, "backup_env", lambda p: None)
    return path


def test_settings_page_can_change_the_cap_without_restart(client, env_at):
    resp = client.put("/api/settings/llm", json={"budget_usd": 12.5, "budget_action": "stop"})

    assert resp.status_code == 200
    assert resp.json()["budget_usd"] == 12.5
    assert resp.json()["budget_action"] == "stop"
    # มีผลทันทีในหน่วยความจำ **และเป็นตัวเลข** (ค่าใน .env เป็นข้อความ ถ้าไม่แปลงจะพังตอนเทียบ)
    assert get_settings().llm_budget_usd == 12.5
    assert "LLM_BUDGET_USD=12.5" in env_at.read_text(encoding="utf-8")


def test_settings_page_rejects_unknown_budget_action(client, env_at):
    resp = client.put("/api/settings/llm", json={"budget_action": "ระเบิดทิ้ง"})
    assert resp.status_code == 400
    assert get_settings().llm_budget_action == "warn"  # ของเดิมไม่ถูกแตะ


def test_settings_page_rejects_negative_cap(client):
    assert client.put("/api/settings/llm", json={"budget_usd": -1}).status_code == 422
