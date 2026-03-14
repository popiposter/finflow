import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { createAccount, deleteAccount, listAccounts, updateAccount } from "@/shared/api/accounts";
import type { Account, AccountType } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { accountTypeLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { formatCurrency } from "@/shared/lib/utils";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { AnimatedList, AnimatedListItem } from "@/shared/ui/AnimatedList";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";
import { SkeletonRows } from "@/shared/ui/Skeleton";

const accountTypes = [
  "checking",
  "savings",
  "credit_card",
  "cash",
  "investment",
  "loan",
  "other",
] as const satisfies AccountType[];

type AccountFormValues = {
  name: string;
  type: AccountType;
  description?: string;
  current_balance?: string;
  currency_code: string;
  is_active: boolean;
};

export function AccountsSettingsPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const schema = useMemo(
    () =>
      z.object({
        name: z.string().trim().min(2, validation.shortName),
        type: z.enum(accountTypes),
        description: z.string().optional(),
        current_balance: z.string().optional(),
        currency_code: z.string().trim().min(3, validation.currencyCode),
        is_active: z.boolean().default(true),
      }),
    [validation],
  );
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const accountsQuery = useQuery({ queryKey: ["accounts"], queryFn: listAccounts });
  const form = useForm<AccountFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      type: "checking",
      description: "",
      current_balance: "0.00",
      currency_code: "USD",
      is_active: true,
    },
  });

  useEffect(() => {
    if (!editingAccount) {
      form.reset({
        name: "",
        type: "checking",
        description: "",
        current_balance: "0.00",
        currency_code: "USD",
        is_active: true,
      });
      return;
    }

    form.reset({
      name: editingAccount.name,
      type: editingAccount.type,
      description: editingAccount.description ?? "",
      current_balance: editingAccount.current_balance ?? "0.00",
      currency_code: editingAccount.currency_code,
      is_active: editingAccount.is_active,
    });
  }, [editingAccount, form]);

  const refreshAccounts = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["accounts"] }),
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.accountCreated" }));
      setIsDialogOpen(false);
      await refreshAccounts();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      accountId,
      payload,
    }: {
      accountId: string;
      payload: AccountFormValues;
    }) => updateAccount(accountId, normalizeAccountPayload(payload)),
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.accountUpdated" }));
      setEditingAccount(null);
      setIsDialogOpen(false);
      await refreshAccounts();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.accountDeleted" }));
      await refreshAccounts();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    if (editingAccount) {
      await updateMutation.mutateAsync({
        accountId: editingAccount.id,
        payload: values,
      });
      return;
    }

    await createMutation.mutateAsync(normalizeAccountPayload(values));
  });

  return (
    <AnimatedPage className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "settings.accountsTitle" })}</p>
          <h2 className="section-title">{intl.formatMessage({ id: "accounts.title" })}</h2>
        </div>
        <Button
          disabled={!isOnline}
          type="button"
          onClick={() => {
            setEditingAccount(null);
            setIsDialogOpen(true);
          }}
        >
          <Plus size={16} />
          {intl.formatMessage({ id: "accounts.new" })}
        </Button>
      </div>

      <Card>
        <div className="list-stack">
          {accountsQuery.isLoading ? (
            <SkeletonRows count={4} />
          ) : accountsQuery.data?.length ? (
            <AnimatedList>
            {accountsQuery.data.map((account) => (
              <AnimatedListItem key={account.id}>
              <article className="transaction-row">
                <div>
                  <div className="transaction-row__title">{account.name}</div>
                  <div className="transaction-row__meta">
                    {accountTypeLabel(intl, account.type)} · {account.currency_code}
                  </div>
                </div>

                <div className="transaction-row__actions">
                  <strong>{formatCurrency(account.current_balance)}</strong>
                  <div className="row-button-group">
                    <button
                      className="inline-action"
                      disabled={!isOnline}
                      type="button"
                      onClick={() => {
                        setEditingAccount(account);
                        setIsDialogOpen(true);
                      }}
                      >
                        <Pencil size={14} />
                        {intl.formatMessage({ id: "common.edit" })}
                      </button>
                    <button
                      className="inline-action inline-action--danger"
                      disabled={!isOnline || deleteMutation.isPending}
                      type="button"
                        onClick={() => {
                          if (window.confirm(intl.formatMessage({ id: "accounts.deleteConfirm" }))) {
                            void deleteMutation.mutateAsync(account.id);
                          }
                        }}
                      >
                        <Trash2 size={14} />
                        {intl.formatMessage({ id: "common.delete" })}
                      </button>
                  </div>
                </div>
              </article>
              </AnimatedListItem>
            ))}
            </AnimatedList>
          ) : (
              <div className="empty-state">{intl.formatMessage({ id: "accounts.empty" })}</div>
            )}
          </div>
      </Card>

      <DialogSheet
        description={intl.formatMessage({ id: "accounts.dialogDescription" })}
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title={
          editingAccount
            ? intl.formatMessage({ id: "accounts.edit" })
            : intl.formatMessage({ id: "accounts.newDialog" })
        }
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <label className="field">
            <span>{intl.formatMessage({ id: "common.name" })}</span>
            <input {...form.register("name")} />
            {getFieldErrorMessage(form.formState.errors.name) ? (
              <small className="field-error">{getFieldErrorMessage(form.formState.errors.name)}</small>
            ) : null}
          </label>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.type" })}</span>
              <select {...form.register("type")}>
                {accountTypes.map((type) => (
                  <option key={type} value={type}>
                    {accountTypeLabel(intl, type)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.currency" })}</span>
              <input {...form.register("currency_code")} />
              {getFieldErrorMessage(form.formState.errors.currency_code) ? (
                <small className="field-error">
                  {getFieldErrorMessage(form.formState.errors.currency_code)}
                </small>
              ) : null}
            </label>
          </div>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.balance" })}</span>
              <input inputMode="decimal" {...form.register("current_balance")} />
            </label>

            <label className="checkbox-field checkbox-field--inline">
              <input type="checkbox" {...form.register("is_active")} />
              <span>{intl.formatMessage({ id: "accounts.active" })}</span>
            </label>
          </div>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.description" })}</span>
            <input {...form.register("description")} />
          </label>

          {createMutation.error || updateMutation.error ? (
            <ApiErrorCallout error={createMutation.error ?? updateMutation.error} />
          ) : null}

          <Button disabled={!isOnline || createMutation.isPending || updateMutation.isPending} type="submit">
            {editingAccount
              ? updateMutation.isPending
                ? intl.formatMessage({ id: "common.saving" })
                : intl.formatMessage({ id: "accounts.save" })
              : createMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "accounts.create" })}
          </Button>
        </form>
      </DialogSheet>
    </AnimatedPage>
  );
}

function normalizeAccountPayload(values: AccountFormValues) {
  return {
    name: values.name,
    type: values.type,
    description: values.description || null,
    current_balance: values.current_balance || null,
    currency_code: values.currency_code,
    is_active: values.is_active,
  };
}
