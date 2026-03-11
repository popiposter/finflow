import { apiFetch, toQueryString } from "@/shared/api/client";
import type {
  PlannedPayment,
  PlannedPaymentInput,
  ProjectionGenerationResult,
  UUID,
} from "@/shared/api/types";

export function listPlans() {
  return apiFetch<PlannedPayment[]>("/planned-payments");
}

export function createPlan(payload: PlannedPaymentInput) {
  return apiFetch<PlannedPayment>("/planned-payments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePlan(planId: UUID, payload: PlannedPaymentInput) {
  return apiFetch<PlannedPayment>(`/planned-payments/${planId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deletePlan(planId: UUID) {
  return apiFetch<void>(`/planned-payments/${planId}`, {
    method: "DELETE",
  });
}

export function generateDueProjections(asOfDate?: string) {
  return apiFetch<ProjectionGenerationResult[]>(
    `/planned-payments/generate${toQueryString({ as_of_date: asOfDate })}`,
    {
      method: "POST",
    },
  );
}
