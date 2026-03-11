import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { RequireAuth } from "@/features/auth/RequireAuth";
import { RequirePublic } from "@/features/auth/RequirePublic";
import { useSessionQuery } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({
  useSessionQuery: vi.fn(),
}));

const mockedUseSessionQuery = vi.mocked(useSessionQuery);

describe("route guards", () => {
  it("redirects protected routes to login when the session cannot be restored", () => {
    mockedUseSessionQuery.mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
    } as ReturnType<typeof useSessionQuery>);

    render(
      <MemoryRouter initialEntries={["/private"]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/private" element={<div>Protected page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects public routes home when a session already exists", () => {
    mockedUseSessionQuery.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { id: "u-1", email: "user@example.com" },
    } as ReturnType<typeof useSessionQuery>);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/" element={<div>Dashboard</div>} />
          <Route element={<RequirePublic />}>
            <Route path="/login" element={<div>Login page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});
