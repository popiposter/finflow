import { motion } from "framer-motion";
import { Outlet } from "react-router-dom";

import { useAppIntl } from "@/shared/lib/i18n";

export function AuthPageLayout() {
  const intl = useAppIntl();

  return (
    <div className="auth-shell">
      <motion.div
        className="auth-panel"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      >
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "auth.layoutEyebrow" })}</p>
          <h1 className="auth-title">{intl.formatMessage({ id: "auth.layoutTitle" })}</h1>
          <p className="auth-copy">{intl.formatMessage({ id: "auth.layoutCopy" })}</p>
        </div>

        <div className="auth-card">
          <Outlet />
        </div>
      </motion.div>
    </div>
  );
}
