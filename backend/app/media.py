import io

from mutagen.mp3 import MP3

class MediaError(Exception):
    def __init__(self, code: str, **extra):
        self.code = code
        self.extra = extra
        super().__init__(code)


def detect_image_suffix(raw: bytes) -> str:
    if raw.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if len(raw) >= 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return ".webp"
    raise MediaError("IMAGE_INVALID")


def mp3_duration_seconds(raw: bytes, max_seconds: float) -> float:
    if not raw.startswith(b"ID3") and not (
        len(raw) >= 2 and raw[0] == 0xFF and (raw[1] & 0xE0) == 0xE0
    ):
        raise MediaError("AUDIO_INVALID")
    buffer = io.BytesIO(raw)
    buffer.name = "audio.mp3"
    try:
        length = float(MP3(buffer).info.length)
    except Exception as exc:
        raise MediaError("AUDIO_INVALID") from exc
    if length <= 0:
        raise MediaError("AUDIO_INVALID")
    # Frame headers often land a fraction over the nominal length.
    if length > max_seconds + 0.1:
        raise MediaError("AUDIO_TOO_LONG", seconds=round(length, 2), max=max_seconds)
    return length
