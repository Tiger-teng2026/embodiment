import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <section className="card mx-auto max-w-md">
      <h1 className="text-lg font-semibold">{t("notFound.title")}</h1>
      <Link to="/" className="btn mt-4">
        {t("notFound.action")}
      </Link>
    </section>
  );
}
