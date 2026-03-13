import { apiFetch } from "@/shared/api/client";
import type { LoginInput, RegisterInput, User } from "@/shared/api/types";

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
