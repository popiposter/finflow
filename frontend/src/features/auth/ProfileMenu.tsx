import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { LogOut, Settings2, UserCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getInitials, useLogoutMutation, useSessionQuery } from "@/features/auth/session";
import { LanguageSwitcher } from "@/features/settings/LanguageSwitcher";
import { useAppIntl } from "@/shared/lib/i18n";

export function ProfileMenu() {
  const intl = useAppIntl();
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
        <button
          className="profile-trigger"
          type="button"
          aria-label={intl.formatMessage({ id: "auth.openProfileMenu" })}
        >
          <span className="profile-avatar">{getInitials(sessionQuery.data)}</span>
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content className="dropdown-content" align="end" sideOffset={10}>
          <div className="dropdown-header">
            <p className="dropdown-title">
              {sessionQuery.data?.email ?? intl.formatMessage({ id: "auth.finflowUser" })}
            </p>
            <p className="dropdown-caption">
              {intl.formatMessage({ id: "auth.cookieWorkspace" })}
            </p>
          </div>

          <DropdownMenu.Item className="dropdown-item" onSelect={() => navigate("/settings")}>
            <UserCircle2 size={16} />
            <span>{intl.formatMessage({ id: "common.profile" })}</span>
          </DropdownMenu.Item>
          <DropdownMenu.Item
            className="dropdown-item"
            onSelect={() => navigate("/settings/accounts")}
          >
            <Settings2 size={16} />
            <span>{intl.formatMessage({ id: "common.settings" })}</span>
          </DropdownMenu.Item>
          <div className="dropdown-item" role="group" aria-label={intl.formatMessage({ id: "common.language" })}>
            <UserCircle2 size={16} />
            <LanguageSwitcher />
          </div>
          <DropdownMenu.Separator className="dropdown-separator" />
          <DropdownMenu.Item className="dropdown-item" onSelect={() => void handleLogout()}>
            <LogOut size={16} />
            <span>
              {logoutMutation.isPending
                ? intl.formatMessage({ id: "common.signingOut" })
                : intl.formatMessage({ id: "common.signOut" })}
            </span>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
