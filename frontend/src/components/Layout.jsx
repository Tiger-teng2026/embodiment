import { useEffect } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitch from "./LanguageSwitch";
import { isMockBackend } from "../api/env";
import { useAuth } from "../auth/AuthContext";

function navClass({ isActive }) {
  return isActive ? "font-medium text-zinc-900" : "text-zinc-500";
}

export default function Layout({ children }) {
  const { t, i18n } = useTranslation();
  const { user, ready, logout } = useAuth();
  const location = useLocation();
  const onLogin = location.pathname === "/login";

  useEffect(() => {
    document.title = `${t("app.name")} ${t("app.nameEn")}`;
    document.documentElement.lang = i18n.language?.startsWith("en") ? "en" : "zh-CN";
  }, [t, i18n.language]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex min-h-14 w-full max-w-5xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2">
          <Link to={user ? "/" : "/login"} className="flex shrink-0 items-baseline gap-2">
            <span className="text-base font-semibold">{t("app.name")}</span>
            <span className="hidden text-sm text-zinc-500 sm:inline">{t("app.nameEn")}</span>
          </Link>
          {ready && user ? (
            <nav className="flex items-center gap-3 text-sm">
              <NavLink to="/" end className={navClass}>
                {t("nav.create")}
              </NavLink>
              <NavLink to="/history" className={navClass}>
                {t("nav.history")}
              </NavLink>
            </nav>
          ) : null}
          <div className="flex-1" />
          {ready && user ? (
            <button type="button" className="shrink-0 text-sm text-zinc-500" onClick={logout}>
              {t("nav.logout")}
            </button>
          ) : null}
          {ready && !user && !onLogin ? (
            <Link to="/login" className="shrink-0 text-sm text-zinc-500">
              {t("login.title")}
            </Link>
          ) : null}
          <LanguageSwitch />
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        {isMockBackend ? (
          <p className="mb-3 text-center text-xs text-zinc-500">【当前模拟调试模式，不会生成真实分身视频】</p>
        ) : null}
        {children}
      </main>
      <footer className="mx-auto flex w-full max-w-5xl flex-col gap-2 px-4 py-8 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
        <p>{t("app.watermark")}</p>
        <Link to="/agreement" className="underline underline-offset-2">
          {t("footer.agreement")}
        </Link>
      </footer>
    </div>
  );
}
