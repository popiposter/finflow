import { Download } from "lucide-react";
import { useEffect, useState } from "react";

import type { DeferredInstallPrompt } from "@/shared/lib/pwa";
import { Button } from "@/shared/ui/Button";

export function InstallPromptButton({ compact = false }: { compact?: boolean }) {
  const [promptEvent, setPromptEvent] = useState<DeferredInstallPrompt | null>(null);

  useEffect(() => {
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setPromptEvent(event as DeferredInstallPrompt);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    };
  }, []);

  if (!promptEvent) {
    return null;
  }

  const handleInstall = async () => {
    await promptEvent.prompt();
    setPromptEvent(null);
  };

  return (
    <Button
      className={compact ? "install-button install-button--compact" : "install-button"}
      type="button"
      variant={compact ? "ghost" : "secondary"}
      onClick={() => void handleInstall()}
    >
      <Download size={16} />
      <span>{compact ? "Install" : "Install app"}</span>
    </Button>
  );
}
