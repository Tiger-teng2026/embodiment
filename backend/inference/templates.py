"""Preset scenes. Drop a 1280x720 PNG at assets/scenes/{id}.png to replace the flat color."""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "scenes"

TEMPLATES: dict[str, dict[str, str]] = {
    "studio_soft": {"color": "#E7E1D8", "ffmpeg_color": "0xE7E1D8"},
    "office_day": {"color": "#D5DDE6", "ffmpeg_color": "0xD5DDE6"},
    "city_night": {"color": "#1C2430", "ffmpeg_color": "0x1C2430"},
    "home_warm": {"color": "#E8D2C0", "ffmpeg_color": "0xE8D2C0"},
}


def scene_asset(template_id: str) -> Path | None:
    path = ASSETS_DIR / f"{template_id}.png"
    if path.is_file():
        return path
    return None
