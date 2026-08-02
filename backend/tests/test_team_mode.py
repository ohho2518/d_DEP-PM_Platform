"""Team Mode tests (Sprint 4) — ไม่มี key ใด ๆ ใน tests: ตรวจ mapping + fallback chain."""
from __future__ import annotations

from app.agents.runtime import FallbackExecutor, TeamExecutor, get_executor
from app.constants import AgentRole


def test_get_executor_solo_without_key_is_fallback(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "agent_mode", "solo")
    assert isinstance(get_executor(), FallbackExecutor)


def test_get_executor_team_mode_switch(monkeypatch):
    """สลับ Solo ↔ Team ด้วย config เท่านั้น — DoD Sprint 4 (orchestrator ไม่เปลี่ยน)."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "agent_mode", "team")
    assert isinstance(get_executor(), TeamExecutor)
    monkeypatch.setattr(get_settings(), "agent_mode", "solo")
    assert isinstance(get_executor(), FallbackExecutor)


def test_role_provider_mapping_matches_blueprint():
    """Blueprint §9: Codex Dev = OpenAI, Gemini SR = Google, PM/Reviewer = Claude."""
    m = TeamExecutor.ROLE_PROVIDER
    assert m[AgentRole.DEV] == "openai"
    assert m[AgentRole.SENIOR_ARCHITECT] == "google"
    assert m[AgentRole.PM] == "anthropic"
    assert m[AgentRole.REVIEWER] == "anthropic"


def test_team_executor_without_any_keys_degrades_to_fallback(db_session):
    """ไม่มี key เลย: ทุก role ต้องได้ deterministic fallback — ไม่ crash."""
    from app.models.project import Project
    from app.models.task import Task

    project = Project(name="TM", type="new")
    db_session.add(project)
    db_session.flush()
    task = Task(project_id=project.id, title="do x", depends_on=[])
    db_session.add(task)
    db_session.flush()

    executor = TeamExecutor()
    work = executor.execute(task, AgentRole.DEV)
    assert "(fallback:dev)" in work
    review = executor.review(task, work)
    assert review.approved is True


def test_team_executor_uses_provider_call_when_available(db_session, monkeypatch):
    """เสียบ provider call ปลอมเข้า _calls — role ต้องเลือก provider ตาม mapping."""
    from app.models.project import Project
    from app.models.task import Task

    project = Project(name="TM2", type="new")
    db_session.add(project)
    db_session.flush()
    task = Task(project_id=project.id, title="build api", depends_on=[])
    db_session.add(task)
    db_session.flush()

    executor = TeamExecutor()
    executor._calls["openai"] = lambda system, prompt: "openai did it"
    executor._calls["anthropic"] = lambda system, prompt: '{"approved": true, "comment": "ok"}'

    assert executor.execute(task, AgentRole.DEV) == "openai did it"
    # SR ไม่มี google call -> chain ไป anthropic
    assert executor.execute(task, AgentRole.SENIOR_ARCHITECT) == '{"approved": true, "comment": "ok"}'
    # review ใช้ anthropic + parse JSON
    review = executor.review(task, "work")
    assert review.approved is True and review.comment == "ok"


def _make_task(db_session, title="t"):
    from app.models.project import Project
    from app.models.task import Task

    project = Project(name=f"P-{title}", type="new")
    db_session.add(project)
    db_session.flush()
    task = Task(project_id=project.id, title=title, depends_on=[])
    db_session.add(task)
    db_session.flush()
    return task


def test_unparseable_review_retries_then_rejects(db_session):
    """debt #3: parse ไม่ได้ → retry 1 ครั้ง แล้ว reject (ไม่ auto-approve งานที่ไม่ถูกตรวจจริง)."""
    task = _make_task(db_session)
    calls = {"n": 0}

    def garbage(system, prompt):
        calls["n"] += 1
        return "นี่ไม่ใช่ JSON เลย"

    executor = TeamExecutor()
    executor._calls["anthropic"] = garbage
    review = executor.review(task, "work")

    assert calls["n"] == 2  # ครั้งแรก + retry
    assert review.approved is False
    assert "unparseable" in review.comment


def test_unparseable_review_recovers_on_retry(db_session):
    task = _make_task(db_session)
    replies = iter(["garbage", '{"approved": true, "comment": "fine"}'])

    executor = TeamExecutor()
    executor._calls["anthropic"] = lambda system, prompt: next(replies)
    review = executor.review(task, "work")

    assert review.approved is True and review.comment == "fine"


def test_token_usage_accumulates_on_task(db_session):
    """debt #7: ทุก execute/review call สะสม tokens_input/tokens_output ลง task."""
    from app.agents.providers import LLMReply

    task = _make_task(db_session)
    executor = TeamExecutor()
    executor._calls["openai"] = lambda system, prompt: LLMReply(
        text="work", input_tokens=100, output_tokens=40
    )
    executor._calls["anthropic"] = lambda system, prompt: LLMReply(
        text='{"approved": true, "comment": "ok"}', input_tokens=30, output_tokens=10
    )

    executor.execute(task, AgentRole.DEV)
    executor.review(task, "work")

    assert task.tokens_input == 130
    assert task.tokens_output == 50


def test_plain_string_provider_call_counts_zero_tokens(db_session):
    """Custom/legacy call ที่คืน str ล้วน — ต้องไม่พังและนับ usage เป็น 0."""
    task = _make_task(db_session)
    executor = TeamExecutor()
    executor._calls["openai"] = lambda system, prompt: "just text"

    assert executor.execute(task, AgentRole.DEV) == "just text"
    assert task.tokens_input == 0 and task.tokens_output == 0
