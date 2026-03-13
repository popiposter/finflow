import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TransactionsPage } from "@/features/transactions/TransactionsPage";
import { renderWithProviders } from "@/test/test-utils";

let isOnline = true;

const account = {
  id: "acc-1",
  user_id: "user-1",
  name: "Main checking",
  type: "checking" as const,
  description: null,
  current_balance: "2400.00",
  currency_code: "USD",
  is_active: true,
  opened_at: null,
  closed_at: null,
  created_at: "",
  updated_at: "",
};

const category = {
  id: "cat-1",
  user_id: "user-1",
  name: "Groceries",
  type: "expense" as const,
  description: null,
  parent_id: null,
  is_active: true,
  display_order: 0,
  created_at: "",
  updated_at: "",
};

const listAccounts = vi.fn();
const listCategories = vi.fn();
const listTransactions = vi.fn();
const createTransaction = vi.fn();
const patchTransaction = vi.fn();
const deleteTransaction = vi.fn();
const parseAndCreateTransaction = vi.fn();
const importTransactionsWorkbook = vi.fn();

const sampleTransaction = {
  id: "txn-1",
  user_id: "user-1",
  account_id: "acc-1",
  category_id: "cat-1",
  counterparty_account_id: null,
  amount: "84.50",
  type: "expense" as const,
  description: "Groceries",
  date_accrual: "2026-03-01T00:00:00Z",
  date_cash: "2026-03-01T00:00:00Z",
  is_reconciled: false,
  planned_payment_id: null,
  projected_transaction_id: null,
  created_at: "",
  updated_at: "",
};

vi.mock("@/shared/lib/offline", () => ({
  useOnlineStatus: () => isOnline,
}));

vi.mock("@/shared/api/accounts", () => ({
  listAccounts: () => listAccounts(),
}));

vi.mock("@/shared/api/categories", () => ({
  listCategories: () => listCategories(),
}));

vi.mock("@/shared/api/transactions", () => ({
  listTransactions: () => listTransactions(),
  createTransaction: (payload: unknown) => createTransaction(payload),
  patchTransaction: (transactionId: string, payload: unknown) =>
    patchTransaction(transactionId, payload),
  deleteTransaction: (transactionId: string) => deleteTransaction(transactionId),
  parseAndCreateTransaction: (payload: unknown) => parseAndCreateTransaction(payload),
  importTransactionsWorkbook: (payload: unknown) => importTransactionsWorkbook(payload),
}));

describe("TransactionsPage", () => {
  beforeEach(() => {
    isOnline = true;
    listAccounts.mockResolvedValue([account]);
    listCategories.mockResolvedValue([category]);
    listTransactions.mockResolvedValue([]);
    createTransaction.mockResolvedValue({ id: "txn-1" });
    patchTransaction.mockResolvedValue({ id: "txn-1" });
    deleteTransaction.mockResolvedValue(undefined);
    parseAndCreateTransaction.mockResolvedValue({ id: "txn-2" });
    importTransactionsWorkbook.mockResolvedValue({
      imported_count: 1,
      imported_transaction_ids: ["txn-3"],
      skipped_count: 0,
      errors: [],
    });
    vi.clearAllMocks();
  });

  it("blocks create and parse actions when offline", async () => {
    isOnline = false;

    renderWithProviders(<TransactionsPage />);

    await waitFor(() => expect(listAccounts).toHaveBeenCalled());

    expect(screen.getByRole("button", { name: /new transaction/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /parse transaction/i })).toBeDisabled();
  });

  it("hydrates the quick-capture form with the first available account", async () => {
    renderWithProviders(<TransactionsPage />);

    await waitFor(() => expect(listAccounts).toHaveBeenCalled());

    await waitFor(() => {
      expect(screen.getAllByLabelText(/^Account$/i)[0]).toHaveValue("acc-1");
    });

    expect(screen.getByRole("button", { name: /parse transaction/i })).toBeEnabled();
  });

  it("filters desktop table by search text", async () => {
    const user = userEvent.setup();

    listTransactions.mockResolvedValue([
      sampleTransaction,
      {
        ...sampleTransaction,
        id: "txn-2",
        category_id: null,
        amount: "2800.00",
        type: "income",
        description: "Salary",
        date_cash: "2026-03-03T00:00:00Z",
      },
    ]);

    renderWithProviders(<TransactionsPage />);

    await waitFor(() => expect(listTransactions).toHaveBeenCalled());

    expect(await screen.findByText(/2 recorded transactions\./i)).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getAllByText("Groceries").length).toBeGreaterThan(0);
    expect(within(table).getByText("Salary")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Search$/i), "Salary");

    await waitFor(() => {
      expect(within(table).queryByText("Groceries")).not.toBeInTheDocument();
      expect(within(table).getByText("Salary")).toBeInTheDocument();
    });
  });

  it("hydrates table filters from URL query params", async () => {
    listTransactions.mockResolvedValue([
      sampleTransaction,
      {
        ...sampleTransaction,
        id: "txn-2",
        category_id: null,
        amount: "2800.00",
        type: "income",
        description: "Salary",
        date_cash: "2026-03-03T00:00:00Z",
      },
    ]);

    renderWithProviders(<TransactionsPage />, {
      route: "/transactions?q=Salary&type=income&sort=amount:asc",
    });

    await waitFor(() => expect(listTransactions).toHaveBeenCalled());

    expect(screen.getByLabelText(/^Search$/i)).toHaveValue("Salary");
    expect(screen.getByLabelText(/^Type$/i)).toHaveValue("income");

    const table = screen.getByRole("table");
    await waitFor(() => {
      expect(within(table).queryByText("Groceries")).not.toBeInTheDocument();
      expect(within(table).getAllByText("Salary").length).toBeGreaterThan(0);
    });
  });

  it("uploads a workbook for the selected account", async () => {
    const user = userEvent.setup();

    renderWithProviders(<TransactionsPage />);

    await waitFor(() => expect(listAccounts).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: /import xlsx/i }));

    const file = new File(["mock workbook"], "transactions.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    await user.upload(screen.getByLabelText(/workbook file/i), file);
    await user.click(screen.getByRole("button", { name: /import transactions/i }));

    await waitFor(() =>
      expect(importTransactionsWorkbook).toHaveBeenCalledWith({
        account_id: "acc-1",
        file,
      }),
    );

    expect(
      await screen.findByText(/1 transactions imported\./i),
    ).toBeInTheDocument();
  });
});
