import { Bot, ChevronRight, LogOut, MessageCircleMore } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { useLogoutMutation, useSessionQuery } from "@/features/auth/session";
import { LanguageSwitcher } from "@/features/settings/LanguageSwitcher";
import { useAppIntl } from "@/shared/lib/i18n";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";

export function SettingsPage() {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const sessionQuery = useSessionQuery();
  const logoutMutation = useLogoutMutation();

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    toast.success(intl.formatMessage({ id: "toast.loggedOut" }));
    navigate("/login", { replace: true });
  };

  return (
    <AnimatedPage className="page-stack">
      <Card>
        <p className="eyebrow">{intl.formatMessage({ id: "settings.ownerEyebrow" })}</p>
        <h2 className="section-title">
          {sessionQuery.data?.email ?? intl.formatMessage({ id: "auth.finflowUser" })}
        </h2>
        <p className="muted-copy">
          {intl.formatMessage({ id: "settings.authCopy" })}
        </p>
      </Card>

      <div className="content-grid">
        <Card>
          <Link className="settings-link" to="/settings/accounts">
            <div>
              <div className="settings-link__title">
                {intl.formatMessage({ id: "settings.accountsTitle" })}
              </div>
              <div className="settings-link__copy">
                {intl.formatMessage({ id: "settings.accountsCopy" })}
              </div>
            </div>
            <ChevronRight size={18} />
          </Link>
        </Card>

        <Card>
          <Link className="settings-link" to="/settings/categories">
            <div>
              <div className="settings-link__title">
                {intl.formatMessage({ id: "settings.categoriesTitle" })}
              </div>
              <div className="settings-link__copy">
                {intl.formatMessage({ id: "settings.categoriesCopy" })}
              </div>
            </div>
            <ChevronRight size={18} />
          </Link>
        </Card>

        <Card>
          <Link className="settings-link" to="/settings/telegram">
            <div>
              <div className="settings-link__title">
                {intl.formatMessage({ id: "settings.telegramTitle" })}
              </div>
              <div className="settings-link__copy">
                {intl.formatMessage({ id: "settings.telegramCardCopy" })}
              </div>
            </div>
            <MessageCircleMore size={18} />
          </Link>
        </Card>

        <Card>
          <Link className="settings-link" to="/settings/ollama">
            <div>
              <div className="settings-link__title">
                {intl.formatMessage({ id: "settings.ollamaTitle" })}
              </div>
              <div className="settings-link__copy">
                {intl.formatMessage({ id: "settings.ollamaCardCopy" })}
              </div>
            </div>
            <Bot size={18} />
          </Link>
        </Card>
      </div>

      <Card>
        <div className="section-header">
          <div>
            <h3 className="section-title">{intl.formatMessage({ id: "settings.languageTitle" })}</h3>
            <p className="muted-copy">{intl.formatMessage({ id: "settings.languageCopy" })}</p>
          </div>
        </div>
        <label className="field">
          <span>{intl.formatMessage({ id: "common.language" })}</span>
          <LanguageSwitcher />
        </label>
      </Card>

      <Card>
        <Button disabled={logoutMutation.isPending} type="button" variant="danger" onClick={() => void handleLogout()}>
          <LogOut size={16} />
          {logoutMutation.isPending
            ? intl.formatMessage({ id: "common.signingOut" })
            : intl.formatMessage({ id: "common.signOut" })}
        </Button>
      </Card>
    </AnimatedPage>
  );
}
