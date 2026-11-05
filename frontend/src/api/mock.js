import { readAudioDuration } from "../lib/audioDuration";
import { FALLBACK_LIMITS } from "../lib/limits";
import { FALLBACK_TEMPLATES } from "../lib/templates";

const MOCK_USER = "admin";
const MOCK_PASSWORD = "embodiment";
const MOCK_TOKEN = "mock-token";

const tasks = [];
let previewUrl = "";

async function ensurePreviewUrl() {
  if (previewUrl) return previewUrl;
  if (typeof document === "undefined" || typeof MediaRecorder === "undefined") return "";
  const canvas = document.createElement("canvas");
  canvas.width = 640;
  canvas.height = 360;
  const ctx = canvas.getContext("2d");
  if (!ctx || typeof canvas.captureStream !== "function") return "";
  ctx.fillStyle = "#18181b";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ffffff";
  ctx.font = "28px sans-serif";
  ctx.fillText("Embodiment mock", 36, 180);

  const stream = canvas.captureStream(15);
  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
    ? "video/webm;codecs=vp8"
    : "video/webm";
  const recorder = new MediaRecorder(stream, { mimeType });
  const chunks = [];
  const stopped = new Promise((resolve) => {
    recorder.onstop = () => resolve();
  });
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  };
  recorder.start();
  await new Promise((resolve) => window.setTimeout(resolve, 500));
  recorder.stop();
  await stopped;
  stream.getTracks().forEach((track) => track.stop());
  previewUrl = URL.createObjectURL(new Blob(chunks, { type: "video/webm" }));
  return previewUrl;
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function fail(status, code, extra = {}) {
  return { status, detail: { code, ...extra } };
}

function ok(data, status = 200) {
  return { status, data };
}

function header(config, name) {
  const headers = config.headers;
  if (!headers) return "";
  if (typeof headers.get === "function") return headers.get(name) || "";
  return headers[name] || headers[name.toLowerCase()] || "";
}

function bodyOf(config) {
  const data = config.data;
  if (typeof data === "string") {
    try {
      return JSON.parse(data);
    } catch {
      return {};
    }
  }
  return data ?? {};
}

function requireUser(config) {
  if (header(config, "Authorization") !== `Bearer ${MOCK_TOKEN}`) {
    return fail(401, "UNAUTHORIZED");
  }
  return null;
}

function field(data, key) {
  if (typeof FormData !== "undefined" && data instanceof FormData) return data.get(key);
  return data?.[key];
}

function arm(task) {
  window.setTimeout(() => {
    if (task.status !== "queued") return;
    task.status = "processing";
    task.updated_at = nowIso();
  }, 2000);
  window.setTimeout(() => {
    if (task.status !== "queued" && task.status !== "processing") return;
    task.status = "succeeded";
    task.updated_at = nowIso();
  }, 6000);
}

function publicTask(task) {
  return {
    id: task.id,
    status: task.status,
    mode: task.mode,
    template_id: task.template_id,
    offset_ms: task.offset_ms,
    audio_duration_sec: task.audio_duration_sec,
    error_code: task.error_code,
    created_at: task.created_at,
    updated_at: task.updated_at,
  };
}

