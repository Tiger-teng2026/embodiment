"""Background removal for preset scenes. The original-photo mode does not call this."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image

from inference.errors import InferenceError
from inference.templates import TEMPLATES, scene_asset

logger = logging.getLogger(__name__)

_session = None


def cut_and_composite(portrait: Path, template_id: str, dest: Path) -> Path:
    try:
        from rembg import new_session, remove
    except Exception as exc:
        logger.exception("rembg import failed")
        raise InferenceError("INFERENCE_FAILED") from exc

    global _session
    if _session is None:
        # Keep cutout on CPU so the 4090 stays available for LivePortrait.
        _session = new_session("u2net", providers=["CPUExecutionProvider"])
    cut = Image.open(io.BytesIO(remove(portrait.read_bytes(), session=_session))).convert("RGBA")
    background = _background(template_id)
    fitted = _fit_height(cut, 640)
    x = (background.width - fitted.width) // 2
    y = (background.height - fitted.height) // 2
    background.paste(fitted, (x, y), fitted)
    dest.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(dest, quality=95)
    return dest


def _background(template_id: str) -> Image.Image:
    asset = scene_asset(template_id)
    if asset is not None:
        image = Image.open(asset).convert("RGB")
        return image.resize((1280, 720))
    color = TEMPLATES[template_id]["color"]
    return Image.new("RGB", (1280, 720), color)


def _fit_height(image: Image.Image, height: int) -> Image.Image:
    ratio = height / image.height
    width = max(2, int(image.width * ratio))
    if width % 2:
        width += 1
    return image.resize((width, height))
