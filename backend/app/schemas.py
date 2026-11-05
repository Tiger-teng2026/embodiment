from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str


class TaskOut(BaseModel):
    id: str
    status: str
    mode: str
    template_id: str | None
    offset_ms: int
    audio_duration_sec: float
    error_code: str | None
    video_url: str | None = None
    created_at: str
    updated_at: str


class TaskListOut(BaseModel):
    tasks: list[TaskOut]
    limit: int


class DownloadOut(BaseModel):
    url: str
    expires_in: int


class TemplateOut(BaseModel):
    id: str
    color: str


class MetaOut(BaseModel):
    max_audio_seconds: float
    max_image_bytes: int
    max_audio_bytes: int
    offset_ms_min: int
    offset_ms_max: int
    watermark_text: str
    modes: list[str]
    history_limit: int


class HealthOut(BaseModel):
    ok: bool
    redis: bool
    minio: bool
