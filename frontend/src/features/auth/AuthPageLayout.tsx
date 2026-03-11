import { Outlet } from "react-router-dom";

export function AuthPageLayout() {
  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div>
          <p className="eyebrow">FinFlow PWA</p>
          <h1 className="auth-title">A cleaner way to see money, plans, and drift.</h1>
          <p className="auth-copy">
            Installable finance tracking with actual transactions, projected cashflow,
            and recurring templates in one calm workspace.
          </p>
        </div>

        <div className="auth-card">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
