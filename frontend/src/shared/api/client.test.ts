import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/shared/api/client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("refreshes once for /auth/me and retries the session request", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "expired" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "u-1", email: "user@example.com" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

    vi.stubGlobal("fetch", fetchMock);

    const payload = await apiFetch<{ id: string; email: string }>("/auth/me");

    expect(payload).toEqual({ id: "u-1", email: "user@example.com" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/auth/refresh",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });

  it("normalizes structured API errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "account_not_found",
              message: "Account not found",
              fields: { account_id: "Field required" },
            },
          }),
          {
            status: 404,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(apiFetch("/accounts")).rejects.toMatchObject({
      status: 404,
      code: "account_not_found",
      fields: { account_id: "Field required" },
      message: "Account not found",
    });
  });
});
