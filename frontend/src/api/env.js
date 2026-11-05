const raw = import.meta.env.VITE_BACKEND_API_URL;
const trimmed = raw === undefined || raw === null ? "" : String(raw).trim();

/** Backend origin, or the literal "mock" when the UI should not call a server. */
export const backendApiUrl = trimmed === "" ? "mock" : trimmed;

export const isMockBackend = backendApiUrl === "mock";

export function apiOrigin() {
  if (isMockBackend) return "";
  return backendApiUrl.replace(/\/$/, "");
}
