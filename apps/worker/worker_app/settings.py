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


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
