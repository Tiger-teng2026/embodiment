"""Mux the original mp3 onto the rendered picture. Audio is stream-copied."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import ffmpeg

from inference.constants import VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from inference.errors import InferenceError

logger = logging.getLogger(__name__)

FONT_CANDIDATES = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
)


def mux_original_audio(
    *,
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    offset_ms: int,
    duration_sec: float,
    watermark_text: str,
    metadata_comment: str,
    task_id: str,
    font_path: str,
) -> None:
    font = _font(font_path)
    text_file = output_path.parent / "watermark.txt"
    text_file.write_text(watermark_text, encoding="utf-8")
    total = duration_sec + abs(offset_ms) / 1000
    video_in, audio_in = _inputs(video_path, audio_path, offset_ms)
    draw = {
        "fontfile": _ffmpeg_path(font),
        "textfile": _ffmpeg_path(text_file),
        "fontsize": 28,
        "fontcolor": "white",
        "box": 1,
        "boxcolor": "black@0.45",
        "boxborderw": 12,
        "x": 24,
        "y": "h-th-24",
    }
    if font.suffix.lower() in {".ttc", ".otc"}:
        draw["fontindex"] = 0
    drawn = (
        video_in.video.filter("fps", fps=VIDEO_FPS)
        .filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT, force_original_aspect_ratio="decrease")
        .filter("pad", VIDEO_WIDTH, VIDEO_HEIGHT, "(ow-iw)/2", "(oh-ih)/2")
        .filter("setsar", 1)
        .filter("drawtext", **draw)
    )
    aigc = json.dumps(
        {
            "Label": "1",
            "ContentProducer": "Embodiment",
            "ProduceID": task_id,
            "ReserveCode1": "AI深度合成",
        },
        ensure_ascii=False,
    )
    stream = ffmpeg.output(
        drawn,
        audio_in.audio,
        str(output_path),
        vcodec="libx264",
        acodec="copy",
        pix_fmt="yuv420p",
        t=f"{total:.3f}",
    )
    command = stream.overwrite_output().compile()
    target = command[-1]
    command = command[:-1] + [
        "-metadata",
        f"comment={metadata_comment}",
        "-metadata",
        f"description={watermark_text}",
        "-metadata",
        f"AIGC={aigc}",
        "-movflags",
        "+faststart",
        target,
    ]
    try:
        ffmpeg.run(stream, cmd=command, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as exc:
        logger.error("ffmpeg mux failed: %s", (exc.stderr or b"").decode("utf-8", errors="replace")[-1500:])
        raise InferenceError("INFERENCE_FAILED") from exc


def _inputs(video_path: Path, audio_path: Path, offset_ms: int):
    if offset_ms > 0:
        return ffmpeg.input(str(video_path)), ffmpeg.input(str(audio_path), itsoffset=offset_ms / 1000)
    if offset_ms < 0:
        return ffmpeg.input(str(video_path), itsoffset=abs(offset_ms) / 1000), ffmpeg.input(str(audio_path))
    return ffmpeg.input(str(video_path)), ffmpeg.input(str(audio_path))


def _font(preferred: str) -> Path:
    if preferred and Path(preferred).is_file():
        return Path(preferred)
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return candidate
    root = Path("/usr/share/fonts")
    if root.is_dir():
        matches = sorted(root.rglob("NotoSansCJK*.ttc")) or sorted(root.rglob("NotoSansCJK*.otf"))
        if matches:
            return matches[0]
    raise InferenceError("FONT_MISSING")


def _ffmpeg_path(path: Path) -> str:
    return path.resolve().as_posix().replace(":", "\\:")
