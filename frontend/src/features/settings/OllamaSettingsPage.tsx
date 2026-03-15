import { useQuery } from "@tanstack/react-query";
import { Bot, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

import { getIntegrationStatus } from "@/shared/api/auth";
import { useAppIntl } from "@/shared/lib/i18n";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { Card } from "@/shared/ui/Card";
import { SkeletonRows } from "@/shared/ui/Skeleton";

export function OllamaSettingsPage() {
  const intl = useAppIntl();
  const integrationQuery = useQuery({
    queryKey: ["integration-status"],
    queryFn: getIntegrationStatus,
  });

  const ollama = integrationQuery.data?.ollama;

  return (
    <AnimatedPage className="page-stack">
      <Card>
        <p className="eyebrow">{intl.formatMessage({ id: "settings.integrationsTitle" })}</p>
        <h2 className="section-title">{intl.formatMessage({ id: "settings.ollamaTitle" })}</h2>
        <p className="muted-copy">{intl.formatMessage({ id: "settings.ollamaCopy" })}</p>
      </Card>

      <Card>
        {integrationQuery.isLoading ? (
          <SkeletonRows count={4} />
        ) : ollama ? (
          <div className="list-stack">
            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.integrationEnabled" })}
                </div>
              <div className="transaction-row__meta">
                  {intl.formatMessage({ id: "settings.ollamaEnabledCopy" })}
                </div>
              </div>
              <strong>
                {ollama.enabled
                  ? intl.formatMessage({ id: "settings.statusOn" })
                  : intl.formatMessage({ id: "settings.statusOff" })}
              </strong>
            </article>

            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.ollamaModel" })}
                </div>
                <div className="transaction-row__meta">{ollama.base_url}</div>
              </div>
              <strong>{ollama.model}</strong>
            </article>

            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.ollamaApiKey" })}
                </div>
              <div className="transaction-row__meta">
                  {intl.formatMessage({ id: "settings.ollamaApiKeyCopy" })}
                </div>
              </div>
              <strong>
                {ollama.api_key_configured
                  ? intl.formatMessage({ id: "settings.statusConfigured" })
                  : intl.formatMessage({ id: "settings.statusMissing" })}
              </strong>
            </article>

            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.ollamaConfidence" })}
                </div>
                <div className="transaction-row__meta">
                  {intl.formatMessage({ id: "settings.ollamaConfidenceCopy" })}
                </div>
              </div>
              <strong>{ollama.min_confidence}</strong>
            </article>
          </div>
        ) : null}
      </Card>

      <Card>
        <div className="settings-link">
          <div>
            <div className="settings-link__title">
              {intl.formatMessage({ id: "settings.ollamaCurrentScopeTitle" })}
            </div>
            <div className="settings-link__copy">
              {intl.formatMessage({ id: "settings.ollamaCurrentScopeCopy" })}
            </div>
          </div>
          <Bot size={18} />
        </div>
      </Card>

      <Card>
        <Link className="settings-link" to="/settings">
          <div>
            <div className="settings-link__title">
              {intl.formatMessage({ id: "settings.backToSettings" })}
            </div>
            <div className="settings-link__copy">
              {intl.formatMessage({ id: "settings.backToSettingsCopy" })}
            </div>
          </div>
          <ChevronRight size={18} />
        </Link>
      </Card>
    </AnimatedPage>
  );
}
