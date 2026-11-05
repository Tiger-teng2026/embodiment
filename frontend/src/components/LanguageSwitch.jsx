import { useTranslation } from "react-i18next";
import { setLanguage } from "../i18n";

export default function LanguageSwitch() {
  const { i18n, t } = useTranslation();
  const current = i18n.resolvedLanguage?.startsWith("en") ? "en" : "zh";
  const item = (active) => (active ? "font-medium text-zinc-900" : "text-zinc-400");

  return (
    <div className="flex shrink-0 items-center gap-2 text-sm" role="group" aria-label={t("lang.switchLabel")}>
      <button type="button" className={item(current === "zh")} aria-pressed={current === "zh"} onClick={() => setLanguage("zh")}>
        {t("lang.zh")}
      </button>
      <span className="text-zinc-300" aria-hidden="true">
        |
      </span>
      <button type="button" className={item(current === "en")} aria-pressed={current === "en"} onClick={() => setLanguage("en")}>
        {t("lang.en")}
      </button>
    </div>
  );
}
