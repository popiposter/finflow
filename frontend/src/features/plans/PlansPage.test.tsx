import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlansPage } from "@/features/plans/PlansPage";
import { renderWithProviders } from "@/test/test-utils";

let isOnline = true;

const listAccounts = vi.fn();
const listCategories = vi.fn();
const listPlans = vi.fn();
const createPlan = vi.fn();
const updatePlan = vi.fn();
const deletePlan = vi.fn();
const generateDueProjections = vi.fn();

vi.mock("@/shared/lib/offline", () => ({
  useOnlineStatus: () => isOnline,
}));

vi.mock("@/shared/api/accounts", () => ({
  listAccounts: () => listAccounts(),
}));

vi.mock("@/shared/api/categories", () => ({
  listCategories: () => listCategories(),
}));

vi.mock("@/shared/api/plans", () => ({
  listPlans: () => listPlans(),
  createPlan: (payload: unknown) => createPlan(payload),
  updatePlan: (planId: string, payload: unknown) => updatePlan(planId, payload),
  deletePlan: (planId: string) => deletePlan(planId),
  generateDueProjections: (asOfDate?: string) => generateDueProjections(asOfDate),
}));

describe("PlansPage", () => {
  beforeEach(() => {
    isOnline = true;
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
    listPlans.mockResolvedValue([]);
    createPlan.mockResolvedValue({ id: "plan-1" });
    updatePlan.mockResolvedValue({ id: "plan-1" });
    deletePlan.mockResolvedValue(undefined);
    generateDueProjections.mockResolvedValue([]);
  });

  it("disables recurring actions when offline", async () => {
    isOnline = false;

    renderWithProviders(<PlansPage />);

    await waitFor(() => expect(listAccounts).toHaveBeenCalled());

    expect(screen.getByRole("button", { name: /generate due/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /new plan/i })).toBeDisabled();
  });

  it("opens the planned payment form with recurring defaults", async () => {
    const user = userEvent.setup();

    renderWithProviders(<PlansPage />);

    await waitFor(() => expect(listAccounts).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: /new plan/i }));

    expect(screen.getByRole("heading", { name: /new planned payment/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^Recurrence$/i)).toHaveValue("monthly");
    expect(screen.getByLabelText(/^Account$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Start$/i)).toBeInTheDocument();
  });
});
