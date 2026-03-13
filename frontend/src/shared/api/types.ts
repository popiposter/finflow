export type UUID = string;

export type AccountType =
  | "checking"
  | "savings"
  | "credit_card"
  | "cash"
  | "investment"
  | "loan"
  | "other";

export type CategoryType = "income" | "expense";

export type TransactionType =
  | "payment"
  | "refund"
  | "transfer"
  | "income"
  | "expense"
  | "adjustment";

export type Recurrence = "daily" | "weekly" | "monthly";

export type ProjectedTransactionStatus = "pending" | "confirmed" | "skipped";
export type ProjectedTransactionType = "income" | "expense";

export type CashflowLedgerMode = "mixed" | "actual_only" | "planned_only";
export type CashflowRowType = "actual" | "projected";
export type ReportGroupBy = "by_category" | "by_type";

export type User = {
  id: UUID;
  email: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type RegisterInput = LoginInput;

export type Account = {
  id: UUID;
  user_id: UUID;
  name: string;
  type: AccountType;
  description: string | null;
  current_balance: string | null;
  currency_code: string;
  is_active: boolean;
  opened_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AccountInput = {
  name: string;
  type: AccountType;
  description?: string | null;
  current_balance?: string | null;
  currency_code?: string;
  is_active?: boolean;
  opened_at?: string | null;
  closed_at?: string | null;
};

export type Category = {
  id: UUID;
  user_id: UUID | null;
  name: string;
  type: CategoryType;
  description: string | null;
  parent_id: UUID | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
};

export type CategoryInput = {
  name: string;
  type: CategoryType;
  description?: string | null;
  parent_id?: UUID | null;
  is_active?: boolean;
  display_order?: number;
};

export type Transaction = {
  id: UUID;
  user_id: UUID;
  account_id: UUID;
  category_id: UUID | null;
  counterparty_account_id: UUID | null;
  amount: string;
  type: TransactionType;
  description: string | null;
  date_accrual: string;
  date_cash: string;
  is_reconciled: boolean;
  planned_payment_id: UUID | null;
  projected_transaction_id: UUID | null;
  created_at: string;
  updated_at: string;
};

export type TransactionInput = {
  account_id: UUID;
  category_id?: UUID | null;
  counterparty_account_id?: UUID | null;
  amount: string;
  type: TransactionType;
  description?: string | null;
  date_accrual: string;
  date_cash: string;
  is_reconciled?: boolean;
};

export type TransactionPatchInput = Partial<
  Pick<
    TransactionInput,
    "amount" | "category_id" | "description" | "date_accrual" | "date_cash" | "is_reconciled"
  >
>;

export type TransactionWorkbookImportInput = {
  account_id: UUID;
  file: File;
};

export type TransactionImportError = {
  row_number: number;
  message: string;
};

export type TransactionWorkbookImportResponse = {
  imported_count: number;
  imported_transaction_ids: UUID[];
  skipped_count: number;
  errors: TransactionImportError[];
};

export type ParseCreateInput = {
  text: string;
  account_id: UUID;
  category_id?: UUID | null;
};

export type PlannedPayment = {
  id: UUID;
  user_id: UUID;
  account_id: UUID;
  category_id: UUID | null;
  amount: string;
  description: string | null;
  recurrence: Recurrence;
  start_date: string;
  end_date: string | null;
  next_due_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PlannedPaymentInput = {
  account_id: UUID;
  category_id?: UUID | null;
  amount: string;
  description?: string | null;
  recurrence: Recurrence;
  start_date: string;
  end_date?: string | null;
  next_due_at?: string | null;
  is_active?: boolean;
};

export type ProjectionGenerationResult = {
  planned_payment_id: UUID;
  generated_projections: UUID[];
  next_due_at: string;
  skipped_occurrences: number;
};

export type ProjectedTransaction = {
  id: UUID;
  planned_payment_id: UUID;
  origin_date: string;
  origin_amount: string;
  origin_description: string | null;
  origin_category_id: UUID | null;
  type: ProjectedTransactionType;
  projected_date: string;
  projected_amount: string;
  projected_description: string | null;
  projected_category_id: UUID | null;
  status: ProjectedTransactionStatus;
  transaction_id: UUID | null;
  resolved_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

export type ProjectedTransactionUpdateInput = {
  projected_amount?: string;
  projected_date?: string;
  projected_description?: string | null;
  projected_category_id?: UUID | null;
};

export type ProjectedTransactionConfirmInput = {
  amount?: string;
  date?: string;
  description?: string | null;
  category_id?: UUID | null;
};

export type ProjectedTransactionConfirmResponse = {
  projected_transaction: ProjectedTransaction;
  transaction_id: UUID;
};

export type CashflowRow = {
  row_type: CashflowRowType;
  row_id: UUID;
  date: string;
  description: string | null;
  amount: string;
  type: string;
  status: string;
  balance_after: string;
  planned_payment_id: UUID | null;
  projected_transaction_id: UUID | null;
  transaction_id: UUID | null;
};

export type CashflowLedgerReport = {
  opening_balance: string;
  closing_balance: string;
  rows: CashflowRow[];
};

export type CashflowForecast = {
  current_balance: string;
  projected_income: string;
  projected_expense: string;
  projected_balance: string;
  pending_count: number;
};

export type ReportCategoryTotal = {
  category_id: UUID | null;
  category_name: string | null;
  total: string;
  type: CategoryType;
};

export type ReportTypeTotal = {
  type: TransactionType;
  total: string;
};

export type PnlReport = {
  date_accrual_start: string;
  date_accrual_end: string;
  totals_by_category: ReportCategoryTotal[];
  totals_by_type: ReportTypeTotal[];
  grand_total: string;
};

export type CashflowReport = {
  date_cash_start: string;
  date_cash_end: string;
  totals_by_category: ReportCategoryTotal[];
  totals_by_type: ReportTypeTotal[];
  grand_total: string;
};

export type ApiErrorShape = {
  detail?: string;
  message?: string;
  error?: string;
};
