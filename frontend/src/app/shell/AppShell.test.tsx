import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "@/app/shell/AppShell";
import { AppIntlProvider } from "@/shared/lib/i18n";

vi.mock("@/shared/lib/offline", () => ({
  useOnlineStatus: vi.fn(() => false),
}));

vi.mock("@/features/auth/ProfileMenu", () => ({
  ProfileMenu: () => <div>Profile menu</div>,
}));

vi.mock("@/features/dashboard/InstallPromptButton", () => ({
  InstallPromptButton: () => <button type="button">Install app</button>,
}));

describe("AppShell", () => {
  it("shows the offline banner when the device is offline", () => {
    render(
      <AppIntlProvider>
        <MemoryRouter initialEntries={["/transactions"]}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/transactions" element={<div>Transactions view</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AppIntlProvider>,
    );

    expect(
      screen.getByText(/cached reads stay available, but changes need a connection/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Transactions" }),
    ).toBeInTheDocument();
  });
});
