import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppErrorBoundary } from "@/app/AppErrorBoundary";
import { AppIntlProvider } from "@/shared/lib/i18n";

function Bomb(): never {
  throw new Error("boom");
}

describe("AppErrorBoundary", () => {
  it("shows a localized fallback for render crashes", async () => {
    const user = userEvent.setup();
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <AppIntlProvider>
        <AppErrorBoundary>
          <Bomb />
        </AppErrorBoundary>
      </AppIntlProvider>,
    );

    expect(
      screen.getByRole("heading", { name: /the app hit an unexpected problem/i }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /go to dashboard/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(
      screen.getByRole("heading", { name: /the app hit an unexpected problem/i }),
    ).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
