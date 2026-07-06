"""Application settings loaded from environment / .env (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

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
    # 'solo'  = Claude ทุกบทบาท (default) | 'team' = map role -> provider
    agent_mode: str = "solo"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-pro"

    # --- Deploy pipeline (Sprint 4, Blueprint §12) --------------------------
    # ครบทั้งคู่ => dispatch repository_dispatch จริง; ไม่ครบ => stub (บันทึก record อย่างเดียว)
    github_token: str = ""
    github_repo: str = ""  # รูปแบบ "owner/repo"
    # task เข้า done ระหว่าง orchestrator run => สร้าง deployment ไป staging อัตโนมัติ
    auto_deploy_enabled: bool = False

    frontend_origin: str = "http://localhost:3000"

    @property
    def agent_enabled(self) -> bool:
        """True when a real Anthropic key is configured."""
        return bool(self.anthropic_api_key.strip())

    @property
    def deploy_dispatch_enabled(self) -> bool:
        """True เมื่อ config GitHub ครบพอจะยิง repository_dispatch จริง."""
        return bool(self.github_token.strip()) and bool(self.github_repo.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
