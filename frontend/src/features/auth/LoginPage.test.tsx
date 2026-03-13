import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/LoginPage";
import { renderWithProviders } from "@/test/test-utils";

const mutateAsync = vi.fn();

vi.mock("@/features/auth/session", () => ({
  useLoginMutation: () => ({
    mutateAsync,
    isPending: false,
    error: null,
  }),
}));

describe("LoginPage validation", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows localized client-side validation messages", async () => {
    const user = userEvent.setup();

    renderWithProviders(<LoginPage />, { route: "/login" });

    await user.type(screen.getByLabelText(/email/i), "bad");
    await user.type(screen.getByLabelText(/password/i), "123");
    fireEvent.submit(screen.getByRole("button", { name: /sign in/i }).closest("form")!);

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Use at least 8 characters.")).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});
