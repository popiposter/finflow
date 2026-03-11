import { describe, expect, it } from "vitest";

import { finflowManifest, finflowPwaOptions } from "@/app/pwa/config";

describe("PWA config", () => {
  it("ships an installable standalone manifest", () => {
    expect(finflowManifest.name).toBe("FinFlow");
    expect(finflowManifest.display).toBe("standalone");
    expect(finflowManifest.icons).toContainEqual(
      expect.objectContaining({ src: "/icon-app.svg" }),
    );
    expect(finflowManifest.icons).toContainEqual(
      expect.objectContaining({ src: "/icon-maskable.svg", purpose: "maskable" }),
    );
  });

  it("keeps runtime API data out of workbox caching decisions", () => {
    expect(finflowPwaOptions.registerType).toBe("autoUpdate");
    expect(finflowPwaOptions.workbox?.navigateFallback).toBe("/index.html");
    expect(finflowPwaOptions.workbox?.runtimeCaching).toEqual([]);
  });
});
