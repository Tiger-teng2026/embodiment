import { useTranslation } from "react-i18next";

const STYLES = {
  queued: "border-zinc-300 text-zinc-600",
  processing: "border-zinc-900 text-zinc-900",
  succeeded: "border-zinc-900 bg-zinc-900 text-white",
  failed: "border-red-200 text-red-700",
};

export default function StatusBadge({ status }) {
  const { t } = useTranslation();
  const style = STYLES[status] || STYLES.queued;
  return (
    <span className={`inline-flex h-6 items-center rounded-full border px-2 text-xs ${style}`}>
      {t(`status.${status}`, { defaultValue: status })}
    </span>
  );
}
