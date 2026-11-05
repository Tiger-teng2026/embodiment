import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { t } = useTranslation();
  const { user, ready, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorCode, setErrorCode] = useState("");
  const [pending, setPending] = useState(false);

  if (!ready) return <p className="text-sm text-zinc-500">{t("common.loading")}</p>;
  if (user) return <Navigate to="/" replace />;

  async function onSubmit(event) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setErrorCode("MISSING_FIELDS");
      return;
    }
    setPending(true);
    setErrorCode("");
    try {
      await login(username.trim(), password);
    } catch (error) {
      setErrorCode(error instanceof ApiError ? error.code : "NETWORK");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card mx-auto max-w-md" onSubmit={onSubmit}>
      <h1 className="text-lg font-semibold">{t("login.title")}</h1>
      <p className="hint mt-2">{t("login.subtitle")}</p>
      <label className="mt-5 block">
        <span className="label">{t("login.username")}</span>
        <input
          className="input"
          name="username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
      </label>
      <label className="mt-4 block">
        <span className="label">{t("login.password")}</span>
        <input
          className="input"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>
      {errorCode ? (
        <p className="error mt-4" role="alert">
          {t(`errors.${errorCode}`, { defaultValue: t("errors.UNKNOWN") })}
        </p>
      ) : null}
      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button className="btn w-full sm:w-auto" type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("login.action")}
        </button>
        <Link to="/agreement" className="text-sm text-zinc-500 underline underline-offset-2">
          {t("footer.agreement")}
        </Link>
      </div>
    </form>
  );
}
