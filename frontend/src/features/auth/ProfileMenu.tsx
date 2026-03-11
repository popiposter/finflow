import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { LogOut, Settings2, UserCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getInitials, useLogoutMutation, useSessionQuery } from "@/features/auth/session";

export function ProfileMenu() {
  const navigate = useNavigate();
  const sessionQuery = useSessionQuery();
  const logoutMutation = useLogoutMutation();

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    navigate("/login", { replace: true });
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className="profile-trigger" type="button" aria-label="Open profile menu">
          <span className="profile-avatar">{getInitials(sessionQuery.data)}</span>
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content className="dropdown-content" align="end" sideOffset={10}>
          <div className="dropdown-header">
            <p className="dropdown-title">{sessionQuery.data?.email ?? "FinFlow user"}</p>
            <p className="dropdown-caption">Cookie-authenticated workspace</p>
          </div>

          <DropdownMenu.Item className="dropdown-item" onSelect={() => navigate("/settings")}>
            <UserCircle2 size={16} />
            <span>Profile</span>
          </DropdownMenu.Item>
          <DropdownMenu.Item
            className="dropdown-item"
            onSelect={() => navigate("/settings/accounts")}
          >
            <Settings2 size={16} />
            <span>Settings</span>
          </DropdownMenu.Item>
          <DropdownMenu.Separator className="dropdown-separator" />
          <DropdownMenu.Item className="dropdown-item" onSelect={() => void handleLogout()}>
            <LogOut size={16} />
            <span>{logoutMutation.isPending ? "Signing out..." : "Sign out"}</span>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