async function createTask(config) {
  const denied = requireUser(config);
  if (denied) return denied;

  const data = bodyOf(config);
  const mode = String(field(data, "mode") || "");
  const templateRaw = field(data, "template_id");
  const templateId = templateRaw ? String(templateRaw) : null;
  const offset = Number(field(data, "offset_ms") ?? 0);
  const portrait = field(data, "portrait");
  const audio = field(data, "audio");

  if (mode !== "original_bg" && mode !== "preset_scene") return fail(400, "MODE_INVALID");
  if (!Number.isInteger(offset) || offset < FALLBACK_LIMITS.offsetMin || offset > FALLBACK_LIMITS.offsetMax) {
    return fail(400, "OFFSET_OUT_OF_RANGE");
  }
  if (mode === "preset_scene" && !templateId) return fail(400, "TEMPLATE_REQUIRED");
  if (mode === "preset_scene" && !FALLBACK_TEMPLATES.some((item) => item.id === templateId)) {
    return fail(400, "TEMPLATE_UNKNOWN");
  }
  if (!(portrait instanceof Blob) || portrait.size === 0) return fail(400, "IMAGE_REQUIRED");
  if (portrait.size > FALLBACK_LIMITS.maxImageBytes) return fail(413, "IMAGE_TOO_LARGE");
  if (!(audio instanceof Blob) || audio.size === 0) return fail(400, "AUDIO_REQUIRED");
  if (audio.size > FALLBACK_LIMITS.maxAudioBytes) return fail(413, "AUDIO_TOO_LARGE");

  let seconds = 0;
  try {
    seconds = await readAudioDuration(audio);
  } catch {
    return fail(400, "AUDIO_INVALID");
  }
  if (seconds > FALLBACK_LIMITS.maxAudioSeconds + 0.1) {
    return fail(413, "AUDIO_TOO_LONG", {
      seconds: Number(seconds.toFixed(2)),
      max: FALLBACK_LIMITS.maxAudioSeconds,
    });
  }

  const stamp = nowIso();
  const task = {
    id: crypto.randomUUID(),
    status: "queued",
    mode,
    template_id: mode === "preset_scene" ? templateId : null,
    offset_ms: offset,
    audio_duration_sec: Number(seconds.toFixed(3)),
    error_code: null,
    created_at: stamp,
    updated_at: stamp,
  };
  tasks.unshift(task);
  arm(task);
  return ok(publicTask(task), 201);
}

export async function mockDispatch(config) {
  const method = String(config.method || "get").toUpperCase();
  const path = String(config.url || "").split("?")[0];

  if (method === "POST" && path === "/api/auth/login") {
    const body = bodyOf(config);
    if (body.username !== MOCK_USER || body.password !== MOCK_PASSWORD) {
      return fail(401, "INVALID_CREDENTIALS");
    }
    return ok({ access_token: MOCK_TOKEN, token_type: "bearer" });
  }

  if (method === "GET" && path === "/api/auth/me") {
    const denied = requireUser(config);
    if (denied) return denied;
    return ok({ username: MOCK_USER });
  }

  if (method === "GET" && path === "/api/meta") {
    return ok({
      max_audio_seconds: FALLBACK_LIMITS.maxAudioSeconds,
      max_image_bytes: FALLBACK_LIMITS.maxImageBytes,
      max_audio_bytes: FALLBACK_LIMITS.maxAudioBytes,
      offset_ms_min: FALLBACK_LIMITS.offsetMin,
      offset_ms_max: FALLBACK_LIMITS.offsetMax,
      watermark_text: FALLBACK_LIMITS.watermark,
      modes: ["original_bg", "preset_scene"],
      history_limit: FALLBACK_LIMITS.historyLimit,
    });
  }

  if (method === "GET" && path === "/api/tasks/templates") {
    const denied = requireUser(config);
    if (denied) return denied;
    return ok(FALLBACK_TEMPLATES.map((item) => ({ id: item.id, color: item.color })));
  }

  if (method === "GET" && path === "/api/tasks") {
    const denied = requireUser(config);
    if (denied) return denied;
    const limit = FALLBACK_LIMITS.historyLimit;
    return ok({ tasks: tasks.slice(0, limit).map(publicTask), limit });
  }

  const download = path.match(/^\/api\/tasks\/([^/]+)\/download$/);
  if (method === "GET" && download) {
    const denied = requireUser(config);
    if (denied) return denied;
    const task = tasks.find((item) => item.id === download[1]);
    if (!task) return fail(404, "TASK_NOT_FOUND");
    if (task.status !== "succeeded") return fail(409, "OUTPUT_NOT_READY");
    const url = await ensurePreviewUrl();
    if (!url) return fail(500, "INFERENCE_FAILED");
    return ok({ url, expires_in: 3600 });
  }

  const single = path.match(/^\/api\/tasks\/([^/]+)$/);
  if (method === "GET" && single) {
    const denied = requireUser(config);
    if (denied) return denied;
    const task = tasks.find((item) => item.id === single[1]);
    if (!task) return fail(404, "TASK_NOT_FOUND");
    return ok(publicTask(task));
  }

  if (method === "POST" && path === "/api/tasks") return createTask(config);

  return fail(404, "UNKNOWN");
}
