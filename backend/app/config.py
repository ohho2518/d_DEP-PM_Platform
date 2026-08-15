"""Application settings loaded from environment / .env (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. See .env.example for the meaning of each variable."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./dep_pm.db"

    # PM Agent (Solo Mode). Empty key => live agent calls disabled (ADR gracefully degrades).
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"
    max_tokens_per_task: int = 16000

    # --- Team Mode (Sprint 4, Blueprint §8-9) -------------------------------
    # 'solo'  = ผู้ให้บริการเดียวทุกบทบาท (default) | 'team' = map role -> provider
    agent_mode: str = "solo"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    gemini_api_key: str = ""
    # ⚠️ ค่าเดิม "gemini-3-pro" **ไม่มีอยู่จริง** บน API v1beta → 404 ทุกครั้ง (เจอ 2026-08-14)
    # ตัวนี้ยิงผ่านจริงแล้ว · ชื่อรุ่นฝั่ง Google เปลี่ยนบ่อย — ตรวจด้วยปุ่มทดสอบที่หน้า /settings
    gemini_model: str = "gemini-3-flash-preview"

    # --- รองรับ AI หลายเจ้า (ใบสั่งงาน 2026-08-06) --------------------------
    # ตอบคนละคำถามกับ `agent_mode`: agent_mode = "บทบาทไหนใช้เจ้าไหนเป็นตัวหลัก",
    # ส่วนสองตัวนี้ = "ตัวหลักคือใคร และล้มแล้วไปต่อที่ใคร" (ใช้ร่วมกันทั้ง solo/team)
    llm_provider: str = "anthropic"
    llm_fallbacks: str = ""  # คั่นด้วย comma เช่น "openai,google" · ว่าง = ไม่มีสำรอง (พฤติกรรมเดิม)
    # เพดานเวลาต่อการเรียกโมเดลหนึ่งครั้ง — **ต้องตั้งเอง** เพราะค่าปริยายของ SDK คือ 600 วินาที
    # ⚠️ เจอจริง 2026-08-14: prompt ที่ได้จาก PDF ทำให้ `/breakdown` ค้างครบ 10 นาที
    # ถ้าไม่มีเพดานนี้ การ "ลองซ้ำ + ไล่เจ้าสำรอง" จะกลายเป็นครึ่งชั่วโมงต่อหนึ่ง task
    llm_timeout_seconds: float = 120.0

    # --- เพดานค่าใช้จ่าย (§5 ใบสั่งงาน 2026-08-06) ---------------------------
    # ราคาต่อ **1 ล้านโทเคน** (USD) · ค่าตั้งต้นมาจากหน้าประกาศราคาของแต่ละเจ้า ณ 2026-08-14
    # ⚠️ **ยังไม่ได้ยืนยันกับบิลจริงของบัญชีนี้** — ราคาเปลี่ยนบ่อยและแต่ละบัญชีมีเงื่อนไขต่างกัน
    # ⇒ ระบบรายงานตัวเลขพร้อมป้ายว่า "ประมาณการ" เสมอ ห้ามเอาไปอ้างเป็นค่าใช้จ่ายจริง
    llm_price_anthropic_in: float = 3.0
    llm_price_anthropic_out: float = 15.0
    llm_price_openai_in: float = 1.25
    llm_price_openai_out: float = 10.0
    llm_price_google_in: float = 0.30
    llm_price_google_out: float = 2.50
    #: เพดานต่อโปรเจกต์ (USD) · 0 = ไม่จำกัด (ค่าปริยาย — ไม่เปลี่ยนพฤติกรรมเดิม)
    llm_budget_usd: float = 0.0
    #: เกินเพดานแล้วทำอะไร — `warn` = เตือนอย่างเดียว (ปริยาย) · `stop` = ไม่เริ่ม task ใหม่
    llm_budget_action: str = "warn"

    # --- Deploy pipeline (Sprint 4, Blueprint §12) --------------------------
    # ครบทั้งคู่ => dispatch repository_dispatch จริง; ไม่ครบ => stub (บันทึก record อย่างเดียว)
    github_token: str = ""
    github_repo: str = ""  # รูปแบบ "owner/repo"
    # task เข้า done ระหว่าง orchestrator run => สร้าง deployment ไป staging อัตโนมัติ
    auto_deploy_enabled: bool = False
    # shared secret ที่ CI ต้องแนบมากับ callback `PATCH /api/deployments/:id`
    # ว่าง = ไม่ตรวจ (โหมด dev บน localhost) — **ต้องตั้งก่อนเปิดพอร์ตออกนอกเครื่อง** (Risk #1)
    deploy_callback_secret: str = ""

    # --- d_CEO integration (Phase 1) ----------------------------------------
    # DEP-PM = Team Lead R&D ปลายสาย Vinit -> Jarvis -> d_CEO -> ที่นี่ (AGENTS.md §3.1)
    # ว่าง = ปิดการเชื่อมต่อ (endpoint /api/ceo/* จะตอบ 503)
    ceo_api_base: str = "http://127.0.0.1:8000"
    # ชื่อทีมใน d_CEO ที่งานของเราถูก assign มา — resolve เป็น id ตอน runtime ผ่าน GET /teams
    # (teams เป็น data ไม่ใช่ค่าตายตัว — ห้าม hardcode id)
    ceo_team_name: str = "Research & Development"
    ceo_timeout_seconds: float = 15.0

    # --- เปิดโปรเจกต์ใหม่จริง (ADR-05 — ยก scaffold มาจาก new-project-studio) --------
    # รากที่อนุญาตให้สร้างโฟลเดอร์ได้ · target นอกรากนี้ถูกปฏิเสธ (กัน scaffold ลงที่มั่ว)
    scaffold_allowed_root: str = r"D:\Dev_Proj"
    # ว่าง = ใช้แม่แบบที่มากับรีโปนี้ (`backend/app/scaffold_kit/`) — เจ้าของแม่แบบคือที่นี่แล้ว
    scaffold_kit_path: str = ""

    # --- ไอเดียที่ยังไม่ได้ลงมือ (2026-08-15) --------------------------------
    # โฟลเดอร์ที่ไปตามหาไอเดียเก่ามาขึ้นบอร์ด **คั่นด้วย `;`** (path ของ Windows มี `,` ได้)
    # ของจริงบนเครื่องนี้กระจายอยู่ 2 ที่มาก่อนจะมีระบบ — ดึงเข้ามาทั้งคู่ (มติผู้ใช้ 2026-08-15)
    idea_roots: str = r"D:\Dev_Proj\IDEAs;D:\Dev_Proj\6_KM\Ideas"

    # --- ประตูหน้าบ้าน (2026-08-14) ------------------------------------------
    # ว่าง = ไม่ตรวจ (dev บน localhost — พฤติกรรมเดิม) · ตั้งค่า = ทุก `/api/*` ต้องแนบ
    # header `X-DEP-PM-Token` · **ต้องตั้งก่อนเปิดพอร์ตออกนอกเครื่อง** เพราะหน้า /settings
    # แก้คีย์ผู้ให้บริการ AI ได้ (docs/SECURITY.md — Risk 5.2)
    api_token: str = ""

    @field_validator("api_token")
    @classmethod
    def _token_must_be_ascii(cls, value: str) -> str:
        """ต้องเป็น ASCII — **HTTP header ส่งอักษรไทยไม่ได้เลย**.

        ไม่ใช่เรื่องความปลอดภัยแต่เป็นเรื่องส่งไม่ออก: client encode header เป็น ASCII
        แล้วโยน `UnicodeEncodeError` ตั้งแต่ต้นทาง ⇒ ตั้ง token ไทยไว้ = ล็อกตัวเองออกจาก API
        โดยไม่มีใครยิงเข้ามาได้เลยแม้แต่คนที่ถือ token · fail-fast ตอนสตาร์ตดีกว่าไปงงตอนใช้
        (คนละเรื่องกับ callback secret เมื่อ 3 ส.ค. ที่ปัญหาอยู่ **ฝั่งเทียบค่า** ไม่ใช่ฝั่งส่ง)
        """
        if value and not value.isascii():
            raise ValueError(
                "API_TOKEN ต้องเป็นตัวอักษร ASCII เท่านั้น (HTTP header ส่งภาษาไทยไม่ได้) — "
                "ใช้ตัวสุ่มยาว ๆ เช่นผลจาก `python -c \"import secrets;print(secrets.token_urlsafe(32))\"`"
            )
        return value

    frontend_origin: str = "http://localhost:3000"

    @property
    def provider_keys(self) -> dict[str, str]:
        """ชื่อผู้ให้บริการ -> คีย์ (ค่าว่าง = ยังไม่ตั้ง).

        อยู่ที่นี่เพราะ `providers.py` กับหน้า Settings ต้องใช้ตารางเดียวกัน —
        ชื่อ key ต้องตรงกับ `providers.BUILDERS`
        """
        return {
            "anthropic": self.anthropic_api_key.strip(),
            "openai": self.openai_api_key.strip(),
            "google": self.gemini_api_key.strip(),
        }

    @property
    def provider_models(self) -> dict[str, str]:
        """ชื่อผู้ให้บริการ -> รุ่นที่ตั้งไว้ (คู่กับ `provider_keys`)."""
        return {
            "anthropic": self.claude_model,
            "openai": self.openai_model,
            "google": self.gemini_model,
        }

    @property
    def provider_prices(self) -> dict[str, tuple[float, float]]:
        """ชื่อผู้ให้บริการ -> (ราคา input, ราคา output) ต่อ 1 ล้านโทเคน — **ประมาณการ**."""
        return {
            "anthropic": (self.llm_price_anthropic_in, self.llm_price_anthropic_out),
            "openai": (self.llm_price_openai_in, self.llm_price_openai_out),
            "google": (self.llm_price_google_in, self.llm_price_google_out),
        }

    @property
    def llm_fallback_list(self) -> list[str]:
        """ลำดับสำรองที่ล้างค่าแล้ว — ตัวว่างถูกตัดทิ้ง, ตัวที่ไม่รู้จักปล่อยให้ chain ข้ามเอง."""
        return [name.strip().lower() for name in self.llm_fallbacks.split(",") if name.strip()]

    @property
    def agent_enabled(self) -> bool:
        """True เมื่อมีคีย์ของผู้ให้บริการ **อย่างน้อยหนึ่งเจ้า**.

        เดิมผูกกับ Anthropic ตัวเดียว — ตั้ง `LLM_PROVIDER=openai` แล้วระบบจะยังคิดว่า
        ไม่มี agent (ใบสั่งงาน 2026-08-06: โค้ดธุรกิจห้ามผูกกับชื่อเจ้าใดเจ้าหนึ่ง)
        """
        return any(self.provider_keys.values())

    @property
    def ceo_enabled(self) -> bool:
        """True เมื่อ config ครบพอจะคุยกับ d_CEO ได้."""
        return bool(self.ceo_api_base.strip())

    @property
    def deploy_dispatch_enabled(self) -> bool:
        """True เมื่อ config GitHub ครบพอจะยิง repository_dispatch จริง."""
        return bool(self.github_token.strip()) and bool(self.github_repo.strip())

    @property
    def api_auth_enabled(self) -> bool:
        """True เมื่อตั้งประตูหน้าบ้านแล้ว — `/health` บอกออกไปได้ (ไม่ใช่ความลับ)."""
        return bool(self.api_token.strip())

    @property
    def callback_auth_enabled(self) -> bool:
        """True เมื่อตั้ง shared secret ให้ callback ของ CI แล้ว (Risk #1)."""
        return bool(self.deploy_callback_secret.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
