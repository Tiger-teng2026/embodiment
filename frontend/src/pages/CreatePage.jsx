import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../api/client";
import FileField from "../components/FileField";
import { readAudioDuration } from "../lib/audioDuration";
import { formatSeconds } from "../lib/format";
import { FALLBACK_LIMITS, limitsFromMeta, megabytes } from "../lib/limits";
import { FALLBACK_TEMPLATES } from "../lib/templates";

const MODES = [
  { id: "original_bg", title: "create.modeOriginal", desc: "create.modeOriginalDesc" },
  { id: "preset_scene", title: "create.modePreset", desc: "create.modePresetDesc" },
];

function isPortrait(file) {
  const typeOk = ["image/jpeg", "image/png", "image/webp"].includes(file.type);
  const nameOk = /\.(jpe?g|png|webp)$/i.test(file.name);
  if (file.type && !typeOk) return false;
  return typeOk || nameOk;
}

function isMp3(file) {
  const nameOk = /\.mp3$/i.test(file.name);
  if (!nameOk) return false;
  if (file.type && file.type !== "audio/mpeg" && file.type !== "audio/mp3") return false;
  return true;
}

export default function CreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [limits, setLimits] = useState(FALLBACK_LIMITS);
  const [templates, setTemplates] = useState(FALLBACK_TEMPLATES);
  const [mode, setMode] = useState("original_bg");
  const [templateId, setTemplateId] = useState(FALLBACK_TEMPLATES[0].id);
  const [portrait, setPortrait] = useState(null);
  const [audio, setAudio] = useState(null);
  const [duration, setDuration] = useState(null);
  const [offset, setOffset] = useState(0);
  const [agreed, setAgreed] = useState(false);
  const [errorCode, setErrorCode] = useState("");
  const [errorParams, setErrorParams] = useState({});
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api("/api/meta", { auth: false })
      .then((data) => {
        if (!cancelled) setLimits(limitsFromMeta(data));
      })
      .catch(() => {});
    api("/api/tasks/templates")
      .then((data) => {
        if (!cancelled && Array.isArray(data) && data.length) setTemplates(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  function fail(code, params = {}) {
    setErrorCode(code);
    setErrorParams(params);
  }

  function onPortrait(file) {
    setErrorCode("");
    if (!file) return;
    if (!isPortrait(file)) {
      setPortrait(null);
      fail("IMAGE_INVALID");
      return;
    }
    if (file.size > limits.maxImageBytes) {
      setPortrait(null);
      fail("IMAGE_TOO_LARGE", { size: megabytes(limits.maxImageBytes) });
      return;
    }
    setPortrait(file);
  }

  async function onAudio(file) {
    setErrorCode("");
    setDuration(null);
    setAudio(null);
    if (!file) return;
    if (!isMp3(file)) {
      fail("AUDIO_TYPE");
      return;
    }
    if (file.size > limits.maxAudioBytes) {
      fail("AUDIO_TOO_LARGE", { size: megabytes(limits.maxAudioBytes) });
      return;
    }
    try {
      const seconds = await readAudioDuration(file);
      if (seconds > limits.maxAudioSeconds + 0.1) {
        setDuration(seconds);
        fail("AUDIO_TOO_LONG", {
          seconds: formatSeconds(seconds),
          max: limits.maxAudioSeconds,
        });
        return;
      }
      setAudio(file);
      setDuration(seconds);
    } catch {
      fail("AUDIO_INVALID");
    }
  }

  function setOffsetClamped(value) {
    if (!Number.isFinite(value)) return;
    const next = Math.min(limits.offsetMax, Math.max(limits.offsetMin, Math.round(value)));
    setOffset(next);
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!portrait) return fail("IMAGE_REQUIRED");
    if (!audio) return fail(duration && duration > limits.maxAudioSeconds ? "AUDIO_TOO_LONG" : "AUDIO_REQUIRED", {
      seconds: duration ? formatSeconds(duration) : "",
      max: limits.maxAudioSeconds,
    });
    if (mode === "preset_scene" && !templateId) return fail("TEMPLATE_REQUIRED");
    if (offset < limits.offsetMin || offset > limits.offsetMax) return fail("OFFSET_OUT_OF_RANGE");
    if (!agreed) return fail("AGREEMENT_REQUIRED");

    const form = new FormData();
    form.set("mode", mode);
    form.set("offset_ms", String(offset));
    if (mode === "preset_scene") form.set("template_id", templateId);
    form.set("portrait", portrait);
    form.set("audio", audio);

    setPending(true);
    setErrorCode("");
    try {
      await api("/api/tasks", { method: "POST", form });
      navigate("/history");
    } catch (error) {
      const code = error instanceof ApiError ? error.code : "NETWORK";
      const detail = error instanceof ApiError ? error.detail : {};
      fail(code, {
        seconds: detail.seconds ?? "",
        max: detail.max ?? limits.maxAudioSeconds,
        size: code === "AUDIO_TOO_LARGE" ? megabytes(limits.maxAudioBytes) : megabytes(limits.maxImageBytes),
      });
    } finally {
      setPending(false);
    }
  }

  const imageMb = megabytes(limits.maxImageBytes);
  const errorText = errorCode
    ? t(`errors.${errorCode}`, {
        defaultValue: t("errors.UNKNOWN"),
        max: limits.maxAudioSeconds,
        size: imageMb,
        ...errorParams,
      })
    : "";

  return (
    <form className="grid gap-4" onSubmit={onSubmit}>
      <section className="card">
        <h1 className="text-lg font-semibold">{t("create.title")}</h1>
        <p className="hint mt-2">{t("create.intro")}</p>
      </section>

      <section className="card">
        <h2 className="text-sm font-medium">{t("create.modeTitle")}</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label={t("create.modeTitle")}>
          {MODES.map((item) => {
            const selected = mode === item.id;
            return (
              <button
                key={item.id}
                type="button"
                role="radio"
                aria-checked={selected}
                onClick={() => setMode(item.id)}
                className={`rounded-xl border p-4 text-left ${selected ? "border-zinc-900" : "border-zinc-200"}`}
              >
                <span className="block text-sm font-medium">{t(item.title)}</span>
                <span className="hint mt-1 block">{t(item.desc)}</span>
              </button>
            );
          })}
        </div>
      </section>

      {mode === "preset_scene" ? (
        <section className="card">
          <h2 className="text-sm font-medium">{t("create.templateTitle")}</h2>
          <p className="hint mt-1">{t("create.templateHint")}</p>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4" role="radiogroup" aria-label={t("create.templateTitle")}>
            {templates.map((item) => {
              const selected = templateId === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setTemplateId(item.id)}
                  className={`rounded-xl border p-3 text-left ${selected ? "border-zinc-900" : "border-zinc-200"}`}
                >
                  <span className="block h-12 rounded-md border border-black/5" style={{ background: item.color }} />
                  <span className="mt-2 block text-sm font-medium">
                    {t(`templates.${item.id}.title`, { defaultValue: item.id })}
                  </span>
                  <span className="hint mt-1 block">{t(`templates.${item.id}.desc`, { defaultValue: "" })}</span>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="card grid gap-5 sm:grid-cols-2">
        <FileField
          label={t("create.portraitTitle")}
          hint={t("create.portraitHint", { size: imageMb })}
          accept="image/jpeg,image/png,image/webp"
          action={t("create.portraitAction")}
          fileName={portrait ? t("create.fileReady", { name: portrait.name }) : ""}
          onFile={onPortrait}
        />
        <div>
          <FileField
            label={t("create.audioTitle")}
            hint={t("create.audioHint", { max: limits.maxAudioSeconds })}
            accept="audio/mpeg,.mp3"
            action={t("create.audioAction")}
            fileName={audio ? t("create.fileReady", { name: audio.name }) : ""}
            onFile={onAudio}
          />
          {duration ? <p className="mt-2 text-sm text-zinc-800">{t("create.audioDuration", { seconds: formatSeconds(duration) })}</p> : null}
        </div>
      </section>

      <section className="card">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-sm font-medium">{t("create.offsetTitle")}</h2>
          <p className="text-sm text-zinc-800">{t("create.offsetValue", { value: offset })}</p>
        </div>
        <p className="hint mt-1">{t("create.offsetHint")}</p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            className="w-full accent-zinc-900"
            type="range"
            min={limits.offsetMin}
            max={limits.offsetMax}
            step={10}
            value={offset}
            aria-label={t("create.offsetTitle")}
            onChange={(event) => setOffsetClamped(event.target.valueAsNumber)}
          />
          <input
            className="input sm:w-28"
            type="number"
            min={limits.offsetMin}
            max={limits.offsetMax}
            step={10}
            value={offset}
            aria-label={t("create.offsetValue", { value: offset })}
            onChange={(event) => setOffsetClamped(event.target.valueAsNumber)}
          />
        </div>
      </section>

      <section className="card">
        <label className="flex items-start gap-3 text-sm leading-6 text-zinc-800">
          <input
            className="mt-1 accent-zinc-900"
            type="checkbox"
            checked={agreed}
            onChange={(event) => setAgreed(event.target.checked)}
          />
          <span>
            {t("create.agreementLabel")}{" "}
            <Link to="/agreement" className="underline underline-offset-2">
              {t("create.agreementLink")}
            </Link>
          </span>
        </label>
        <p className="hint mt-3">{t("create.watermarkNote", { text: limits.watermark })}</p>
        <p className="hint mt-2">{t("create.pipelineNote")}</p>
        {errorText ? (
          <p className="error mt-4" role="alert">
            {errorText}
          </p>
        ) : null}
        <button className="btn mt-5 w-full sm:w-auto" type="submit" disabled={pending}>
          {pending ? t("create.submitting") : t("create.submit")}
        </button>
      </section>
    </form>
  );
}
