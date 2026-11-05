import axios from "axios";
import { apiOrigin, isMockBackend } from "./env";
import { mockDispatch } from "./mock";

export { isMockBackend };

export const TOKEN_KEY = "embodiment_token";

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(code, status, detail) {
    super(code);
    this.code = code;
    this.status = status;
    this.detail = detail || {};
  }
}

const http = axios.create({
  baseURL: apiOrigin(),
  timeout: 60000,
});

http.interceptors.request.use((config) => {
  if (!config.skipAuth) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  if (typeof FormData !== "undefined" && config.data instanceof FormData && typeof config.headers?.delete === "function") {
    config.headers.delete("Content-Type");
  }
  return config;
});

if (isMockBackend) {
  http.defaults.adapter = async (config) => {
    const result = await mockDispatch(config);
    const response = {
      data: result.data ?? { detail: result.detail },
      status: result.status,
      statusText: result.status >= 400 ? "Error" : "OK",
      headers: {},
      config,
    };
    if (result.status >= 400) {
      const error = new axios.AxiosError(
        result.detail?.code || "Error",
        String(result.status),
        config,
        null,
        response,
      );
      return Promise.reject(error);
    }
    return response;
  };
}

function errorFromAxios(error, skipAuth) {
  const status = error.response?.status || 0;
  const detail = error.response?.data?.detail;
  const payload = detail && typeof detail === "object" ? detail : {};
  const code = payload.code || (status >= 500 || status === 0 ? "NETWORK" : "UNKNOWN");
  if (status === 401 && !skipAuth) {
    setToken(null);
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
  }
  return new ApiError(code, status, payload);
}

export async function api(path, options = {}) {
  const skipAuth = options.auth === false;
  try {
    const response = await http.request({
      url: path,
      method: options.method || "GET",
      data: options.form ?? options.body,
      skipAuth,
    });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (axios.isAxiosError(error)) throw errorFromAxios(error, skipAuth);
    throw new ApiError("NETWORK", 0, {});
  }
}
