import axios, { type AxiosResponse } from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface ApiEnvelope<T = unknown> {
  success: boolean;
  message: string;
  data: T;
  errors?: unknown[] | null;
}

/** Extract the inner `data` field from a standard API envelope response. */
export function unwrapEnvelope<T>(response: AxiosResponse<ApiEnvelope<T>>): T {
  return response.data.data;
}

/** Extract a list from paginated or plain list envelope responses. */
export function unwrapList<T>(response: AxiosResponse<ApiEnvelope<unknown>>): T[] {
  const payload = response.data?.data;
  return Array.isArray(payload) ? (payload as T[]) : [];
}

/**
 * Dashboard `/dashboard/hospitals` returns `{ totals, hospitals: [...] }`
 * rather than a bare array — normalize that here.
 */
export function unwrapDashboardHospitals<T>(
  response: AxiosResponse<ApiEnvelope<unknown>>,
): T[] {
  const payload = response.data?.data;
  if (Array.isArray(payload)) {
    return payload as T[];
  }
  if (payload && typeof payload === "object" && "hospitals" in payload) {
    const hospitals = (payload as { hospitals?: unknown }).hospitals;
    return Array.isArray(hospitals) ? (hospitals as T[]) : [];
  }
  return [];
}

/** Turn FastAPI / axios error payloads into a readable string. */
export function formatApiError(error: unknown, fallback = "Request failed."): string {
  if (!error || typeof error !== "object" || !("response" in error)) {
    return fallback;
  }
  const detail = (error as { response?: { data?: { detail?: unknown; message?: string } } })
    .response?.data;
  if (!detail) return fallback;
  if (typeof detail.message === "string") return detail.message;
  const raw = detail.detail;
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    return raw
      .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)))
      .join(" ");
  }
  return fallback;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to attach JWT token from localStorage to outgoing requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("resqmesh_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("resqmesh_token");
    }
    return Promise.reject(error);
  }
);

