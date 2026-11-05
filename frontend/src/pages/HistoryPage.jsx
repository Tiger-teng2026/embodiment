import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import { formatSeconds, formatTime } from "../lib/format";
import { FALLBACK_LIMITS, limitsFromMeta, megabytes } from "../lib/limits";

export default function HistoryPage() {
  const { t, i18n } = useTranslation();
  const [tasks, setTasks] = useState([]);
  const [limit, setLimit] = useState(FALLBACK_LIMITS.historyLimit);
  const [loading, setLoading] = useState(true);
  const [errorCode, setErrorCode] = useState("");
  const [errorParams, setErrorParams] = useState({});
  const [busyId, setBusyId] = useState("");

  const load = useCallback(async () => {
    const data = await api("/api/tasks");
    setTasks(data.tasks || []);
    setLimit(data.limit || FALLBACK_LIMITS.historyLimit);
  }, []);

  useEffect(() => {
    let cancelled = false;
    api("/api/meta", { auth: false })
      .then((data) => {
        if (!cancelled) setLimit(limitsFromMeta(data).historyLimit);
      })
      .catch(() => {});
    load()
      .catch((error) => {
        if (!cancelled) setErrorCode(error instanceof ApiError ? error.code : "NETWORK");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  useEffect(() => {
    const active = tasks.some((task) => task.status === "queued" || task.status === "processing");
    if (!active) return undefined;
    const timer = setInterval(() => {
      load().catch(() => {});
    }, 4000);
    return () => clearInterval(timer);
  }, [tasks, load]);

  async function onDownload(task) {
    const popup = window.open("", "_blank");
    setBusyId(task.id);
    setErrorCode("");
    try {
      const data = await api(`/api/tasks/${task.id}/download`);
      if (popup) popup.location.href = data.url;
      else window.location.assign(data.url);
    } catch (error) {
      if (popup) popup.close();
      const code = error instanceof ApiError ? error.code : "NETWORK";
      const detail = error instanceof ApiError ? error.detail : {};
      setErrorCode(code);
      setErrorParams({
        seconds: detail.seconds ?? "",
        max: detail.max ?? 30,
        size: megabytes(FALLBACK_LIMITS.maxImageBytes),
      });
    } finally {
      setBusyId("");
    }
  }

  const language = i18n.language?.startsWith("en") ? "en" : "zh";
  const errorText = errorCode
    ? t(`errors.${errorCode}`, { defaultValue: t("errors.UNKNOWN"), ...errorParams })
    : "";

  return (
    <div className="grid gap-4">
      <section className="card flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{t("history.title")}</h1>
          <p className="hint mt-2">{t("history.intro", { count: limit })}</p>
        </div>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => {
            setErrorCode("");
            load().catch((error) => setErrorCode(error instanceof ApiError ? error.code : "NETWORK"));
          }}
        >
          {t("history.refresh")}
        </button>
      </section>

      {errorText ? (
        <p className="error" role="alert">
          {errorText}
        </p>
      ) : null}

      {loading ? <p className="text-sm text-zinc-500">{t("common.loading")}</p> : null}

      {!loading && tasks.length === 0 ? (
        <section className="card">
          <p className="text-sm text-zinc-700">{t("history.empty")}</p>
          <Link to="/" className="btn mt-4">
            {t("history.openCreate")}
          </Link>
        </section>
      ) : null}

      <div className="grid gap-3" aria-live="polite">
        {tasks.map((task) => (
          <article key={task.id} className="card">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium">{t("history.id", { id: task.id.slice(0, 8) })}</p>
              <StatusBadge status={task.status} />
            </div>
            <dl className="mt-3 grid gap-1 text-sm text-zinc-600 sm:grid-cols-2">
              <div>
                {t("history.pair", {
                  label: t("history.mode"),
                  value: t(`modes.${task.mode}`, { defaultValue: task.mode }),
                })}
              </div>
              {task.template_id ? (
                <div>
                  {t("history.pair", {
                    label: t("history.template"),
                    value: t(`templates.${task.template_id}.title`, { defaultValue: task.template_id }),
                  })}
                </div>
              ) : null}
              <div>{t("history.duration", { seconds: formatSeconds(task.audio_duration_sec) })}</div>
              <div>{t("history.offset", { value: task.offset_ms })}</div>
              <div className="sm:col-span-2">{t("history.created", { time: formatTime(task.created_at, language) })}</div>
            </dl>
            {task.error_code ? (
              <p className="error mt-3">
                {t(`errors.${task.error_code}`, {
                  defaultValue: t("errors.UNKNOWN"),
                  max: 30,
                  seconds: formatSeconds(task.audio_duration_sec),
                  size: megabytes(FALLBACK_LIMITS.maxImageBytes),
                })}
              </p>
            ) : null}
            {task.status === "succeeded" ? (
              <button
                type="button"
                className="btn mt-4"
                disabled={busyId === task.id}
                onClick={() => onDownload(task)}
              >
                {busyId === task.id ? t("history.downloading") : t("history.download")}
              </button>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}
