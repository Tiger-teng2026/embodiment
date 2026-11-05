from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from inference.constants import (
    AI_METADATA_COMMENT,
    HISTORY_LIMIT,
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    MAX_IMAGE_BYTES,
    OFFSET_MS_MAX,
    OFFSET_MS_MIN,
    WATERMARK_TEXT,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Embodiment"
    secret_key: str
    admin_username: str
    admin_password: str
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = "sqlite:////data/embodiment.db"
    redis_url: str
    gpu_device_id: str = "0"

    minio_endpoint: str
    minio_public_endpoint: str = ""
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = False
    minio_bucket_name: str
    presign_seconds: int = 3600

    cors_origins: str = "*"
    liveportrait_home: str = "/opt/LivePortrait"
    liveportrait_driving: str = ""

    max_audio_seconds: float = MAX_AUDIO_SECONDS
    max_image_bytes: int = MAX_IMAGE_BYTES
    max_audio_bytes: int = MAX_AUDIO_BYTES
    offset_ms_min: int = OFFSET_MS_MIN
    offset_ms_max: int = OFFSET_MS_MAX
    history_limit: int = HISTORY_LIMIT

    watermark_text: str = WATERMARK_TEXT
    ai_metadata_comment: str = AI_METADATA_COMMENT
    font_path: str = ""
    work_dir: str = "/data/work"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def secrets_are_set(self):
        required = (
            "secret_key",
            "admin_username",
            "admin_password",
            "redis_url",
            "minio_endpoint",
            "minio_access_key",
            "minio_secret_key",
            "minio_bucket_name",
        )
        missing = [name for name in required if not str(getattr(self, name)).strip()]
        if missing:
            raise ValueError("missing required settings: " + ", ".join(missing))
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_dirs(self) -> None:
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.removeprefix("sqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
