import axios, { AxiosError } from "axios";

export const api = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  withCredentials: true,
});

export function errorMessage(err: unknown): string {
  const detail = (err as AxiosError<{ detail?: unknown }>)?.response?.data?.detail;
  if (!detail) return (err as Error)?.message || "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d?.msg || JSON.stringify(d)).join(" ");
  if (typeof detail === "object" && detail && "message" in detail) return String((detail as { message: string }).message);
  return JSON.stringify(detail);
}

export const get = async <T,>(path: string): Promise<T> => (await api.get<T>(path)).data;
export const post = async <T,>(path: string, body?: unknown): Promise<T> => (await api.post<T>(path, body)).data;
export const put = async <T,>(path: string, body?: unknown): Promise<T> => (await api.put<T>(path, body)).data;
export const patch = async <T,>(path: string, body?: unknown): Promise<T> => (await api.patch<T>(path, body)).data;
