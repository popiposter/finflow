import type { IntlShape } from "react-intl";

import type {
  AccountType,
  CashflowLedgerMode,
  CategoryType,
  ProjectedTransactionStatus,
  Recurrence,
  TransactionType,
} from "@/shared/api/types";

export function accountTypeLabel(intl: IntlShape, type: AccountType) {
  return intl.formatMessage({ id: `accounts.type.${type}` });
}

export function categoryTypeLabel(intl: IntlShape, type: CategoryType) {
  return intl.formatMessage({ id: `categories.type.${type}` });
}

export function recurrenceLabel(intl: IntlShape, recurrence: Recurrence) {
  return intl.formatMessage({ id: `plans.recurrence.${recurrence}` });
}

export function transactionTypeLabel(intl: IntlShape, type: TransactionType) {
  return intl.formatMessage({ id: `transactions.type.${type}` });
}

export function projectionStatusLabel(
  intl: IntlShape,
  status: ProjectedTransactionStatus | string,
) {
  if (status !== "pending" && status !== "confirmed" && status !== "skipped") {
    return status;
  }

  return intl.formatMessage({ id: `status.${status}` });
}

export function ledgerModeLabel(intl: IntlShape, mode: CashflowLedgerMode) {
  return intl.formatMessage({ id: `reports.mode.${mode}` });
}
