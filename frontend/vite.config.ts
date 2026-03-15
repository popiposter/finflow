import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

import { finflowPwaOptions } from "./src/app/pwa/config";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const devProxyTarget =
  process.env.VITE_DEV_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), VitePWA(finflowPwaOptions)],
  resolve: {
    alias: {
      "@": path.resolve(rootDir, "src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (id.includes("recharts")) {
            return "charts";
          }
          if (id.includes("@tanstack")) {
            return "tanstack";
          }
          if (id.includes("@radix-ui")) {
            return "radix";
          }
          if (id.includes("react-intl") || id.includes("@formatjs")) {
            return "intl";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    proxy: {
      "/api": {
        target: devProxyTarget,
        changeOrigin: false,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    css: true,
  },
});
