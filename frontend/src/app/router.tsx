import type { ReactNode } from "react";
import { Suspense, lazy } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AppShell } from "@/app/shell/AppShell";
import { AuthPageLayout } from "@/features/auth/AuthPageLayout";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { RequirePublic } from "@/features/auth/RequirePublic";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { Card } from "@/shared/ui/Card";
import { SkeletonRows } from "@/shared/ui/Skeleton";

const LoginPage = lazy(() =>
  import("@/features/auth/LoginPage").then((module) => ({ default: module.LoginPage })),
);
const RegisterPage = lazy(() =>
  import("@/features/auth/RegisterPage").then((module) => ({ default: module.RegisterPage })),
);
const DashboardPage = lazy(() =>
  import("@/features/dashboard/DashboardPage").then((module) => ({ default: module.DashboardPage })),
);
const TransactionsPage = lazy(() =>
  import("@/features/transactions/TransactionsPage").then((module) => ({
    default: module.TransactionsPage,
  })),
);
const PlansPage = lazy(() =>
  import("@/features/plans/PlansPage").then((module) => ({ default: module.PlansPage })),
);
const ProjectionsPage = lazy(() =>
  import("@/features/projections/ProjectionsPage").then((module) => ({
    default: module.ProjectionsPage,
  })),
);
const ReportsPage = lazy(() =>
  import("@/features/reports/ReportsPage").then((module) => ({ default: module.ReportsPage })),
);
const AccountsSettingsPage = lazy(() =>
  import("@/features/settings/AccountsSettingsPage").then((module) => ({
    default: module.AccountsSettingsPage,
  })),
);
const CategoriesSettingsPage = lazy(() =>
  import("@/features/settings/CategoriesSettingsPage").then((module) => ({
    default: module.CategoriesSettingsPage,
  })),
);
const TelegramSettingsPage = lazy(() =>
  import("@/features/settings/TelegramSettingsPage").then((module) => ({
    default: module.TelegramSettingsPage,
  })),
);
const OllamaSettingsPage = lazy(() =>
  import("@/features/settings/OllamaSettingsPage").then((module) => ({
    default: module.OllamaSettingsPage,
  })),
);

function RouteFallback() {
  return (
    <div className="page-stack">
      <Card>
        <SkeletonRows count={4} />
      </Card>
    </div>
  );
}

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<RouteFallback />}>{children}</Suspense>;
}

export function AppRouter() {
  return (
    <Routes>
      <Route element={<RequirePublic />}>
        <Route element={<AuthPageLayout />}>
          <Route path="/login" element={<LazyPage><LoginPage /></LazyPage>} />
          <Route path="/register" element={<LazyPage><RegisterPage /></LazyPage>} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<LazyPage><DashboardPage /></LazyPage>} />
          <Route path="/transactions" element={<LazyPage><TransactionsPage /></LazyPage>} />
          <Route path="/transactions/new" element={<LazyPage><TransactionsPage autoOpenNew /></LazyPage>} />
          <Route path="/plans" element={<LazyPage><PlansPage /></LazyPage>} />
          <Route path="/projections" element={<LazyPage><ProjectionsPage /></LazyPage>} />
          <Route path="/reports" element={<LazyPage><ReportsPage /></LazyPage>} />
          <Route path="/settings" element={<Outlet />}>
            <Route index element={<SettingsPage />} />
            <Route path="accounts" element={<LazyPage><AccountsSettingsPage /></LazyPage>} />
            <Route path="categories" element={<LazyPage><CategoriesSettingsPage /></LazyPage>} />
            <Route path="telegram" element={<LazyPage><TelegramSettingsPage /></LazyPage>} />
            <Route path="ollama" element={<LazyPage><OllamaSettingsPage /></LazyPage>} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
