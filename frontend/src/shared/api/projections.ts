import { apiFetch, toQueryString } from "@/shared/api/client";
import type {
  ProjectedTransaction,
  ProjectedTransactionConfirmInput,
  ProjectedTransactionConfirmResponse,
  ProjectedTransactionStatus,
  ProjectedTransactionUpdateInput,
  UUID,
} from "@/shared/api/types";

type ProjectionFilter = {
  status?: ProjectedTransactionStatus | "";
  from?: string;
  to?: string;
};

export function listProjectedTransactions(filters: ProjectionFilter = {}) {
  return apiFetch<ProjectedTransaction[]>(
    `/projected-transactions${toQueryString(filters)}`,
  );
}

export function updateProjectedTransaction(
  projectionId: UUID,
  payload: ProjectedTransactionUpdateInput,
) {
  return apiFetch<ProjectedTransaction>(`/projected-transactions/${projectionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function confirmProjectedTransaction(
  projectionId: UUID,
  payload: ProjectedTransactionConfirmInput = {},
) {
  return apiFetch<ProjectedTransactionConfirmResponse>(
    `/projected-transactions/${projectionId}/confirm`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function skipProjectedTransaction(projectionId: UUID) {
  return apiFetch<ProjectedTransaction>(
    `/projected-transactions/${projectionId}/skip`,
    {
      method: "POST",
    },
  );
}
