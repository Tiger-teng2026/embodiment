import redis
from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthOut, MetaOut
from app.storage import storage
from inference.constants import MODES

router = APIRouter()


def _redis_ok() -> bool:
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        return bool(client.ping())
    except redis.RedisError:
        return False


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(ok=True, redis=_redis_ok(), minio=storage.healthy())


@router.get("/meta", response_model=MetaOut)
def meta() -> MetaOut:
    return MetaOut(
        max_audio_seconds=settings.max_audio_seconds,
        max_image_bytes=settings.max_image_bytes,
        max_audio_bytes=settings.max_audio_bytes,
        offset_ms_min=settings.offset_ms_min,
        offset_ms_max=settings.offset_ms_max,
        watermark_text=settings.watermark_text,
        modes=list(MODES),
        history_limit=settings.history_limit,
    )
