"""LivePortrait entry.

Stock LivePortrait is driven by a face video, not by an audio file. This runner
animates the lip region from a driving clip, trimmed to the audio length. The
caller's original mp3 is muxed afterwards and is never passed to the model.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import ffmpeg

from inference.errors import InferenceError

logger = logging.getLogger(__name__)

_pipeline = None


def warmup(liveportrait_home: str, device_id: str) -> None:
    _load_pipeline(Path(liveportrait_home), device_id)


def drive_portrait(
    *,
    source: Path,
    output_dir: Path,
    duration_sec: float,
    liveportrait_home: str,
    driving_path: str,
    device_id: str,
) -> Path:
    home = Path(liveportrait_home)
    driving_src = Path(driving_path) if driving_path else home / "assets" / "examples" / "driving" / "d0.mp4"
    weights = home / "pretrained_weights" / "liveportrait" / "base_models" / "warping_module.pth"
    if not (home / "inference.py").is_file() or not weights.is_file() or not driving_src.is_file():
        raise InferenceError("LIVEPORTRAIT_NOT_READY")

    output_dir.mkdir(parents=True, exist_ok=True)
    driving = output_dir / "driving.mp4"
    _loop_driving(driving_src, driving, duration_sec)
    _load_pipeline(home, device_id)
    rendered = _execute(home, source, driving, output_dir)
    if not rendered.is_file() or rendered.stat().st_size == 0:
        raise InferenceError("INFERENCE_FAILED")
    return rendered


def _load_pipeline(home: Path, device_id: str) -> None:
    global _pipeline
    if _pipeline is not None:
        return
    os.environ["CUDA_VISIBLE_DEVICES"] = str(device_id)
    if str(home) not in sys.path:
        sys.path.insert(0, str(home))
    try:
        from src.config.argument_config import ArgumentConfig
        from src.config.crop_config import CropConfig
        from src.config.inference_config import InferenceConfig
        from src.live_portrait_pipeline import LivePortraitPipeline
    except Exception as exc:
        logger.exception("liveportrait import failed")
        raise InferenceError("LIVEPORTRAIT_NOT_READY") from exc

    # CUDA_VISIBLE_DEVICES leaves one card, so LivePortrait must use cuda:0.
    args = ArgumentConfig(device_id=0, flag_force_cpu=False, flag_use_half_precision=True)
    args.animation_region = "lip"
    inference_cfg = _partial(InferenceConfig, args)
    crop_cfg = _partial(CropConfig, args)
    try:
        _pipeline = LivePortraitPipeline(inference_cfg=inference_cfg, crop_cfg=crop_cfg)
    except Exception as exc:
        logger.exception("liveportrait load failed")
        raise InferenceError("LIVEPORTRAIT_NOT_READY") from exc


def _execute(home: Path, source: Path, driving: Path, output_dir: Path) -> Path:
    from src.config.argument_config import ArgumentConfig

    args = ArgumentConfig(
        source=str(source),
        driving=str(driving),
        output_dir=str(output_dir),
        device_id=0,
        flag_pasteback=True,
        flag_do_crop=True,
        flag_relative_motion=True,
        flag_stitching=True,
        audio_priority="driving",
    )
    args.animation_region = "lip"
    previous = Path.cwd()
    os.chdir(home)
    try:
        rendered, _concat = _pipeline.execute(args)
    except InferenceError:
        raise
    except Exception as exc:
        logger.exception("liveportrait execute failed")
        raise InferenceError("INFERENCE_FAILED") from exc
    finally:
        os.chdir(previous)
    return Path(rendered)


def _partial(target, source):
    values = {key: getattr(source, key) for key in target.__dataclass_fields__ if hasattr(source, key)}
    return target(**values)


def _loop_driving(source: Path, dest: Path, duration_sec: float) -> None:
    try:
        (
            ffmpeg.input(str(source), stream_loop=-1)
            .output(
                str(dest),
                t=f"{duration_sec:.3f}",
                vcodec="libx264",
                pix_fmt="yuv420p",
                r=25,
                an=None,
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as exc:
        logger.error("driving clip failed: %s", (exc.stderr or b"").decode("utf-8", errors="replace")[-1500:])
        raise InferenceError("INFERENCE_FAILED") from exc
