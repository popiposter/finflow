import { BrowserRouter } from "react-router-dom";

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
      </AppErrorBoundary>
    </AppProviders>
  );
}
