import { registerSW } from "virtual:pwa-register";

export type DeferredInstallPrompt = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

export function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return () => undefined;
  }

  return registerSW({
    immediate: true,
    onOfflineReady() {
      console.info("FinFlow is ready for offline shell access.");
    },
  });
}
