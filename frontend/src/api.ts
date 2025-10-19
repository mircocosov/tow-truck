export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1/";

export const WS_BASE =
  import.meta.env.VITE_WS_BASE_URL ?? "ws://127.0.0.1:8000/";

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiError extends Error {
  status?: number;
  payload?: unknown;
}

export function resolveUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) {
    return pathOrUrl;
  }
  return new URL(pathOrUrl, API_BASE).toString();
}

export async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export function createApiError(
  message: string,
  status?: number,
  payload?: unknown,
): ApiError {
  const error = new Error(message) as ApiError;
  error.status = status;
  error.payload = payload;
  return error;
}
