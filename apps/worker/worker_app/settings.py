from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / '.env', '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')
    smtp_connect_timeout_seconds: int = Field(default=10, alias='SMTP_CONNECT_TIMEOUT_SECONDS')
    smtp_max_send_attempts: int = Field(default=5, alias='SMTP_MAX_SEND_ATTEMPTS')


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
