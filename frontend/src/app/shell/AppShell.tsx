import { BellRing, Landmark, LayoutDashboard, ListTodo, ReceiptText, Settings2 } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { ProfileMenu } from "@/features/auth/ProfileMenu";
import { InstallPromptButton } from "@/features/dashboard/InstallPromptButton";
import { useOnlineStatus } from "@/shared/lib/offline";
import { cn } from "@/shared/lib/utils";

const primaryNav = [
  { to: "/", label: "Home", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: ReceiptText },
  { to: "/plans", label: "Plans", icon: ListTodo },
  { to: "/projections", label: "Projections", icon: BellRing },
  { to: "/reports", label: "Reports", icon: Landmark },
];

export function AppShell() {
  const location = useLocation();
  const isOnline = useOnlineStatus();

  return (
    <div className="app-shell">
      {!isOnline ? (
        <div className="offline-banner">
          You're offline. Cached reads stay available, but changes need a connection.
        </div>
      ) : null}

      <aside className="sidebar">
        <div className="brand-block">
          <span className="brand-mark">F</span>
          <div>
            <div className="eyebrow">Installable cashflow workspace</div>
            <div className="brand-name">FinFlow</div>
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
            <span>Settings</span>
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
              {location.pathname === "/" ? "Dashboard" : "Core finance"}
            </div>
            <h1 className="topbar-title">{resolvePageTitle(location.pathname)}</h1>
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

function resolvePageTitle(pathname: string) {
  if (pathname.startsWith("/transactions")) {
    return "Transactions";
  }

  if (pathname.startsWith("/plans")) {
    return "Planned payments";
  }

  if (pathname.startsWith("/projections")) {
    return "Projected transactions";
  }

  if (pathname.startsWith("/reports")) {
    return "Reports and cashflow";
  }

  if (pathname.startsWith("/settings/accounts")) {
    return "Account settings";
  }

  if (pathname.startsWith("/settings/categories")) {
    return "Category settings";
  }

  if (pathname.startsWith("/settings")) {
    return "Settings";
  }

  return "Finance cockpit";
}
