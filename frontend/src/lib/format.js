export function formatSeconds(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return number.toFixed(number >= 10 ? 1 : 2);
}

export function formatTime(iso, language) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
