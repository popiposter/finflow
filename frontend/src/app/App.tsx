import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import { AppErrorBoundary } from "@/app/AppErrorBoundary";
import { AppProviders } from "@/app/AppProviders";
import { AppRouter } from "@/app/router";

export function App() {
  return (
    <AppProviders>
      <AppErrorBoundary>
        <BrowserRouter>
          <AppRouter />
        </BrowserRouter>
        <Toaster
          position="top-right"
          richColors
          closeButton
          toastOptions={{
            style: { fontFamily: "var(--font-body)" },
          }}
        />
      </AppErrorBoundary>
    </AppProviders>
  );
}
