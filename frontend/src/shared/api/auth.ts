import { apiFetch } from "@/shared/api/client";
import type {
  ApiToken,
  ApiTokenWithRawToken,
  IntegrationStatusResponse,
  LoginInput,
  RegisterInput,
  TelegramChatLink,
  User,
} from "@/shared/api/types";

export function registerUser(payload: RegisterInput) {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginWithPassword(payload: LoginInput) {
  return apiFetch<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser() {
  return apiFetch<User>("/auth/me");
}

export function logoutCurrentSession() {
  return apiFetch<{ message: string }>("/auth/logout", {
    method: "POST",
  });
}

export function listApiTokens() {
  return apiFetch<ApiToken[]>("/auth/api-tokens");
}

export function createApiToken(payload: { name: string }) {
  return apiFetch<ApiTokenWithRawToken>("/auth/api-tokens", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function revokeApiToken(tokenId: string) {
  return apiFetch<ApiToken>(`/auth/api-tokens/${tokenId}`, {
    method: "DELETE",
  });
}

export function listTelegramLinks() {
  return apiFetch<TelegramChatLink[]>("/auth/telegram-links");
}

export function disconnectTelegramLink(linkId: string) {
  return apiFetch<TelegramChatLink>(`/auth/telegram-links/${linkId}`, {
    method: "DELETE",
  });
}

export function updateTelegramLink(linkId: string, payload: { account_id: string }) {
  return apiFetch<TelegramChatLink>(`/auth/telegram-links/${linkId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getIntegrationStatus() {
  return apiFetch<IntegrationStatusResponse>("/health/integrations");
}
