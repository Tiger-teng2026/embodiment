import { Outlet, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AgreementPage from "./pages/AgreementPage";
import CreatePage from "./pages/CreatePage";
import HistoryPage from "./pages/HistoryPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";

function Frame() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Frame />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/agreement" element={<AgreementPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <CreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
