import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronRight, Copy, PowerOff, Send, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import {
  createApiToken,
  disconnectTelegramLink,
  getIntegrationStatus,
  listApiTokens,
  listTelegramLinks,
  revokeApiToken,
} from "@/shared/api/auth";
import { listAccounts } from "@/shared/api/accounts";
import type { ApiTokenWithRawToken } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { SkeletonRows } from "@/shared/ui/Skeleton";

export function TelegramSettingsPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const [tokenName, setTokenName] = useState("Telegram Bot");
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [latestToken, setLatestToken] = useState<ApiTokenWithRawToken | null>(null);

  const integrationQuery = useQuery({
    queryKey: ["integration-status"],
    queryFn: getIntegrationStatus,
  });
  const accountsQuery = useQuery({ queryKey: ["accounts"], queryFn: listAccounts });
  const tokensQuery = useQuery({ queryKey: ["api-tokens"], queryFn: listApiTokens });
  const linksQuery = useQuery({ queryKey: ["telegram-links"], queryFn: listTelegramLinks });

  const createTokenMutation = useMutation({
    mutationFn: createApiToken,
    onSuccess: (data) => {
      setLatestToken(data);
      toast.success(intl.formatMessage({ id: "settings.telegramTokenCreated" }));
      void tokensQuery.refetch();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const revokeTokenMutation = useMutation({
    mutationFn: revokeApiToken,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "settings.telegramTokenRevoked" }));
      await queryClient.invalidateQueries({ queryKey: ["api-tokens"] });
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const disconnectLinkMutation = useMutation({
    mutationFn: disconnectTelegramLink,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "settings.telegramLinkDisconnected" }));
      await queryClient.invalidateQueries({ queryKey: ["telegram-links"] });
      await queryClient.invalidateQueries({ queryKey: ["integration-status"] });
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const suggestedCommand = useMemo(() => {
    if (!latestToken) {
      return "";
    }
    if (selectedAccountId) {
      return `/connect ${latestToken.raw_token} ${selectedAccountId}`;
    }
    return `/connect ${latestToken.raw_token}`;
  }, [latestToken, selectedAccountId]);

  const copyText = async (value: string, successId: string) => {
    await navigator.clipboard.writeText(value);
    toast.success(intl.formatMessage({ id: successId }));
  };

  const telegram = integrationQuery.data?.telegram;
  const accountNameById = useMemo(
    () => new Map((accountsQuery.data ?? []).map((account) => [account.id, account.name])),
    [accountsQuery.data],
  );

  return (
    <AnimatedPage className="page-stack">
      <Card>
        <p className="eyebrow">{intl.formatMessage({ id: "settings.integrationsTitle" })}</p>
        <h2 className="section-title">{intl.formatMessage({ id: "settings.telegramTitle" })}</h2>
        <p className="muted-copy">{intl.formatMessage({ id: "settings.telegramCopy" })}</p>
      </Card>

      <Card>
        {integrationQuery.isLoading ? (
          <SkeletonRows count={3} />
        ) : telegram ? (
          <div className="list-stack">
            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.integrationEnabled" })}
                </div>
              <div className="transaction-row__meta">
                  {intl.formatMessage({ id: "settings.telegramEnabledCopy" })}
                </div>
              </div>
              <strong>
                {telegram.enabled
                  ? intl.formatMessage({ id: "settings.statusOn" })
                  : intl.formatMessage({ id: "settings.statusOff" })}
              </strong>
            </article>

            <article className="transaction-row">
              <div>
                <div className="transaction-row__title">
                  {intl.formatMessage({ id: "settings.telegramCommands" })}
                </div>
                <div className="transaction-row__meta">
                  {intl.formatMessage({ id: "settings.telegramCommandsCopy" })}
                </div>
              </div>
              <div className="transaction-row__actions">
                {telegram.commands.map((command) => (
                  <span key={command}>{command}</span>
                ))}
              </div>
            </article>
          </div>
        ) : null}
      </Card>

      <Card>
        <div className="form-stack">
          <div>
            <h3 className="section-title">{intl.formatMessage({ id: "settings.telegramTokenTitle" })}</h3>
            <p className="muted-copy">{intl.formatMessage({ id: "settings.telegramTokenCopy" })}</p>
          </div>

          <label className="field">
            <span>{intl.formatMessage({ id: "settings.telegramTokenName" })}</span>
            <input value={tokenName} onChange={(event) => setTokenName(event.target.value)} />
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "settings.telegramAccount" })}</span>
            <select
              value={selectedAccountId}
              onChange={(event) => setSelectedAccountId(event.target.value)}
            >
              <option value="">{intl.formatMessage({ id: "settings.telegramAccountAuto" })}</option>
              {accountsQuery.data?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.id})
                </option>
              ))}
            </select>
          </label>

          {createTokenMutation.error ? <ApiErrorCallout error={createTokenMutation.error} /> : null}

          <Button
            disabled={createTokenMutation.isPending || !tokenName.trim()}
            type="button"
            onClick={() => createTokenMutation.mutate({ name: tokenName.trim() })}
          >
            <Send size={16} />
            {createTokenMutation.isPending
              ? intl.formatMessage({ id: "common.creating" })
              : intl.formatMessage({ id: "settings.telegramCreateToken" })}
          </Button>
        </div>
      </Card>

      {latestToken ? (
        <Card>
          <div className="form-stack">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "settings.telegramLatestTokenTitle" })}</h3>
              <p className="muted-copy">{intl.formatMessage({ id: "settings.telegramLatestTokenCopy" })}</p>
            </div>

            <label className="field">
              <span>{intl.formatMessage({ id: "settings.telegramRawToken" })}</span>
              <input readOnly value={latestToken.raw_token} />
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "settings.telegramConnectCommand" })}</span>
              <input readOnly value={suggestedCommand} />
            </label>

            <div className="action-group">
              <Button
                type="button"
                variant="secondary"
                onClick={() => void copyText(latestToken.raw_token, "settings.telegramTokenCopied")}
              >
                <Copy size={16} />
                {intl.formatMessage({ id: "settings.copyToken" })}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void copyText(suggestedCommand, "settings.telegramCommandCopied")}
              >
                <Check size={16} />
                {intl.formatMessage({ id: "settings.copyCommand" })}
              </Button>
            </div>
          </div>
        </Card>
      ) : null}

      <Card>
        <div className="list-stack">
          <div>
            <h3 className="section-title">{intl.formatMessage({ id: "settings.telegramExistingTokensTitle" })}</h3>
            <p className="muted-copy">{intl.formatMessage({ id: "settings.telegramExistingTokensCopy" })}</p>
          </div>

          {tokensQuery.isLoading ? (
            <SkeletonRows count={2} />
          ) : tokensQuery.data?.length ? (
            tokensQuery.data.map((token) => (
              <article key={token.id} className="transaction-row">
                <div>
                  <div className="transaction-row__title">{token.name}</div>
                  <div className="transaction-row__meta">
                    {intl.formatMessage(
                      { id: "settings.telegramTokenCreatedAt" },
                      { date: intl.formatDate(token.created_at, { dateStyle: "medium" }) },
                    )}
                  </div>
                </div>
                <div className="transaction-row__actions">
                  <strong>
                    {token.is_revoked
                      ? intl.formatMessage({ id: "settings.statusRevoked" })
                      : intl.formatMessage({ id: "settings.statusActive" })}
                  </strong>
                  {!token.is_revoked ? (
                    <Button
                      type="button"
                      variant="ghost"
                      disabled={revokeTokenMutation.isPending}
                      onClick={() => revokeTokenMutation.mutate(token.id)}
                    >
                      <Trash2 size={16} />
                      {intl.formatMessage({ id: "settings.revokeToken" })}
                    </Button>
                  ) : null}
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">{intl.formatMessage({ id: "settings.telegramNoTokens" })}</div>
          )}
        </div>
      </Card>

      <Card>
        <div className="list-stack">
          <div>
            <h3 className="section-title">{intl.formatMessage({ id: "settings.telegramLinkedChatsTitle" })}</h3>
            <p className="muted-copy">{intl.formatMessage({ id: "settings.telegramLinkedChatsCopy" })}</p>
          </div>

          {linksQuery.isLoading ? (
            <SkeletonRows count={2} />
          ) : linksQuery.data?.length ? (
            linksQuery.data.map((link) => (
              <article key={link.id} className="transaction-row">
                <div>
                  <div className="transaction-row__title">
                    {link.first_name ?? link.username ?? `Chat ${link.chat_id}`}
                  </div>
                  <div className="transaction-row__meta">
                    {intl.formatMessage(
                      { id: "settings.telegramLinkedChatMeta" },
                      {
                        chatId: link.chat_id,
                        accountName:
                          accountNameById.get(link.account_id) ??
                          intl.formatMessage({ id: "settings.telegramUnknownAccount" }),
                      },
                    )}
                  </div>
                  <div className="transaction-row__meta">
                    {link.last_seen_at
                      ? intl.formatMessage(
                          { id: "settings.telegramLastSeen" },
                          {
                            date: intl.formatDate(new Date(link.last_seen_at), {
                              dateStyle: "medium",
                              timeStyle: "short",
                            }),
                          },
                        )
                      : intl.formatMessage({ id: "settings.telegramLastSeenNever" })}
                  </div>
                </div>
                <div className="transaction-row__actions">
                  <strong>
                    {link.is_active
                      ? intl.formatMessage({ id: "settings.statusActive" })
                      : intl.formatMessage({ id: "settings.statusInactive" })}
                  </strong>
                  {link.is_active ? (
                    <Button
                      type="button"
                      variant="ghost"
                      disabled={disconnectLinkMutation.isPending}
                      onClick={() => disconnectLinkMutation.mutate(link.id)}
                    >
                      <PowerOff size={16} />
                      {intl.formatMessage({ id: "settings.disconnectChat" })}
                    </Button>
                  ) : null}
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">{intl.formatMessage({ id: "settings.telegramNoLinkedChats" })}</div>
          )}
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
