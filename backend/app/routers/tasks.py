import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.billing import ledger
from app.config import settings
from app.db import get_db
from app.errors import api_error
from app.media import MediaError, detect_image_suffix, mp3_duration_seconds
from app.models import Task, utcnow
from app.schemas import DownloadOut, TaskListOut, TaskOut, TemplateOut
from app.storage import StorageError, storage
from app.worker import process_task
from inference.constants import MODE_ORIGINAL, MODE_PRESET, MODES
from inference.templates import TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter()

IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def serialize(task: Task, video_url: str | None = None) -> TaskOut:
    return TaskOut(
        id=task.id,
        status=task.status,
        mode=task.mode,
        template_id=task.template_id,
        offset_ms=task.offset_ms,
        audio_duration_sec=round(task.audio_duration_sec, 3),
        error_code=task.error_code,
        video_url=video_url,
        created_at=task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        updated_at=task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _video_url(task: Task) -> str | None:
    if task.status != "succeeded" or not task.output_key:
        return None
    try:
        return storage.presign(task.output_key, f"{task.id}.mp4")
    except StorageError as exc:
        raise api_error(503, "STORAGE_UNAVAILABLE") from exc


async def _read_upload(upload: UploadFile, limit: int) -> bytes:
    return await upload.read(limit + 1)


@router.get("/api/tasks/templates", response_model=list[TemplateOut])
def list_templates(_user: str = Depends(get_current_user)) -> list[TemplateOut]:
    return [TemplateOut(id=key, color=value["color"]) for key, value in TEMPLATES.items()]


@router.get("/api/tasks/list", response_model=TaskListOut)
@router.get("/api/tasks", response_model=TaskListOut)
def list_tasks(
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=settings.history_limit, ge=1, le=100),
) -> TaskListOut:
    rows = db.scalars(select(Task).order_by(Task.created_at.desc()).limit(limit)).all()
    return TaskListOut(tasks=[serialize(row) for row in rows], limit=limit)


@router.get("/api/task/{task_id}", response_model=TaskOut)
@router.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: str,
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    task = db.get(Task, task_id)
    if task is None:
        raise api_error(404, "TASK_NOT_FOUND")
    return serialize(task, _video_url(task))


@router.get("/api/tasks/{task_id}/download", response_model=DownloadOut)
def download_task(
    task_id: str,
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DownloadOut:
    task = db.get(Task, task_id)
    if task is None:
        raise api_error(404, "TASK_NOT_FOUND")
    if task.status != "succeeded" or not task.output_key:
        raise api_error(409, "OUTPUT_NOT_READY")
    url = _video_url(task)
    if not url:
        raise api_error(409, "OUTPUT_NOT_READY")
    return DownloadOut(url=url, expires_in=settings.presign_seconds)


@router.post("/api/create-task", response_model=TaskOut, status_code=201)
@router.post("/api/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    mode: str = Form(...),
    offset_ms: int = Form(0),
    template_id: str | None = Form(None),
    portrait: UploadFile = File(...),
    audio: UploadFile = File(...),
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    ledger.authorize(username)
    if mode not in MODES:
        raise api_error(400, "MODE_INVALID")
    if not settings.offset_ms_min <= offset_ms <= settings.offset_ms_max:
        raise api_error(400, "OFFSET_OUT_OF_RANGE")

    chosen_template = (template_id or "").strip() or None
    if mode == MODE_PRESET:
        if not chosen_template:
            raise api_error(400, "TEMPLATE_REQUIRED")
        if chosen_template not in TEMPLATES:
            raise api_error(400, "TEMPLATE_UNKNOWN")
    else:
        chosen_template = None

    portrait_bytes = await _read_upload(portrait, settings.max_image_bytes)
    audio_bytes = await _read_upload(audio, settings.max_audio_bytes)
    if not portrait_bytes:
        raise api_error(400, "IMAGE_REQUIRED")
    if len(portrait_bytes) > settings.max_image_bytes:
        raise api_error(413, "IMAGE_TOO_LARGE")
    if not audio_bytes:
        raise api_error(400, "AUDIO_REQUIRED")
    if len(audio_bytes) > settings.max_audio_bytes:
        raise api_error(413, "AUDIO_TOO_LARGE")

    try:
        suffix = detect_image_suffix(portrait_bytes)
        duration = mp3_duration_seconds(audio_bytes, settings.max_audio_seconds)
    except MediaError as exc:
        status = 413 if exc.code == "AUDIO_TOO_LONG" else 400
        raise api_error(status, exc.code, **exc.extra) from exc

    task_id = str(uuid.uuid4())
    portrait_key = f"uploads/{task_id}/portrait{suffix}"
    audio_key = f"uploads/{task_id}/audio.mp3"
    task = Task(
        id=task_id,
        owner=username,
        status="queued",
        mode=mode if mode == MODE_ORIGINAL else MODE_PRESET,
        template_id=chosen_template,
        offset_ms=offset_ms,
        audio_duration_sec=duration,
        portrait_key=portrait_key,
        audio_key=audio_key,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    uploaded: list[str] = []
    try:
        storage.ensure_bucket()
        storage.upload_bytes(portrait_key, portrait_bytes, IMAGE_TYPES[suffix])
        uploaded.append(portrait_key)
        storage.upload_bytes(audio_key, audio_bytes, "audio/mpeg")
        uploaded.append(audio_key)
    except StorageError as exc:
        for key in uploaded:
            storage.remove_quiet(key)
        task.status = "failed"
        task.error_code = "STORAGE_UNAVAILABLE"
        task.updated_at = utcnow()
        db.commit()
        raise api_error(503, "STORAGE_UNAVAILABLE") from exc

    try:
        process_task.delay(task.id)
    except Exception as exc:
        logger.exception("queue unavailable for task %s", task.id)
        task.status = "failed"
        task.error_code = "QUEUE_UNAVAILABLE"
        task.updated_at = utcnow()
        db.commit()
        raise api_error(503, "QUEUE_UNAVAILABLE") from exc

    return serialize(task)
