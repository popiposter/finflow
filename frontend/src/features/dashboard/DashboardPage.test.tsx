import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { renderWithProviders } from "@/test/test-utils";

const listAccounts = vi.fn();
const listCategories = vi.fn();
const getForecast = vi.fn();
const getLedgerReport = vi.fn();
const listProjectedTransactions = vi.fn();
const parseAndCreateTransaction = vi.fn();
const generateDueProjections = vi.fn();

vi.mock("@/shared/lib/offline", () => ({
  useOnlineStatus: () => true,
}));

vi.mock("@/shared/api/accounts", () => ({
  listAccounts: () => listAccounts(),
}));

vi.mock("@/shared/api/categories", () => ({
  listCategories: () => listCategories(),
}));

vi.mock("@/shared/api/reports", () => ({
  getForecast: (targetDate?: string) => getForecast(targetDate),
  getLedgerReport: (params: unknown) => getLedgerReport(params),
}));

vi.mock("@/shared/api/projections", () => ({
  listProjectedTransactions: (filters: unknown) => listProjectedTransactions(filters),
}));

vi.mock("@/shared/api/transactions", () => ({
  parseAndCreateTransaction: (payload: unknown) => parseAndCreateTransaction(payload),
}));

vi.mock("@/shared/api/plans", () => ({
  generateDueProjections: (asOfDate?: string) => generateDueProjections(asOfDate),
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listAccounts.mockResolvedValue([
      {
        id: "acc-1",
        user_id: "user-1",
        name: "Main checking",
        type: "checking",
        description: null,
        current_balance: "2400.00",
        currency_code: "USD",
        is_active: true,
        opened_at: null,
        closed_at: null,
        created_at: "",
        updated_at: "",
      },
    ]);
    listCategories.mockResolvedValue([
      {
        id: "cat-1",
        user_id: "user-1",
        name: "Salary",
        type: "income",
        description: null,
        parent_id: null,
        is_active: true,
        display_order: 0,
        created_at: "",
        updated_at: "",
      },
    ]);
    getForecast.mockResolvedValue({
      current_balance: "2400.00",
      projected_income: "3800.00",
      projected_expense: "1200.00",
      projected_balance: "5000.00",
      pending_count: 3,
    });
    getLedgerReport.mockResolvedValue({
      opening_balance: "2200.00",
      closing_balance: "2400.00",
      rows: [
        {
          row_type: "actual",
          row_id: "row-1",
          date: "2026-03-10",
          description: "Payroll",
          amount: "1400.00",
          type: "income",
          status: "posted",
          balance_after: "2400.00",
          planned_payment_id: null,
          projected_transaction_id: null,
          transaction_id: "txn-1",
        },
      ],
    });
    listProjectedTransactions.mockResolvedValue([
      { id: "proj-1" },
      { id: "proj-2" },
      { id: "proj-3" },
    ]);
    parseAndCreateTransaction.mockResolvedValue({ id: "txn-2" });
    generateDueProjections.mockResolvedValue([]);
  });

  it("renders forecast metrics and recent ledger rows", async () => {
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Payroll")).toBeInTheDocument();
    expect(screen.getByText("$5,000.00")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText(/^Account$/i)).toHaveValue("acc-1");
    });
  });
});
