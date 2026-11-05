from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), default="admin")
    status: Mapped[str] = mapped_column(String(20), index=True)
    mode: Mapped[str] = mapped_column(String(32))
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    offset_ms: Mapped[int] = mapped_column(Integer)
    audio_duration_sec: Mapped[float] = mapped_column(Float)
    portrait_key: Mapped[str] = mapped_column(String(512))
    audio_key: Mapped[str] = mapped_column(String(512))
    output_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
