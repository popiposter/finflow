import { apiFetch } from "@/shared/api/client";
import type { Account, AccountInput, UUID } from "@/shared/api/types";

export function listAccounts() {
  return apiFetch<Account[]>("/accounts");
}

export function createAccount(payload: AccountInput) {
  return apiFetch<Account>("/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAccount(accountId: UUID, payload: AccountInput) {
  return apiFetch<Account>(`/accounts/${accountId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteAccount(accountId: UUID) {
  return apiFetch<void>(`/accounts/${accountId}`, {
    method: "DELETE",
  });
}
