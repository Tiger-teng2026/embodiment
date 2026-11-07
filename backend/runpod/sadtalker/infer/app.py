"""SadTalker 无声口型服务。音频混流由 embodiment 主后端完成。"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from pipeline import InferFailure, render_silent_video

app = FastAPI(title="Embodiment SadTalker", version="1.0.0")
_gpu = threading.Lock()
_OUTPUT = Path(os.environ.get("SADTALKER_OUTPUT_DIR", "/workspace/outputs"))
_WORK = Path(os.environ.get("SADTALKER_WORK_DIR", "/tmp/sadtalker-jobs"))


class InferIn(BaseModel):
    source_image_url: str = Field(min_length=8, max_length=4000)
    audio_file_url: str = Field(min_length=8, max_length=4000)
    audio_offset: int = Field(ge=-1000, le=1000)
    max_duration: int = Field(default=30, ge=1, le=30)


@app.get("/health")
def health():
    marker = Path(os.environ.get("SADTALKER_CHECKPOINT_DIR", "/workspace/sadtalker/checkpoints"))
    ready = (marker / "SadTalker_V0.0.2_256.safetensors").is_file()
    body = {"ok": ready}
    return JSONResponse(status_code=200 if ready else 503, content=body)


@app.post("/infer")
def infer(payload: InferIn, request: Request, authorization: str | None = Header(default=None)):
    _check_key(authorization)
    if not _gpu.acquire(blocking=False):
        return JSONResponse(status_code=429, content={"code": "RATE_LIMITED", "message": "GPU 正在处理另一条任务"})
    try:
        _OUTPUT.mkdir(parents=True, exist_ok=True)
        _WORK.mkdir(parents=True, exist_ok=True)
        video = render_silent_video(
            image_url=payload.source_image_url,
            audio_url=payload.audio_file_url,
            offset_ms=payload.audio_offset,
            max_duration=payload.max_duration,
            work_root=_WORK,
            output_dir=_OUTPUT,
        )
        base = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/") or str(request.base_url).rstrip("/")
        return {"video_url": f"{base}/outputs/{video.name}"}
    except InferFailure as exc:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})
    finally:
        _gpu.release()


@app.get("/outputs/{name}")
def output_file(name: str, authorization: str | None = Header(default=None)):
    _check_key(authorization)
    if "/" in name or ".." in name or not name.endswith(".mp4"):
        return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": "文件不存在"})
    path = _OUTPUT / name
    if not path.is_file():
        return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": "文件不存在"})
    return FileResponse(path, media_type="video/mp4", filename=name)


def _check_key(authorization: str | None) -> None:
    expected = os.environ.get("INFERENCE_API_KEY", "").strip()
    if not expected:
        return
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token != expected:
        raise _AuthError()


class _AuthError(Exception):
    pass


@app.exception_handler(_AuthError)
def _unauthorized(_request, _exc):
    return JSONResponse(status_code=401, content={"code": "UNAUTHORIZED", "message": "推理密钥无效"})
