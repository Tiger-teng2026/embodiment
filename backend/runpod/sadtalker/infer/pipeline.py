"""下载素材、做人脸检测，再调用 SadTalker。只写出无声画面。"""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
import uuid
from pathlib import Path

from face_check import FaceMissing, assert_one_face

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024


class InferFailure(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(message)


def render_silent_video(
    *,
    image_url: str,
    audio_url: str,
    offset_ms: int,
    max_duration: int,
    work_root: Path,
    output_dir: Path,
) -> Path:
    job = work_root / uuid.uuid4().hex
    job.mkdir(parents=True, exist_ok=True)
    image_path = job / "source.jpg"
    audio_path = job / "driven.mp3"
    wav_path = job / "driven.wav"
    try:
        return _render_job(job, image_path, audio_path, wav_path, image_url, audio_url, offset_ms, max_duration, output_dir)
    finally:
        shutil.rmtree(job, ignore_errors=True)


def _render_job(job, image_path, audio_path, wav_path, image_url, audio_url, offset_ms, max_duration, output_dir) -> Path:
    _download(image_url, image_path, MAX_IMAGE_BYTES, "image")
    _as_jpeg(image_path)
    _download(audio_url, audio_path, MAX_AUDIO_BYTES, "audio")
    try:
        assert_one_face(image_path)
    except FaceMissing as exc:
        raise InferFailure(422, "FACE_NOT_DETECTED", "没有检测到可用的人脸") from exc
    limit = min(30, max(1, int(max_duration)))
    duration = _duration(audio_path)
    if duration <= 0:
        raise InferFailure(400, "AUDIO_INVALID", "音频无法读取")
    _to_wav(audio_path, wav_path, limit)
    timeout = max(30, int(os.environ.get("INFER_TIMEOUT_SECONDS", "180")))
    try:
        produced = _run_sadtalker(image_path, wav_path, job / "result", timeout)
    except subprocess.TimeoutExpired as exc:
        raise InferFailure(504, "GPU_TIMEOUT", "推理超时") from exc
    silent = output_dir / f"{uuid.uuid4().hex}.mp4"
    output_dir.mkdir(parents=True, exist_ok=True)
    _silent_with_offset(produced, silent, offset_ms)
    return silent


def _run_sadtalker(image_path: Path, wav_path: Path, result_dir: Path, timeout: int) -> Path:
    home = Path(os.environ.get("SADTALKER_HOME", "/opt/sadtalker"))
    checkpoints = os.environ.get("SADTALKER_CHECKPOINT_DIR", "/workspace/sadtalker/checkpoints")
    size = os.environ.get("SADTALKER_SIZE", "256")
    result_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "python3",
        "inference.py",
        "--driven_audio",
        str(wav_path),
        "--source_image",
        str(image_path),
        "--result_dir",
        str(result_dir),
        "--checkpoint_dir",
        checkpoints,
        "--still",
        "--preprocess",
        "crop",
        "--size",
        size,
        "--batch_size",
        "1",
    ]
    completed = subprocess.run(
        command,
        cwd=home,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    log = f"{completed.stdout}\n{completed.stderr}"
    if "Can't get the coeffs of the input" in log:
        raise InferFailure(422, "FACE_NOT_DETECTED", "没有检测到可用的人脸")
    videos = sorted(result_dir.glob("*.mp4"), key=lambda path: path.stat().st_mtime)
    if completed.returncode != 0 or not videos:
        raise InferFailure(500, "SERVICE_ERROR", "口型画面生成失败")
    return videos[-1]


def _silent_with_offset(source: Path, dest: Path, offset_ms: int) -> None:
    seconds = abs(int(offset_ms)) / 1000
    command = ["ffmpeg", "-y", "-i", str(source)]
    if offset_ms > 0:
        command += ["-vf", f"tpad=start_mode=clone:start_duration={seconds:.3f}"]
    elif offset_ms < 0:
        command += ["-ss", f"{seconds:.3f}"]
    command += ["-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest)]
    _ffmpeg(command, "画面封装失败")


def _to_wav(source: Path, dest: Path, max_seconds: int) -> None:
    # 只为驱动口型准备一段最多 30 秒的波形。原音频不回传，也不做变调或音色处理。
    _ffmpeg(
        ["ffmpeg", "-y", "-i", str(source), "-t", str(max_seconds), "-ac", "1", "-ar", "16000", str(dest)],
        "音频无法读取",
        code="AUDIO_INVALID",
        status=400,
    )


def _duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    try:
        return float((completed.stdout or "").strip())
    except ValueError:
        return 0.0


def _as_jpeg(path: Path) -> None:
    import cv2

    image = cv2.imread(str(path))
    if image is None or not cv2.imwrite(str(path), image):
        raise InferFailure(400, "VALIDATION_ERROR", "图片无法读取")


def _download(url: str, dest: Path, limit: int, kind: str) -> None:
    if not url.startswith(("https://", "http://")):
        raise InferFailure(400, "VALIDATION_ERROR", "素材地址无效")
    request = urllib.request.Request(url, headers={"User-Agent": "embodiment-sadtalker"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(limit + 1)
    except Exception as exc:
        code = "AUDIO_INVALID" if kind == "audio" else "VALIDATION_ERROR"
        raise InferFailure(400, code, "素材下载失败") from exc
    if not data or len(data) > limit:
        code = "AUDIO_INVALID" if kind == "audio" else "VALIDATION_ERROR"
        raise InferFailure(400, code, "素材为空或超过大小限制")
    dest.write_bytes(data)


def _ffmpeg(command: list[str], message: str, code: str = "SERVICE_ERROR", status: int = 500) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise InferFailure(status, code, message)
