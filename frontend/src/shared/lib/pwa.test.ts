import { afterEach, describe, expect, it, vi } from "vitest";

import { registerServiceWorker } from "@/shared/lib/pwa";

vi.mock("virtual:pwa-register", () => ({
  registerSW: vi.fn(() => vi.fn()),
}));

describe("registerServiceWorker", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("registers the service worker when navigator support is available", async () => {
    Object.defineProperty(window.navigator, "serviceWorker", {
      configurable: true,
      value: {},
    });

    registerServiceWorker();

    const { registerSW } = await import("virtual:pwa-register");

    expect(vi.mocked(registerSW)).toHaveBeenCalledWith(
      expect.objectContaining({
        immediate: true,
        onOfflineReady: expect.any(Function),
      }),
    );
  });
});
