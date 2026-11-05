"""Shared product limits. The API, worker, and pipeline all read from here."""

MAX_AUDIO_SECONDS = 30.0
OFFSET_MS_MIN = -1000
OFFSET_MS_MAX = 1000
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024
HISTORY_LIMIT = 50

MODE_ORIGINAL = "original_bg"
MODE_PRESET = "preset_scene"
MODES = (MODE_ORIGINAL, MODE_PRESET)

WATERMARK_TEXT = "化身 Embodiment AI合成内容"
AI_METADATA_COMMENT = (
    "AI深度合成视觉内容，由化身 Embodiment 生成。"
    "音频为用户原始录音，未做语音合成、音色克隆或改写。"
    " AI-generated visual. Audio is the original recording and was not synthesized or cloned."
)

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 25
