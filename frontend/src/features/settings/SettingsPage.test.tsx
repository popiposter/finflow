import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsPage } from "@/features/settings/SettingsPage";
import { renderWithProviders } from "@/test/test-utils";

const useSessionQuery = vi.fn();
const useLogoutMutation = vi.fn();

vi.mock("@/features/auth/session", () => ({
  useSessionQuery: () => useSessionQuery(),
  useLogoutMutation: () => useLogoutMutation(),
}));

describe("SettingsPage", () => {
  beforeEach(() => {
    if (typeof window.localStorage?.clear === "function") {
      window.localStorage.clear();
    }
    useSessionQuery.mockReturnValue({
      data: { email: "user@example.com" },
    });
    useLogoutMutation.mockReturnValue({
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it("switches the interface language to Russian", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    expect(screen.getByRole("heading", { name: "Language" })).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Language"), "ru");

    expect(screen.getByRole("heading", { name: "Язык" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Выйти" })).toBeInTheDocument();
  });
});
