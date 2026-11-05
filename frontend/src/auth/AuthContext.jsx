import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setToken, TOKEN_KEY } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setReady(true);
      return;
    }
    let cancelled = false;
    api("/api/auth/me")
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch(() => setToken(null))
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      async login(username, password) {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: { username, password },
          auth: false,
        });
        setToken(data.access_token);
        const me = await api("/api/auth/me");
        setUser(me);
      },
      logout() {
        setToken(null);
        setUser(null);
      },
    }),
    [user, ready],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("AuthProvider missing");
  return ctx;
}
