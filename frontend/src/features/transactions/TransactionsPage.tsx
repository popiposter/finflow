import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Pencil, Plus, Trash2, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { listAccounts } from "@/shared/api/accounts";
import { listCategories } from "@/shared/api/categories";
import {
  createTransaction,
  deleteTransaction,
  importTransactionsWorkbook,
  listTransactions,
  parseAndCreateTransaction,
  patchTransaction,
} from "@/shared/api/transactions";
import type {
  Transaction,
  TransactionType,
  TransactionWorkbookImportResponse,
} from "@/shared/api/types";
import { useOnlineStatus } from "@/shared/lib/offline";
import {
  formatCurrency,
  formatDateTimeInputValue,
  formatShortDate,
  toIsoDateTime,
} from "@/shared/lib/utils";
import { useAppIntl } from "@/shared/lib/i18n";
import { transactionTypeLabel } from "@/shared/lib/labels";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";

const transactionTypes = [
  "expense",
  "income",
  "payment",
  "refund",
  "transfer",
  "adjustment",
] as const satisfies TransactionType[];

const transactionSchema = z.object({
  account_id: z.string().uuid(),
  category_id: z.string().optional(),
  amount: z.string().min(1),
  type: z.enum(transactionTypes),
  description: z.string().optional(),
  date_accrual: z.string().min(1),
  date_cash: z.string().min(1),
  is_reconciled: z.boolean().default(false),
});

const captureSchema = z.object({
  text: z.string().min(3),
  account_id: z.string().uuid(),
  category_id: z.string().optional(),
});

type TransactionFormValues = z.infer<typeof transactionSchema>;
type CaptureValues = z.infer<typeof captureSchema>;

type TransactionsPageProps = {
  autoOpenNew?: boolean;
};

