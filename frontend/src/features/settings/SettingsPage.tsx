import { ChevronRight, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useLogoutMutation, useSessionQuery } from "@/features/auth/session";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";

export function SettingsPage() {
  const navigate = useNavigate();
  const sessionQuery = useSessionQuery();
  const logoutMutation = useLogoutMutation();

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    navigate("/login", { replace: true });
  };

  return (
    <div className="page-stack">
      <Card>
        <p className="eyebrow">Workspace owner</p>
        <h2 className="section-title">{sessionQuery.data?.email ?? "FinFlow user"}</h2>
        <p className="muted-copy">
          This PWA uses HttpOnly cookies for auth and keeps cached reads available offline.
        </p>
      </Card>

      <div className="content-grid">
        <Card>
          <Link className="settings-link" to="/settings/accounts">
            <div>
              <div className="settings-link__title">Accounts</div>
              <div className="settings-link__copy">Manage account types, balances, and lifecycle.</div>
            </div>
            <ChevronRight size={18} />
          </Link>
        </Card>

        <Card>
          <Link className="settings-link" to="/settings/categories">
            <div>
              <div className="settings-link__title">Categories</div>
              <div className="settings-link__copy">Maintain your reporting and ingestion taxonomy.</div>
            </div>
            <ChevronRight size={18} />
          </Link>
        </Card>
      </div>

      <Card>
        <Button disabled={logoutMutation.isPending} type="button" variant="danger" onClick={() => void handleLogout()}>
          <LogOut size={16} />
          {logoutMutation.isPending ? "Signing out..." : "Sign out"}
        </Button>
      </Card>
    </div>
  );
}
