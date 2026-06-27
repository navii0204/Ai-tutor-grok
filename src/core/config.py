"""Central configuration — all settings loaded from env / .env file.

Scalability note: For multi-tenant SaaS, extend TenantSettings per-school
and load from a config-service or database rather than environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    provider: Literal["ollama", "llamacpp", "openai_compat", "claude", "mock"] = "ollama"
    api_key: str = ""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    timeout: int = 60
    max_tokens: int = 1024
    temperature: float = 0.7


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./brainecosystem.db"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    url: str | None = None
    ttl_seconds: int = 3600


class FeatureFlags(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FEATURE_", extra="ignore")

    simulator: bool = True
    vision: bool = False
    parent_reports: bool = True
    spaced_repetition: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "insecure-dev-key-change-in-production"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Tenant
    default_tenant_id: str = "demo-school-001"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    # Vision
    vision_enabled: bool = False
    vision_model: str = "llava:7b"

    # Sub-settings (loaded via their own env prefix)
    @property
    def llm(self) -> LLMSettings:
        return LLMSettings()

    @property
    def db(self) -> DatabaseSettings:
        return DatabaseSettings()

    @property
    def redis(self) -> RedisSettings:
        return RedisSettings()

    @property
    def features(self) -> FeatureFlags:
        return FeatureFlags()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
