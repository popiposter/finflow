import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSessionQuery } from "@/features/auth/session";

export function RequireAuth() {
  const location = useLocation();
  const sessionQuery = useSessionQuery();

  if (sessionQuery.isLoading) {
    return <FullScreenState title="Checking your session..." />;
  }

  if (sessionQuery.isError) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function FullScreenState({ title }: { title: string }) {
  return (
    <div className="auth-shell">
      <div className="auth-card auth-card--loading">
        <div className="spinner" aria-hidden="true" />
        <p>{title}</p>
      </div>
    </div>
  );
}
