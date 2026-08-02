"""Clients ของระบบข้างเคียงใน ecosystem dPRO (consumer side).

ชั้นนี้เป็น infrastructure เหมือน `db/` — `services/` เรียกได้, `models/` ห้ามเรียก
"""
from app.integrations.ceo_client import CeoClient, CeoTask, CeoUnavailable, get_ceo_client

__all__ = ["CeoClient", "CeoTask", "CeoUnavailable", "get_ceo_client"]
