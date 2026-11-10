from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://reviewapp:reviewapp@localhost:5432/reviewapp"
    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
