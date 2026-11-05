import logging
from contextlib import contextmanager

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# One GPU job at a time. The lock outlives a crashed worker via its timeout.
GPU_LOCK_KEY = "embodiment:gpu"
GPU_LOCK_TIMEOUT_SEC = 30 * 60


@contextmanager
def gpu_lock():
    client = redis.Redis.from_url(settings.redis_url)
    lock = client.lock(GPU_LOCK_KEY, timeout=GPU_LOCK_TIMEOUT_SEC, blocking_timeout=GPU_LOCK_TIMEOUT_SEC)
    acquired = lock.acquire(blocking=True)
    if not acquired:
        raise TimeoutError("GPU lock was not acquired")
    try:
        yield
    finally:
        try:
            lock.release()
        except redis.exceptions.LockError:
            logger.warning("GPU lock had already expired")
