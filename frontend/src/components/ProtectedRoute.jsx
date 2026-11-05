import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, ready } = useAuth();
  const { t } = useTranslation();
  if (!ready) return <p className="text-sm text-zinc-500">{t("common.loading")}</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
