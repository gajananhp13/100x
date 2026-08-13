from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_name: str = "100x Resume"
    debug: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    github_token: str | None = None
    report_storage_dir: str = "data/reports"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    document_parse_timeout_seconds: float = 30.0
    github_rate_warning_at: int = 20


settings = Settings()