export function readAudioDuration(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const audio = document.createElement("audio");
    audio.preload = "metadata";
    let settled = false;
    const timer = setTimeout(() => finish(new Error("AUDIO_INVALID")), 4000);

    function finish(error, value) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      URL.revokeObjectURL(url);
      if (error) reject(error);
      else resolve(value);
    }

    audio.onloadedmetadata = () => {
      if (Number.isFinite(audio.duration) && audio.duration > 0) {
        finish(null, audio.duration);
        return;
      }
      const onTime = () => {
        audio.removeEventListener("timeupdate", onTime);
        if (!Number.isFinite(audio.duration) || audio.duration <= 0) finish(new Error("AUDIO_INVALID"));
        else finish(null, audio.duration);
      };
      audio.addEventListener("timeupdate", onTime);
      try {
        audio.currentTime = 1e101;
      } catch {
        finish(new Error("AUDIO_INVALID"));
      }
    };
    audio.onerror = () => finish(new Error("AUDIO_INVALID"));
    audio.src = url;
  });
}
