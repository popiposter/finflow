import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectionsPage } from "@/features/projections/ProjectionsPage";
import { renderWithProviders } from "@/test/test-utils";

let isOnline = true;

const listCategories = vi.fn();
const listProjectedTransactions = vi.fn();
const updateProjectedTransaction = vi.fn();
const confirmProjectedTransaction = vi.fn();
const skipProjectedTransaction = vi.fn();

vi.mock("@/shared/lib/offline", () => ({
  useOnlineStatus: () => isOnline,
}));

vi.mock("@/shared/api/categories", () => ({
  listCategories: () => listCategories(),
}));

vi.mock("@/shared/api/projections", () => ({
  listProjectedTransactions: (filters: unknown) => listProjectedTransactions(filters),
  updateProjectedTransaction: (projectionId: string, payload: unknown) =>
    updateProjectedTransaction(projectionId, payload),
  confirmProjectedTransaction: (projectionId: string) =>
    confirmProjectedTransaction(projectionId),
  skipProjectedTransaction: (projectionId: string) => skipProjectedTransaction(projectionId),
}));

describe("ProjectionsPage", () => {
  beforeEach(() => {
    isOnline = true;
    vi.clearAllMocks();
    listCategories.mockResolvedValue([
      {
        id: "cat-1",
        user_id: "user-1",
        name: "Rent",
        type: "expense",
        description: null,
        parent_id: null,
        is_active: true,
        display_order: 0,
        created_at: "",
        updated_at: "",
      },
    ]);
    listProjectedTransactions.mockResolvedValue([
      {
        id: "proj-1",
        planned_payment_id: "plan-1",
        origin_date: "2026-03-12",
        origin_amount: "1200.00",
        origin_description: "Monthly rent",
        origin_category_id: "cat-1",
        type: "expense",
        projected_date: "2026-03-12",
        projected_amount: "1200.00",
        projected_description: "Monthly rent",
        projected_category_id: "cat-1",
        status: "pending",
        transaction_id: null,
        resolved_at: null,
        version: 1,
        created_at: "",
        updated_at: "",
      },
    ]);
    updateProjectedTransaction.mockResolvedValue({ id: "proj-1" });
    confirmProjectedTransaction.mockResolvedValue({ transaction_id: "txn-1" });
    skipProjectedTransaction.mockResolvedValue({ id: "proj-1" });
  });

  it("disables projection mutations when offline", async () => {
    isOnline = false;

    renderWithProviders(<ProjectionsPage />);

    expect(await screen.findByText("Monthly rent")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /edit/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /confirm/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /skip/i })).toBeDisabled();
  });

  it("edits a pending projection", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ProjectionsPage />);

    expect(await screen.findByText("Monthly rent")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /edit/i }));
    await user.clear(screen.getByLabelText(/projected amount/i));
    await user.type(screen.getByLabelText(/projected amount/i), "1280.00");
    await user.click(screen.getByRole("button", { name: /save projection/i }));

    await waitFor(() => {
      expect(updateProjectedTransaction).toHaveBeenCalledWith(
        "proj-1",
        expect.objectContaining({
          projected_amount: "1280.00",
          projected_description: "Monthly rent",
          projected_category_id: "cat-1",
        }),
      );
    });
  });
});
