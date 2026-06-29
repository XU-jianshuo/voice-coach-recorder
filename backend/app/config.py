from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Voice Coach Recorder"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    device_token: str = "change-me-device-token"

    database_url: str = "sqlite:///./data/voice_coach.db"
    storage_dir: str = "./data/storage"
    max_upload_mb: int = Field(default=200, gt=0)

    redis_url: str = "redis://redis:6379/0"
    use_background_queue: bool = False

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = ""
    deepseek_reasoning_model: str = ""
    use_deepseek: bool = False

    asr_provider: str = "mock"
    funasr_model_dir: str = "./models/funasr"
    sensevoice_model_dir: str = "./models/sensevoice"
    enable_diarization: bool = False

    raw_audio_retention_days: int = Field(default=30, ge=1)
    backup_retention_days: int = Field(default=14, ge=1)
    require_https: bool = False

    cors_origins: str = "*"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
