export const FALLBACK_LIMITS = {
  maxAudioSeconds: 30,
  maxImageBytes: 15 * 1024 * 1024,
  maxAudioBytes: 20 * 1024 * 1024,
  offsetMin: -1000,
  offsetMax: 1000,
  watermark: "化身 Embodiment AI合成内容",
  historyLimit: 50,
};

export function limitsFromMeta(data) {
  if (!data) return FALLBACK_LIMITS;
  return {
    maxAudioSeconds: Number(data.max_audio_seconds) || FALLBACK_LIMITS.maxAudioSeconds,
    maxImageBytes: Number(data.max_image_bytes) || FALLBACK_LIMITS.maxImageBytes,
    maxAudioBytes: Number(data.max_audio_bytes) || FALLBACK_LIMITS.maxAudioBytes,
    offsetMin: Number.isFinite(data.offset_ms_min) ? data.offset_ms_min : FALLBACK_LIMITS.offsetMin,
    offsetMax: Number.isFinite(data.offset_ms_max) ? data.offset_ms_max : FALLBACK_LIMITS.offsetMax,
    watermark: data.watermark_text || FALLBACK_LIMITS.watermark,
    historyLimit: Number(data.history_limit) || FALLBACK_LIMITS.historyLimit,
  };
}

export function megabytes(bytes) {
  return Math.round(bytes / (1024 * 1024));
}
