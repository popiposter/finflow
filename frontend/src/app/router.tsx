import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AppShell } from "@/app/shell/AppShell";
import { AuthPageLayout } from "@/features/auth/AuthPageLayout";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { RequirePublic } from "@/features/auth/RequirePublic";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PlansPage } from "@/features/plans/PlansPage";
import { ProjectionsPage } from "@/features/projections/ProjectionsPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { AccountsSettingsPage } from "@/features/settings/AccountsSettingsPage";
import { CategoriesSettingsPage } from "@/features/settings/CategoriesSettingsPage";
import { OllamaSettingsPage } from "@/features/settings/OllamaSettingsPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { TelegramSettingsPage } from "@/features/settings/TelegramSettingsPage";
import { TransactionsPage } from "@/features/transactions/TransactionsPage";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<RequirePublic />}>
        <Route element={<AuthPageLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/transactions/new" element={<TransactionsPage autoOpenNew />} />
          <Route path="/plans" element={<PlansPage />} />
          <Route path="/projections" element={<ProjectionsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<Outlet />}>
            <Route index element={<SettingsPage />} />
            <Route path="accounts" element={<AccountsSettingsPage />} />
            <Route path="categories" element={<CategoriesSettingsPage />} />
            <Route path="telegram" element={<TelegramSettingsPage />} />
            <Route path="ollama" element={<OllamaSettingsPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
