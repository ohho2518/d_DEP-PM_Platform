"""StubMetadataProvider — returns a deterministic mock Baseline Report (ADR-02, Risk #1).

Every field is clearly marked as mock so the UI can render "(mock)" and users are never
misled into thinking a real scan happened.
"""
from __future__ import annotations

from app.constants import Priority
from app.metadata.provider import MetadataProvider
from app.schemas.scan import BaselineFinding, BaselineReport


class StubMetadataProvider:
    """Implements the :class:`MetadataProvider` protocol with canned findings."""

    name = "stub"
    is_mock = True

    async def baseline_report(self, project_id: str, repo_ref: str | None) -> BaselineReport:
        findings = [
            BaselineFinding(
                category="tech_debt",
                title="[mock] ฟังก์ชันหลักไม่มี type hints",
                detail="ตัวอย่าง finding จาก StubMetadataProvider — ไม่ใช่ผลสแกนจริง",
                suggested_priority=Priority.P2,
                confidence=0.5,
            ),
            BaselineFinding(
                category="missing_tests",
                title="[mock] โมดูล core ยังไม่มี unit test",
                detail="รอ DEP Engine จริงเพื่อสแกน coverage ที่แท้จริง",
                suggested_priority=Priority.P1,
                confidence=0.5,
            ),
            BaselineFinding(
                category="doc_coverage",
                title="[mock] README ขาดส่วน Setup / Run",
                detail="ตัวอย่าง finding — placeholder จนกว่า metadata engine จะพร้อม",
                suggested_priority=Priority.P3,
                confidence=0.5,
            ),
        ]
        return BaselineReport(
            project_id=project_id,
            provider=self.name,
            is_mock=True,
            summary="(mock) Baseline Report จาก StubMetadataProvider — DEP Engine ยังไม่พร้อม (ADR-02)",
            findings=findings,
        )


# Static assertion that the stub satisfies the protocol.
_provider: MetadataProvider = StubMetadataProvider()
