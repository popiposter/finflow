import type { VitePWAOptions } from "vite-plugin-pwa";

type FinflowManifest = Exclude<VitePWAOptions["manifest"], false | undefined>;

export const finflowManifest: FinflowManifest = {
  name: "FinFlow",
  short_name: "FinFlow",
  description:
    "An installable finance workspace for transactions, projections, and cashflow.",
  start_url: "/",
  display: "standalone",
  orientation: "portrait",
  background_color: "#f4efe5",
  theme_color: "#203229",
  icons: [
    {
      src: "/icon-app.svg",
      sizes: "192x192",
      type: "image/svg+xml",
      purpose: "any",
    },
    {
      src: "/icon-maskable.svg",
      sizes: "512x512",
      type: "image/svg+xml",
      purpose: "maskable",
    },
    {
      src: "/icon-apple.svg",
      sizes: "180x180",
      type: "image/svg+xml",
      purpose: "any",
    },
  ],
};

export const finflowPwaOptions: Partial<VitePWAOptions> = {
  registerType: "autoUpdate",
  includeAssets: ["icon-app.svg", "icon-maskable.svg", "icon-apple.svg"],
  manifest: finflowManifest,
  workbox: {
    navigateFallback: "/index.html",
    cleanupOutdatedCaches: true,
    globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
    runtimeCaching: [],
  },
  devOptions: {
    enabled: true,
  },
};
