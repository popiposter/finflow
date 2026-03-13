import type { ApiErrorShape } from "@/shared/api/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

type RequestOptions = {
  retryOnUnauthorized?: boolean;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string>;
  readonly payload: unknown;

  constructor(
    status: number,
    payload: unknown,
    fallbackMessage: string,
    code?: string,
    fields?: Record<string, string>,
  ) {
    const detail = resolveErrorMessage(payload) ?? fallbackMessage;
    super(detail);
    this.status = status;
    this.code = code ?? resolveErrorCode(payload) ?? defaultErrorCode(status);
    this.fields = fields ?? resolveErrorFields(payload);
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

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: buildHeaders(init.headers, init.body),
    });
  } catch (error) {
    throw new ApiError(0, error, "Network request failed", "network_error");
  }

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
    const payload = await readBody(response);
    throw new ApiError(
      response.status,
      payload,
      `${init.method ?? "GET"} ${path} failed`,
      resolveErrorCode(payload) ?? defaultErrorCode(response.status),
      resolveErrorFields(payload),
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
  if (maybeError.error && typeof maybeError.error === "object" && "message" in maybeError.error) {
    return typeof maybeError.error.message === "string" ? maybeError.error.message : null;
  }
  return maybeError.detail ?? maybeError.message ?? (typeof maybeError.error === "string" ? maybeError.error : null);
}

function resolveErrorCode(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const maybeError = payload as ApiErrorShape;
  if (maybeError.error && typeof maybeError.error === "object" && "code" in maybeError.error) {
    return typeof maybeError.error.code === "string" ? maybeError.error.code : null;
  }

  return null;
}

function resolveErrorFields(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return {};
  }

  const maybeError = payload as ApiErrorShape;
  if (maybeError.error && typeof maybeError.error === "object" && "fields" in maybeError.error) {
    const fields = maybeError.error.fields;
    if (fields && typeof fields === "object") {
      return Object.fromEntries(
        Object.entries(fields as Record<string, unknown>).map(([key, value]) => [key, String(value)]),
      );
    }
  }

  return {};
}

function defaultErrorCode(status: number) {
  if (status === 0) {
    return "network_error";
  }
  if (status === 401) {
    return "authentication_required";
  }
  if (status === 403) {
    return "permission_denied";
  }
  if (status === 404) {
    return "not_found";
  }
  if (status === 409) {
    return "conflict";
  }
  if (status === 422) {
    return "validation_error";
  }
  if (status >= 500) {
    return "internal_error";
  }
  return "request_failed";
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
