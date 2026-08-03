"""Client คุยกับ d_CEO (Solo_CEO API) — DEP-PM เป็นฝั่ง **consumer**.

สายบังคับบัญชา: Vinit → d_Jarvis → d_CEO → delegate → **DEP-PM (Team Lead R&D)**
รายละเอียด + กติกาใน `AGENTS.md` §3.1 · contract ใน `docs/INTEGRATION_CEO.md`

หลักการของไฟล์นี้ (เดียวกับ `services/deploy.py`)
- **ไฟล์เดียวคุมผิวสัมผัสทั้งหมด** — ที่อื่นห้ามยิง HTTP ไป d_CEO เอง (แบบเดียวกับ
  `jarvis/ceo_client.py` ฝั่ง Jarvis) เพื่อให้ contract drift เห็นได้จากจุดเดียว
- **d_CEO ปิดอยู่ต้อง degrade ไม่ล้ม** — error ทางเครือข่ายถูกแปลงเป็น `CeoUnavailable`
  ให้ caller ตัดสินใจ (endpoint → 503, เส้นทางอัตโนมัติ → ข้ามเงียบ)
- **ห้ามส่ง `done`/`awaiting_approval`** — มติ Vinit 2026-08-02 (เคส d_MOS): ระบบข้างเคียง
  ปิดงานฝั่ง d_CEO เองไม่ได้ ทุกงานต้องผ่าน QC gate → ส่งได้แค่ `in_progress` / `qc_review`
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings

# คำศัพท์สถานะของ **d_CEO** (คนละชุดกับ TaskStatus ของเรา — อย่าปนกัน)
CEO_STATUS_IN_PROGRESS = "in_progress"  # รับงานแล้ว กำลังทำ
CEO_STATUS_QC_REVIEW = "qc_review"  # ส่งผลงานเข้า QC gate

# สถานะที่ DEP-PM ได้รับอนุญาตให้ส่งกลับ (กฎเหล็ก "ปิดงานเองไม่ได้ ต้องผ่าน QC gate")
ALLOWED_OUTBOUND_STATUSES = frozenset({CEO_STATUS_IN_PROGRESS, CEO_STATUS_QC_REVIEW})


class CeoUnavailable(RuntimeError):
    """เรียก d_CEO ไม่สำเร็จ (ปิดอยู่ / network / ตอบ error) — ไม่ใช่ bug ของเรา."""


@dataclass(frozen=True)
class CeoTask:
    """งานใน d_CEO เท่าที่ DEP-PM ใช้ (shape ตาม `GET /tasks` ของ provider)."""

    id: str
    input_text: str
    assigned_team_id: str | None
    status: str
    output: str | None
    created_at: str  # ISO 8601 **UTC** — แปลงเป็น Asia/Bangkok ตอนแสดงผลเท่านั้น

    @classmethod
    def from_payload(cls, raw: dict[str, Any]) -> CeoTask:
        return cls(
            id=str(raw.get("id", "")),
            input_text=raw.get("input_text") or "",
            assigned_team_id=(str(raw["assigned_team_id"]) if raw.get("assigned_team_id") else None),
            status=raw.get("status") or "",
            output=raw.get("output"),
            created_at=raw.get("created_at") or "",
        )


class CeoClient:
    """Sync client (โค้ดฝั่งเราเป็น sync ทั้งหมด — ไม่แตะ async เพื่อความสม่ำเสมอ)."""

    def __init__(self, base_url: str, *, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- ชั้นล่างสุด --------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.request(method, url, timeout=self.timeout, **kwargs)
        except httpx.HTTPError as exc:
            raise CeoUnavailable(f"เชื่อมต่อ d_CEO ไม่ได้ ({url}): {exc}") from exc
        if response.status_code >= 400:
            raise CeoUnavailable(
                f"d_CEO ตอบ {response.status_code} ที่ {path}: {response.text[:200]}"
            )
        if not response.content:
            return None
        return response.json()

    # --- endpoints ที่เราพึ่งพา ---------------------------------------------
    def health(self) -> bool:
        """True = สมองออนไลน์. ไม่ raise — ใช้ตัดสินใจแสดงผลอย่างเดียว."""
        try:
            payload = self._request("GET", "/health")
        except CeoUnavailable:
            return False
        return bool(payload) and payload.get("status") == "ok"

    def list_teams(self) -> list[dict[str, Any]]:
        return list(self._request("GET", "/teams") or [])

    def resolve_team_id(self, name: str) -> str | None:
        """หา team id จากชื่อ — teams เป็น data ใน d_CEO ห้าม hardcode id ฝั่งเรา."""
        wanted = name.strip().casefold()
        for team in self.list_teams():
            if str(team.get("name", "")).strip().casefold() == wanted:
                return str(team.get("id"))
        return None

    def list_tasks(self, *, status: str = "queued", limit: int = 50) -> list[CeoTask]:
        payload = self._request("GET", "/tasks", params={"status": status, "limit": limit})
        return [CeoTask.from_payload(row) for row in (payload or [])]

    def patch_task(
        self, task_id: str, *, status: str | None = None, output: str | None = None
    ) -> CeoTask:
        """เลื่อนสถานะ/เขียนผลงานกลับ d_CEO.

        ValueError เมื่อพยายามส่งสถานะนอก `ALLOWED_OUTBOUND_STATUSES` — เป็น guardrail
        ของกฎ "ปิดงานเองไม่ได้ ต้องผ่าน QC gate" ไม่ใช่ข้อจำกัดของ provider
        """
        if status is not None and status not in ALLOWED_OUTBOUND_STATUSES:
            raise ValueError(
                f"DEP-PM ส่งสถานะ '{status}' กลับ d_CEO ไม่ได้ — "
                f"อนุญาตเฉพาะ {sorted(ALLOWED_OUTBOUND_STATUSES)} (ต้องผ่าน QC gate)"
            )
        body: dict[str, Any] = {}
        if status is not None:
            body["status"] = status
        if output is not None:
            body["output"] = output
        if not body:
            raise ValueError("patch_task ต้องมีอย่างน้อย status หรือ output")
        return CeoTask.from_payload(self._request("PATCH", f"/tasks/{task_id}", json=body) or {})

    def qc_task(self, task_id: str) -> CeoTask:
        """สั่งให้ QC ของ d_CEO ตรวจงานนี้ (`POST /tasks/{id}/qc`) — **ปุ่มฉุกเฉิน**.

        ปกติ**ไม่ต้องเรียก**: ตั้งแต่ contract v6 ของ d_CEO (2026-08-03) การ PATCH ที่เลื่อน
        สถานะ**เข้า** `qc_review` พร้อมมี `output` จะถูกส่งเข้า QC ต่อให้อัตโนมัติ —
        `patch_task` ของเราส่ง `status` + `output` ไปพร้อมกันใน request เดียวอยู่แล้ว

        ใช้เมื่อ QC ฝั่งเขาล่มตอนนั้นแล้วงานค้าง `qc_review` เท่านั้น
        ⚠️ **หนึ่งรอบ QC มีราคา** (~ครึ่งหนึ่งของค่างานหนึ่งชิ้น) — อย่ายิงซ้ำโดยไม่จำเป็น
        """
        return CeoTask.from_payload(self._request("POST", f"/tasks/{task_id}/qc") or {})


def get_ceo_client() -> CeoClient | None:
    """FastAPI dependency — คืน None เมื่อยังไม่ตั้งค่า (endpoint แปลงเป็น 503).

    tests override dependency นี้ด้วย stub (ไม่ mock HTTP — กติกาใน AI_AGENT_GUIDE)
    """
    settings = get_settings()
    if not settings.ceo_enabled:
        return None
    return CeoClient(settings.ceo_api_base, timeout=settings.ceo_timeout_seconds)
