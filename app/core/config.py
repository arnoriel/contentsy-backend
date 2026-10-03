from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Contentsy API"

    database_url: str
    redis_url: str

    openrouter_api_key: str = ""
    openrouter_model: str = ""

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=1440, gt=0)

    upload_dir: str = "storage/uploads"
    max_upload_size_mb: int = Field(default=500, gt=0)

    signup_credits: int = Field(default=10, ge=0)

    cors_origins: str = "http://localhost:3000"

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
