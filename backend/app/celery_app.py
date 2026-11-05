from celery import Celery

from app.config import settings

celery_app = Celery(
    "embodiment",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    worker_concurrency=1,
    worker_pool="solo",
    broker_connection_retry_on_startup=True,
)

# Celery's CLI looks for an attribute named `app` or `celery`.
app = celery_app

from app import worker as _worker  # noqa: E402, F401
