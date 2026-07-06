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
    max_tokens_per_task: int = 4096

    frontend_origin: str = "http://localhost:3000"

    @property
    def agent_enabled(self) -> bool:
        """True when a real Anthropic key is configured."""
        return bool(self.anthropic_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()
