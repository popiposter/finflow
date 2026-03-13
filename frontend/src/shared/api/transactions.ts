import { apiFetch } from "@/shared/api/client";
import type {
  ParseCreateInput,
  Transaction,
  TransactionInput,
  TransactionWorkbookImportInput,
  TransactionWorkbookImportResponse,
  TransactionPatchInput,
  UUID,
} from "@/shared/api/types";

export function listTransactions() {
  return apiFetch<Transaction[]>("/transactions");
}

export function createTransaction(payload: TransactionInput) {
  return apiFetch<Transaction>("/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function patchTransaction(transactionId: UUID, payload: TransactionPatchInput) {
  return apiFetch<Transaction>(`/transactions/${transactionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTransaction(transactionId: UUID) {
  return apiFetch<void>(`/transactions/${transactionId}`, {
    method: "DELETE",
  });
}

export function parseAndCreateTransaction(payload: ParseCreateInput) {
  return apiFetch<Transaction>("/transactions/parse-and-create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function importTransactionsWorkbook(payload: TransactionWorkbookImportInput) {
  const formData = new FormData();
  formData.set("account_id", payload.account_id);
  formData.set("file", payload.file);

  return apiFetch<TransactionWorkbookImportResponse>("/transactions/import", {
    method: "POST",
    body: formData,
  });
}
