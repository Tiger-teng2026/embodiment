import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const SECTIONS = ["s1", "s2", "s3", "s4", "s5", "s6"];

export default function AgreementPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  return (
    <article className="card mx-auto max-w-3xl">
      <h1 className="text-lg font-semibold">{t("agreement.title")}</h1>
      <p className="hint mt-3">{t("agreement.intro")}</p>
      <div className="mt-6 grid gap-5">
        {SECTIONS.map((key) => (
          <section key={key}>
            <h2 className="text-sm font-medium">{t(`agreement.${key}Title`)}</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-700">{t(`agreement.${key}Body`)}</p>
          </section>
        ))}
      </div>
      <Link to={user ? "/" : "/login"} className="btn mt-6">
        {user ? t("notFound.action") : t("login.title")}
      </Link>
    </article>
  );
}
