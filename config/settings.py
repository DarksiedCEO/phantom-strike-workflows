from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    temporal_server_url: str = Field(default="localhost:7233", alias="TEMPORAL_SERVER_URL")
    temporal_namespace: str = Field(default="default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field(
        default="phantom-strike-signal-validation",
        alias="TEMPORAL_TASK_QUEUE",
    )
    core_base_url: str = Field(..., alias="CORE_BASE_URL")
    contracts_schema_dir: str = Field(
        default="/Users/andrelove/IdeaProjects/phantom-strike-contracts/schemas/v1",
        alias="CONTRACTS_SCHEMA_DIR",
    )
    contracts_commit: str = Field(default="3110d87", alias="CONTRACTS_COMMIT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    smoke_timeout_seconds: int = Field(default=60, alias="SMOKE_TIMEOUT_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
