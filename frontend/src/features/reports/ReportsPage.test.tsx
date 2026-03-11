import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReportsPage } from "@/features/reports/ReportsPage";
import { renderWithProviders } from "@/test/test-utils";

const getPnlReport = vi.fn();
const getCashflowReport = vi.fn();
const getLedgerReport = vi.fn();
const getForecast = vi.fn();

vi.mock("@/shared/api/reports", () => ({
  getPnlReport: (params: unknown) => getPnlReport(params),
  getCashflowReport: (params: unknown) => getCashflowReport(params),
  getLedgerReport: (params: unknown) => getLedgerReport(params),
  getForecast: (targetDate?: string) => getForecast(targetDate),
}));

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPnlReport.mockResolvedValue({
      date_accrual_start: "2026-02-01",
      date_accrual_end: "2026-03-31",
      totals_by_category: [{ category_id: "cat-1", category_name: "Salary", total: "3800.00", type: "income" }],
      totals_by_type: [{ type: "income", total: "3800.00" }],
      grand_total: "3800.00",
    });
    getCashflowReport.mockResolvedValue({
      date_cash_start: "2026-02-01",
      date_cash_end: "2026-03-31",
      totals_by_category: [{ category_id: "cat-1", category_name: "Housing", total: "-1200.00", type: "expense" }],
      totals_by_type: [{ type: "expense", total: "-1200.00" }],
      grand_total: "-1200.00",
    });
    getLedgerReport.mockResolvedValue({
      opening_balance: "2200.00",
      closing_balance: "5000.00",
      rows: [
        {
          row_type: "projected",
          row_id: "row-1",
          date: "2026-03-15",
          description: "March salary",
          amount: "2600.00",
          type: "income",
          status: "pending",
          balance_after: "5000.00",
          planned_payment_id: "plan-1",
          projected_transaction_id: "proj-1",
          transaction_id: null,
        },
      ],
    });
    getForecast.mockResolvedValue({
      current_balance: "2400.00",
      projected_income: "3800.00",
      projected_expense: "1200.00",
      projected_balance: "5000.00",
      pending_count: 2,
    });
  });

  it("renders forecast and switches to the unified ledger tab", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ReportsPage />);

    expect(await screen.findByText("Current balance")).toBeInTheDocument();
    expect(await screen.findByText("$5,000.00")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /unified ledger/i }));

    await waitFor(() => {
      expect(screen.getByText("March salary")).toBeInTheDocument();
    });
    expect(screen.getByText(/Opening \$2,200.00/i)).toBeInTheDocument();
  });
});