export function TransactionsPage({ autoOpenNew = false }: TransactionsPageProps) {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(autoOpenNew);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importAccountId, setImportAccountId] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importSummary, setImportSummary] = useState<TransactionWorkbookImportResponse | null>(null);

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });
  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: listCategories,
  });
  const transactionsQuery = useQuery({
    queryKey: ["transactions"],
    queryFn: listTransactions,
  });

  const accountOptions = accountsQuery.data ?? [];
  const categoryOptions = categoriesQuery.data ?? [];

  const transactionForm = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      account_id: "",
      category_id: "",
      amount: "",
      type: "expense",
      description: "",
      date_accrual: formatDateTimeInputValue(new Date().toISOString()),
      date_cash: formatDateTimeInputValue(new Date().toISOString()),
      is_reconciled: false,
    },
  });

  const captureForm = useForm<CaptureValues>({
    resolver: zodResolver(captureSchema),
    defaultValues: {
      text: "",
      account_id: "",
      category_id: "",
    },
  });

  useEffect(() => {
    const defaultAccountId = accountsQuery.data?.[0]?.id ?? "";
    if (editingTransaction) {
      transactionForm.reset({
        account_id: editingTransaction.account_id,
        category_id: editingTransaction.category_id ?? "",
        amount: editingTransaction.amount,
        type: editingTransaction.type,
        description: editingTransaction.description ?? "",
        date_accrual: formatDateTimeInputValue(editingTransaction.date_accrual),
        date_cash: formatDateTimeInputValue(editingTransaction.date_cash),
        is_reconciled: editingTransaction.is_reconciled,
      });
      return;
    }

    transactionForm.reset({
      account_id: defaultAccountId,
      category_id: "",
      amount: "",
      type: "expense",
      description: "",
      date_accrual: formatDateTimeInputValue(new Date().toISOString()),
      date_cash: formatDateTimeInputValue(new Date().toISOString()),
      is_reconciled: false,
    });
  }, [accountsQuery.data, editingTransaction, transactionForm]);

  useEffect(() => {
    captureForm.reset((current) => ({
      text: current.text,
      account_id: current.account_id || accountsQuery.data?.[0]?.id || "",
      category_id: current.category_id,
    }));
  }, [accountsQuery.data, captureForm]);

  useEffect(() => {
    if (!importAccountId && accountsQuery.data?.length) {
      setImportAccountId(accountsQuery.data[0].id);
    }
  }, [accountsQuery.data, importAccountId]);

  useEffect(() => {
    if (autoOpenNew) {
      setIsDialogOpen(true);
    }
  }, [autoOpenNew]);

  const refreshWorkspace = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      queryClient.invalidateQueries({ queryKey: ["reports"] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: createTransaction,
    onSuccess: async () => {
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
  });

  const patchMutation = useMutation({
    mutationFn: ({
      transactionId,
      payload,
    }: {
      transactionId: string;
      payload: Record<string, unknown>;
    }) => patchTransaction(transactionId, payload),
    onSuccess: async () => {
      setEditingTransaction(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: refreshWorkspace,
  });

  const captureMutation = useMutation({
    mutationFn: parseAndCreateTransaction,
    onSuccess: async () => {
      captureForm.reset({
        text: "",
        account_id: accountOptions[0]?.id ?? "",
        category_id: "",
      });
      await refreshWorkspace();
    },
  });

  const importMutation = useMutation({
    mutationFn: importTransactionsWorkbook,
    onSuccess: async (result) => {
      setImportSummary(result);
      setIsImportDialogOpen(false);
      setImportFile(null);
      await refreshWorkspace();
    },
  });

  const handleDialogChange = (open: boolean) => {
    setIsDialogOpen(open);
    if (!open) {
      setEditingTransaction(null);
      if (autoOpenNew || location.pathname === "/transactions/new") {
        navigate("/transactions", { replace: true });
      }
    }
  };

  const onSubmit = transactionForm.handleSubmit(async (values) => {
    if (editingTransaction) {
      await patchMutation.mutateAsync({
        transactionId: editingTransaction.id,
        payload: {
          amount: values.amount,
          category_id: values.category_id || null,
          description: values.description || null,
          date_accrual: toIsoDateTime(values.date_accrual),
          date_cash: toIsoDateTime(values.date_cash),
          is_reconciled: values.is_reconciled,
        },
      });
      return;
    }

    await createMutation.mutateAsync({
      account_id: values.account_id,
      category_id: values.category_id || null,
      counterparty_account_id: null,
      amount: values.amount,
      type: values.type,
      description: values.description || null,
      date_accrual: toIsoDateTime(values.date_accrual),
      date_cash: toIsoDateTime(values.date_cash),
      is_reconciled: values.is_reconciled,
    });
  });

  const onCaptureSubmit = captureForm.handleSubmit(async (values) => {
    await captureMutation.mutateAsync({
      text: values.text,
      account_id: values.account_id,
      category_id: values.category_id || null,
    });
  });

  const transactions = useMemo(
    () => transactionsQuery.data ?? [],
    [transactionsQuery.data],
  );

  return (
    <div className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "transactions.eyebrow" })}</p>
          <h2 className="section-title">{intl.formatMessage({ id: "transactions.title" })}</h2>
        </div>

        <div className="action-group">
          <Button
            disabled={!isOnline || !accountOptions.length}
            type="button"
            variant="secondary"
            onClick={() => setIsImportDialogOpen(true)}
          >
            <FileSpreadsheet size={16} />
            {intl.formatMessage({ id: "transactions.import" })}
          </Button>
          <Button
            disabled={!isOnline || !accountOptions.length}
            type="button"
            onClick={() => {
              setEditingTransaction(null);
              setIsDialogOpen(true);
            }}
          >
            <Plus size={16} />
            {intl.formatMessage({ id: "transactions.new" })}
          </Button>
        </div>
      </div>

      {importSummary ? (
        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "transactions.importTitle" })}</h3>
              <p className="muted-copy">
                {importSummary.skipped_count
                  ? intl.formatMessage(
                      { id: "transactions.importWithSkipped" },
                      {
                        count: importSummary.imported_count,
                        skipped: importSummary.skipped_count,
                      },
                    )
                  : intl.formatMessage(
                      { id: "transactions.importSummary" },
                      { count: importSummary.imported_count },
                    )}
              </p>
            </div>
          </div>
          {importSummary.errors.length ? (
            <div className="list-stack">
              <div className="muted-copy">{intl.formatMessage({ id: "transactions.importErrors" })}</div>
              {importSummary.errors.map((error) => (
                <div key={`${error.row_number}-${error.message}`} className="callout">
                  #{error.row_number}: {error.message}
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      <div className="content-grid">
        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "dashboard.quickCaptureTitle" })}</h3>
              <p className="muted-copy">{intl.formatMessage({ id: "transactions.quickCaptureCopy" })}</p>
            </div>
            <span className="pill">
              <WandSparkles size={14} />
              {intl.formatMessage({ id: "transactions.parsePill" })}
            </span>
          </div>

          <form className="form-stack" onSubmit={onCaptureSubmit}>
            <label className="field">
              <span>{intl.formatMessage({ id: "dashboard.text" })}</span>
              <textarea
                rows={3}
                placeholder={intl.formatMessage({ id: "transactions.placeholder" })}
                {...captureForm.register("text")}
              />
            </label>

            <div className="field-grid field-grid--two">
              <label className="field">
                <span>{intl.formatMessage({ id: "common.account" })}</span>
                <select {...captureForm.register("account_id")}>
                  <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
                  {accountOptions.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>{intl.formatMessage({ id: "common.category" })}</span>
                <select {...captureForm.register("category_id")}>
                  <option value="">{intl.formatMessage({ id: "common.autoOrNone" })}</option>
                  {categoryOptions.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {captureMutation.error ? (
              <div className="callout callout--danger">{captureMutation.error.message}</div>
            ) : null}

            <Button
              disabled={!isOnline || captureMutation.isPending || !accountOptions.length}
              type="submit"
            >
              {captureMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "transactions.parse" })}
            </Button>
          </form>
        </Card>

        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "transactions.ledgerTitle" })}</h3>
              <p className="muted-copy">
                {intl.formatMessage({ id: "transactions.recordedCount" }, { count: transactions.length })}
              </p>
            </div>
          </div>

          <div className="list-stack">
            {transactions.length ? (
              transactions.map((transaction) => (
                <article className="transaction-row" key={transaction.id}>
                  <div>
                    <div className="transaction-row__title">
                      {transaction.description ?? intl.formatMessage({ id: "transactions.untitled" })}
                    </div>
                    <div className="transaction-row__meta">
                      {transactionTypeLabel(intl, transaction.type)} · {formatShortDate(transaction.date_cash)}
                    </div>
                  </div>

                  <div className="transaction-row__actions">
                    <strong>{formatCurrency(transaction.amount)}</strong>
                    <div className="row-button-group">
                      <button
                        className="inline-action"
                        disabled={!isOnline}
                        type="button"
                        onClick={() => {
                          setEditingTransaction(transaction);
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
                          if (window.confirm(intl.formatMessage({ id: "transactions.deleteConfirm" }))) {
                            void deleteMutation.mutateAsync(transaction.id);
                          }
                        }}
                      >
                        <Trash2 size={14} />
                        {intl.formatMessage({ id: "common.delete" })}
                      </button>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state">{intl.formatMessage({ id: "transactions.empty" })}</div>
            )}
          </div>
        </Card>
      </div>

      <DialogSheet
        description={
          editingTransaction
            ? intl.formatMessage({ id: "transactions.patchDescription" })
            : intl.formatMessage({ id: "transactions.createDescription" })
        }
        onOpenChange={handleDialogChange}
        open={isDialogOpen}
        title={
          editingTransaction
            ? intl.formatMessage({ id: "transactions.edit" })
            : intl.formatMessage({ id: "transactions.new" })
        }
      >
        <form className="form-stack" onSubmit={onSubmit}>
          {editingTransaction ? (
            <div className="callout">
              {intl.formatMessage({ id: "transactions.patchCallout" })}
            </div>
          ) : (
            <div className="field-grid field-grid--two">
              <label className="field">
                <span>{intl.formatMessage({ id: "common.account" })}</span>
                <select {...transactionForm.register("account_id")}>
                  <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
                  {accountOptions.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>{intl.formatMessage({ id: "common.type" })}</span>
                <select {...transactionForm.register("type")}>
                  {transactionTypes.map((type) => (
                    <option key={type} value={type}>
                      {transactionTypeLabel(intl, type)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.amount" })}</span>
              <input inputMode="decimal" placeholder="0.00" {...transactionForm.register("amount")} />
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.category" })}</span>
              <select {...transactionForm.register("category_id")}>
                <option value="">{intl.formatMessage({ id: "common.none" })}</option>
                {categoryOptions.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.description" })}</span>
            <input
              placeholder={intl.formatMessage({ id: "transactions.descriptionPlaceholder" })}
              {...transactionForm.register("description")}
            />
          </label>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "transactions.accrualDate" })}</span>
              <input type="datetime-local" {...transactionForm.register("date_accrual")} />
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "transactions.cashDate" })}</span>
              <input type="datetime-local" {...transactionForm.register("date_cash")} />
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...transactionForm.register("is_reconciled")} />
            <span>{intl.formatMessage({ id: "transactions.reconciled" })}</span>
          </label>

          {createMutation.error || patchMutation.error ? (
            <div className="callout callout--danger">
              {createMutation.error?.message ?? patchMutation.error?.message}
            </div>
          ) : null}

          <Button
            disabled={!isOnline || createMutation.isPending || patchMutation.isPending}
            type="submit"
          >
            {editingTransaction
              ? patchMutation.isPending
                ? intl.formatMessage({ id: "common.saving" })
                : intl.formatMessage({ id: "transactions.saveChanges" })
              : createMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "transactions.createAction" })}
          </Button>
        </form>
      </DialogSheet>

      <DialogSheet
        description={intl.formatMessage({ id: "transactions.importDescription" })}
        onOpenChange={setIsImportDialogOpen}
        open={isImportDialogOpen}
        title={intl.formatMessage({ id: "transactions.importTitle" })}
      >
        <form
          className="form-stack"
          onSubmit={(event) => {
            event.preventDefault();
            if (!importFile || !importAccountId) {
              return;
            }
            void importMutation.mutateAsync({
              account_id: importAccountId,
              file: importFile,
            });
          }}
        >
          <div className="callout">{intl.formatMessage({ id: "transactions.importHint" })}</div>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.account" })}</span>
            <select value={importAccountId} onChange={(event) => setImportAccountId(event.target.value)}>
              <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
              {accountOptions.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "transactions.importFile" })}</span>
            <input
              accept=".xlsx"
              type="file"
              onChange={(event) => setImportFile(event.target.files?.[0] ?? null)}
            />
          </label>

          {importMutation.error ? (
            <div className="callout callout--danger">{importMutation.error.message}</div>
          ) : null}

          <Button
            disabled={!isOnline || importMutation.isPending || !importAccountId || !importFile}
            type="submit"
          >
            {importMutation.isPending
              ? intl.formatMessage({ id: "transactions.importing" })
              : intl.formatMessage({ id: "transactions.importAction" })}
          </Button>
        </form>
      </DialogSheet>
    </div>
  );
}
