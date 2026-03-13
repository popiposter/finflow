import { BellRing, Landmark, LayoutDashboard, ListTodo, ReceiptText, Settings2 } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { ProfileMenu } from "@/features/auth/ProfileMenu";
import { InstallPromptButton } from "@/features/dashboard/InstallPromptButton";
import { useAppIntl } from "@/shared/lib/i18n";
import { useOnlineStatus } from "@/shared/lib/offline";
import { cn } from "@/shared/lib/utils";

export function AppShell() {
  const intl = useAppIntl();
  const location = useLocation();
  const isOnline = useOnlineStatus();
  const primaryNav = [
    { to: "/", label: intl.formatMessage({ id: "shell.home" }), icon: LayoutDashboard },
    {
      to: "/transactions",
      label: intl.formatMessage({ id: "shell.transactions" }),
      icon: ReceiptText,
    },
    { to: "/plans", label: intl.formatMessage({ id: "shell.plans" }), icon: ListTodo },
    {
      to: "/projections",
      label: intl.formatMessage({ id: "shell.projections" }),
      icon: BellRing,
    },
    { to: "/reports", label: intl.formatMessage({ id: "shell.reports" }), icon: Landmark },
  ];

  return (
    <div className="app-shell">
      {!isOnline ? (
        <div className="offline-banner">
          {intl.formatMessage({ id: "shell.offlineBanner" })}
        </div>
      ) : null}

      <aside className="sidebar">
        <div className="brand-block">
          <span className="brand-mark">F</span>
          <div>
            <div className="eyebrow">
              {intl.formatMessage({ id: "shell.installableWorkspace" })}
            </div>
            <div className="brand-name">{intl.formatMessage({ id: "common.appName" })}</div>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          {primaryNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                className={({ isActive }) =>
                  cn("sidebar-link", isActive && "is-active")
                }
                to={item.to}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}

          <NavLink
            className={({ isActive }) =>
              cn("sidebar-link", isActive && "is-active")
            }
            to="/settings"
          >
            <Settings2 size={18} />
            <span>{intl.formatMessage({ id: "shell.settings" })}</span>
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <InstallPromptButton compact />
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div>
            <div className="eyebrow">
              {location.pathname === "/"
                ? intl.formatMessage({ id: "shell.dashboardEyebrow" })
                : intl.formatMessage({ id: "shell.coreFinanceEyebrow" })}
            </div>
            <h1 className="topbar-title">{resolvePageTitle(location.pathname, intl)}</h1>
          </div>

          <div className="topbar-actions">
            <InstallPromptButton />
            <ProfileMenu />
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>

        <nav className="bottom-nav" aria-label="Mobile primary">
          {primaryNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                className={({ isActive }) =>
                  cn("bottom-link", isActive && "is-active")
                }
                to={item.to}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

function resolvePageTitle(
  pathname: string,
  intl: ReturnType<typeof useAppIntl>,
) {
  if (pathname.startsWith("/transactions")) {
    return intl.formatMessage({ id: "shell.transactions" });
  }

  if (pathname.startsWith("/plans")) {
    return intl.formatMessage({ id: "shell.plannedPayments" });
  }

  if (pathname.startsWith("/projections")) {
    return intl.formatMessage({ id: "shell.projectedTransactions" });
  }

  if (pathname.startsWith("/reports")) {
    return intl.formatMessage({ id: "shell.reportsAndCashflow" });
  }

  if (pathname.startsWith("/settings/accounts")) {
    return intl.formatMessage({ id: "shell.accountSettings" });
  }

  if (pathname.startsWith("/settings/categories")) {
    return intl.formatMessage({ id: "shell.categorySettings" });
  }

  if (pathname.startsWith("/settings")) {
    return intl.formatMessage({ id: "shell.settings" });
  }

  return intl.formatMessage({ id: "shell.financeCockpit" });
}
