"""Portrait pipeline: optional rembg, LivePortrait, then original-audio mux."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from inference.constants import (
    MAX_AUDIO_SECONDS,
    MODE_ORIGINAL,
    MODE_PRESET,
    MODES,
    OFFSET_MS_MAX,
    OFFSET_MS_MIN,
)
from inference.errors import InferenceError
from inference.ffmpeg_mux import mux_original_audio
from inference.liveportrait_runner import drive_portrait
from inference.portrait_prep import cut_and_composite
from inference.templates import TEMPLATES

logger = logging.getLogger(__name__)


@dataclass
class InferenceRequest:
    task_id: str
    mode: str
    portrait_path: Path
    audio_path: Path
    output_path: Path
    offset_ms: int
    template_id: str | None
    duration_sec: float
    device_id: str
    liveportrait_home: str
    driving_path: str = ""
    font_path: str = ""
    watermark_text: str = "化身 Embodiment AI合成内容"
    metadata_comment: str = ""


def run_inference(request: InferenceRequest) -> Path:
    _validate(request)
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    source = _prepare_source(request)
    rendered = drive_portrait(
        source=source,
        output_dir=request.output_path.parent / "liveportrait",
        duration_sec=request.duration_sec,
        liveportrait_home=request.liveportrait_home,
        driving_path=request.driving_path,
        device_id=request.device_id,
    )
    mux_original_audio(
        video_path=rendered,
        audio_path=request.audio_path,
        output_path=request.output_path,
        offset_ms=request.offset_ms,
        duration_sec=request.duration_sec,
        watermark_text=request.watermark_text,
        metadata_comment=request.metadata_comment,
        task_id=request.task_id,
        font_path=request.font_path,
    )
    if not request.output_path.is_file() or request.output_path.stat().st_size == 0:
        raise InferenceError("INFERENCE_FAILED")
    return request.output_path


def _prepare_source(request: InferenceRequest) -> Path:
    if request.mode == MODE_ORIGINAL:
        return _as_rgb(request.portrait_path, request.output_path.parent / "source.jpg")
    if not request.template_id or request.template_id not in TEMPLATES:
        raise InferenceError("TEMPLATE_UNKNOWN")
    logger.info("rembg cutout for preset scene %s", request.template_id)
    return cut_and_composite(
        request.portrait_path,
        request.template_id,
        request.output_path.parent / "source.jpg",
    )


def _as_rgb(src: Path, dest: Path) -> Path:
    if src.suffix.lower() in {".jpg", ".jpeg"}:
        return src
    Image.open(src).convert("RGB").save(dest, quality=95)
    return dest


def _validate(request: InferenceRequest) -> None:
    if request.mode not in MODES:
        raise InferenceError("MODE_INVALID")
    if request.duration_sec <= 0 or request.duration_sec > MAX_AUDIO_SECONDS + 0.1:
        raise InferenceError("AUDIO_TOO_LONG")
    if not OFFSET_MS_MIN <= request.offset_ms <= OFFSET_MS_MAX:
        raise InferenceError("OFFSET_OUT_OF_RANGE")
    if request.mode == MODE_PRESET and not request.template_id:
        raise InferenceError("TEMPLATE_REQUIRED")
    if not request.portrait_path.is_file() or not request.audio_path.is_file():
        raise InferenceError("INFERENCE_FAILED")
