import { Navigate, Outlet } from "react-router-dom";

import { useSessionQuery } from "@/features/auth/session";

export function RequirePublic() {
  const sessionQuery = useSessionQuery();

  if (sessionQuery.isLoading) {
    return (
      <div className="auth-shell">
        <div className="auth-card auth-card--loading">
          <div className="spinner" aria-hidden="true" />
          <p>Restoring your workspace...</p>
        </div>
      </div>
    );
  }

  if (sessionQuery.data) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
