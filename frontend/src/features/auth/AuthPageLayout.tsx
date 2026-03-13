import { Outlet } from "react-router-dom";

import { useAppIntl } from "@/shared/lib/i18n";

export function AuthPageLayout() {
  const intl = useAppIntl();

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "auth.layoutEyebrow" })}</p>
          <h1 className="auth-title">{intl.formatMessage({ id: "auth.layoutTitle" })}</h1>
          <p className="auth-copy">{intl.formatMessage({ id: "auth.layoutCopy" })}</p>
        </div>

        <div className="auth-card">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
