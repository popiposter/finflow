import type { ApiErrorShape } from "@/shared/api/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

type RequestOptions = {
  retryOnUnauthorized?: boolean;
};

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, payload: unknown, fallbackMessage: string) {
    const detail = resolveErrorMessage(payload) ?? fallbackMessage;
    super(detail);
    this.status = status;
    this.payload = payload;
  }
}

let refreshInFlight: Promise<boolean> | null = null;

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const { retryOnUnauthorized = true } = options;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: buildHeaders(init.headers, init.body),
  });

  if (
    response.status === 401 &&
    retryOnUnauthorized &&
    shouldRetryUnauthorized(path)
  ) {
    const refreshed = await refreshSession();

    if (refreshed) {
      return apiFetch<T>(path, init, { retryOnUnauthorized: false });
    }
  }

  if (!response.ok) {
    throw new ApiError(
      response.status,
      await readBody(response),
      `${init.method ?? "GET"} ${path} failed`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await readBody(response)) as T;
}

export function toQueryString(params: Record<string, string | number | boolean | undefined | null>) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    searchParams.set(key, String(value));
  });

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function refreshSession() {
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        refreshInFlight = null;
      });
  }

  return refreshInFlight;
}

async function readBody(response: Response) {
  const contentType = response.headers.get("content-type");

  if (contentType?.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

function buildHeaders(headers: HeadersInit | undefined, body: BodyInit | null | undefined) {
  const nextHeaders = new Headers(headers);

  if (!nextHeaders.has("Accept")) {
    nextHeaders.set("Accept", "application/json");
  }

  if (body && !(body instanceof FormData) && !nextHeaders.has("Content-Type")) {
    nextHeaders.set("Content-Type", "application/json");
  }

  return nextHeaders;
}

function shouldRetryUnauthorized(path: string) {
  return path === "/auth/me" || !path.startsWith("/auth/");
}

function resolveErrorMessage(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const maybeError = payload as ApiErrorShape;
  return maybeError.detail ?? maybeError.message ?? maybeError.error ?? null;
}
