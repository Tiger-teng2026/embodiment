"""GPU pipeline for one task. LivePortrait stays loaded in this solo worker."""

import logging
import os
import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.billing import ledger
from app.celery_app import celery_app
from app.config import settings
from app.db import SessionLocal, init_db
from app.gpu_lock import gpu_lock
from app.models import Task, utcnow
from app.storage import StorageError, storage
from inference.errors import InferenceError
from celery.signals import worker_ready

from inference.liveportrait_runner import warmup
from inference.pipeline import InferenceRequest, run_inference

logger = logging.getLogger(__name__)


@worker_ready.connect
def _warmup_models(**_kwargs) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = str(settings.gpu_device_id)
    try:
        warmup(settings.liveportrait_home, settings.gpu_device_id)
    except Exception:
        logger.exception("LivePortrait warmup failed; the first task will report it")


def _mark_failed(db: Session, task_id: str, code: str) -> None:
    task = db.get(Task, task_id)
    if task is None:
        return
    task.status = "failed"
    task.error_code = code
    task.updated_at = utcnow()
    db.commit()
    ledger.record(task.owner, task.id, task.audio_duration_sec, "failed")


@celery_app.task(name="embodiment.process_task", acks_late=True)
def process_task(task_id: str) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = str(settings.gpu_device_id)
    init_db()
    db = SessionLocal()
    work = Path(settings.work_dir) / task_id
    try:
        task = db.get(Task, task_id)
        if task is None or task.status not in {"queued", "processing"}:
            return
        task.status = "processing"
        task.error_code = None
        task.updated_at = utcnow()
        db.commit()

        work.mkdir(parents=True, exist_ok=True)
        suffix = Path(task.portrait_key).suffix or ".jpg"
        portrait = work / f"portrait{suffix}"
        audio = work / "audio.mp3"
        output = work / "output.mp4"
        storage.ensure_bucket()
        storage.download(task.portrait_key, portrait)
        storage.download(task.audio_key, audio)
        with gpu_lock():
            run_inference(
                InferenceRequest(
                    task_id=task.id,
                    mode=task.mode,
                    portrait_path=portrait,
                    audio_path=audio,
                    output_path=output,
                    offset_ms=task.offset_ms,
                    template_id=task.template_id,
                    duration_sec=task.audio_duration_sec,
                    device_id=settings.gpu_device_id,
                    liveportrait_home=settings.liveportrait_home,
                    driving_path=settings.liveportrait_driving,
                    font_path=settings.font_path,
                    watermark_text=settings.watermark_text,
                    metadata_comment=settings.ai_metadata_comment,
                )
            )
        key = f"outputs/{task.id}.mp4"
        storage.upload_file(key, output, "video/mp4")
        task.output_key = key
        task.status = "succeeded"
        task.error_code = None
        task.updated_at = utcnow()
        db.commit()
        ledger.record(task.owner, task.id, task.audio_duration_sec, "succeeded")
    except InferenceError as exc:
        logger.info("task %s failed: %s", task_id, exc.code)
        db.rollback()
        _mark_failed(db, task_id, exc.code)
    except StorageError:
        logger.exception("storage failed for task %s", task_id)
        db.rollback()
        _mark_failed(db, task_id, "STORAGE_UNAVAILABLE")
    except Exception:
        logger.exception("task %s failed", task_id)
        try:
            db.rollback()
            _mark_failed(db, task_id, "INFERENCE_FAILED")
        except Exception:
            logger.exception("could not record failure for task %s", task_id)
    finally:
        db.close()
        shutil.rmtree(work, ignore_errors=True)
