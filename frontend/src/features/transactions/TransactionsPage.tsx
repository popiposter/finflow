import { zodResolver } from "@hookform/resolvers/zod";
import {
  type ColumnDef,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { toast } from "sonner";

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
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { formatImportRowError } from "@/shared/lib/api-errors";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
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
import { DataTable } from "@/shared/ui/DataTable";
import { DialogSheet } from "@/shared/ui/DialogSheet";
import { SkeletonRows } from "@/shared/ui/Skeleton";
import { useDebouncedValue } from "@/shared/lib/useDebouncedValue";
import { TransactionsTableToolbar } from "@/features/transactions/TransactionsTableToolbar";
import {
  TransactionsQuickCaptureCard,
  type CaptureValues,
} from "@/features/transactions/TransactionsQuickCaptureCard";

const transactionTypes = [
  "expense",
  "income",
  "payment",
  "refund",
  "transfer",
  "adjustment",
] as const satisfies TransactionType[];

type TransactionFormValues = {
  account_id: string;
  category_id?: string;
  amount: string;
  type: TransactionType;
  description?: string;
  date_accrual: string;
  date_cash: string;
  is_reconciled: boolean;
};

type TransactionsPageProps = {
  autoOpenNew?: boolean;
};

type ReconciledFilter = "all" | "yes" | "no";

type TransactionTableRow = {
  id: string;
  type: TransactionType;
  typeLabel: string;
  description: string;
  amount: string;
  dateCash: string;
  dateCashLabel: string;
  accountLabel: string;
  categoryLabel: string;
  isReconciled: boolean;
};

export function TransactionsPage({ autoOpenNew = false }: TransactionsPageProps) {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const transactionSchema = useMemo(
    () =>
      z.object({
        account_id: z.string().uuid(validation.invalidSelection),
        category_id: z.string().optional(),
        amount: z.string().trim().min(1, validation.required),
        type: z.enum(transactionTypes),
        description: z.string().optional(),
        date_accrual: z.string().min(1, validation.required),
        date_cash: z.string().min(1, validation.required),
        is_reconciled: z.boolean().default(false),
      }),
    [validation],
  );
  const captureSchema = useMemo(
    () =>
      z.object({
        text: z.string().trim().min(3, validation.shortCapture),
        account_id: z.string().uuid(validation.invalidSelection),
        category_id: z.string().optional(),
      }),
    [validation],
  );
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(autoOpenNew);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importAccountId, setImportAccountId] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importSummary, setImportSummary] = useState<TransactionWorkbookImportResponse | null>(null);
  const [globalSearch, setGlobalSearch] = useState(() => searchParams.get("q") ?? "");
  const [typeFilter, setTypeFilter] = useState<"all" | TransactionType>(() => {
    const value = searchParams.get("type");
    return value && transactionTypes.includes(value as TransactionType)
      ? (value as TransactionType)
      : "all";
  });
  const [accountFilter, setAccountFilter] = useState(() => searchParams.get("account") ?? "all");
  const [categoryFilter, setCategoryFilter] = useState(() => searchParams.get("category") ?? "all");
  const [reconciledFilter, setReconciledFilter] = useState<ReconciledFilter>(() => {
    const value = searchParams.get("rec");
    return value === "yes" || value === "no" ? value : "all";
  });
  const [dateFrom, setDateFrom] = useState(() => searchParams.get("from") ?? "");
  const [dateTo, setDateTo] = useState(() => searchParams.get("to") ?? "");
  const [sorting, setSorting] = useState<SortingState>(() => {
    const sortParam = searchParams.get("sort");
    if (!sortParam) {
      return [{ id: "dateCash", desc: true }];
    }

    const [id, direction] = sortParam.split(":");
    const allowedIds = new Set([
      "dateCash",
      "typeLabel",
      "description",
      "accountLabel",
      "categoryLabel",
      "amount",
      "isReconciled",
    ]);

    if (!allowedIds.has(id)) {
      return [{ id: "dateCash", desc: true }];
    }

    return [{ id, desc: direction !== "asc" }];
  });
  const debouncedSearch = useDebouncedValue(globalSearch, 250);

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
      toast.success(intl.formatMessage({ id: "toast.transactionCreated" }));
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
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
      toast.success(intl.formatMessage({ id: "toast.transactionUpdated" }));
      setEditingTransaction(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.transactionDeleted" }));
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const captureMutation = useMutation({
    mutationFn: parseAndCreateTransaction,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.transactionCreated" }));
      captureForm.reset({
        text: "",
        account_id: accountOptions[0]?.id ?? "",
        category_id: "",
      });
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const importMutation = useMutation({
    mutationFn: importTransactionsWorkbook,
    onSuccess: async (result) => {
      toast.success(intl.formatMessage({ id: "toast.importComplete" }, { count: result.imported_count }));
      setImportSummary(result);
      setIsImportDialogOpen(false);
      setImportFile(null);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
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

  const accountById = useMemo(
    () => new Map(accountOptions.map((account) => [account.id, account.name])),
    [accountOptions],
  );

  const categoryById = useMemo(
    () => new Map(categoryOptions.map((category) => [category.id, category.name])),
    [categoryOptions],
  );

  const tableRows = useMemo<TransactionTableRow[]>(
    () =>
      transactions.map((transaction) => ({
        id: transaction.id,
        type: transaction.type,
        typeLabel: transactionTypeLabel(intl, transaction.type),
        description: transaction.description ?? intl.formatMessage({ id: "transactions.untitled" }),
        amount: transaction.amount,
        dateCash: transaction.date_cash,
        dateCashLabel: formatShortDate(transaction.date_cash),
        accountLabel:
          accountById.get(transaction.account_id) ?? intl.formatMessage({ id: "common.na" }),
        categoryLabel: transaction.category_id
          ? categoryById.get(transaction.category_id) ?? intl.formatMessage({ id: "common.na" })
          : intl.formatMessage({ id: "common.none" }),
        isReconciled: transaction.is_reconciled,
      })),
    [transactions, intl, accountById, categoryById],
  );

  const filteredRows = useMemo(() => {
    const normalizedSearch = debouncedSearch.trim().toLowerCase();

    return tableRows.filter((row) => {
      if (typeFilter !== "all" && row.type !== typeFilter) {
        return false;
      }

      if (accountFilter !== "all" && row.accountLabel !== accountFilter) {
        return false;
      }

      if (categoryFilter !== "all" && row.categoryLabel !== categoryFilter) {
        return false;
      }

      if (reconciledFilter === "yes" && !row.isReconciled) {
        return false;
      }

      if (reconciledFilter === "no" && row.isReconciled) {
        return false;
      }

      if (dateFrom && row.dateCash.slice(0, 10) < dateFrom) {
        return false;
      }

      if (dateTo && row.dateCash.slice(0, 10) > dateTo) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      return [
        row.description,
        row.typeLabel,
        row.accountLabel,
        row.categoryLabel,
        row.amount,
        row.dateCashLabel,
      ].some((value) => value.toLowerCase().includes(normalizedSearch));
    });
  }, [tableRows, debouncedSearch, typeFilter, accountFilter, categoryFilter, reconciledFilter, dateFrom, dateTo]);

  const tableColumns = useMemo<ColumnDef<TransactionTableRow>[]>(
    () => [
      {
        accessorKey: "dateCash",
        header: intl.formatMessage({ id: "transactions.table.cashDate" }),
        cell: ({ row }) => row.original.dateCashLabel,
      },
      {
        accessorKey: "typeLabel",
        header: intl.formatMessage({ id: "common.type" }),
      },
      {
        accessorKey: "description",
        header: intl.formatMessage({ id: "common.description" }),
      },
      {
        accessorKey: "accountLabel",
        header: intl.formatMessage({ id: "common.account" }),
      },
      {
        accessorKey: "categoryLabel",
        header: intl.formatMessage({ id: "common.category" }),
      },
      {
        accessorKey: "amount",
        header: intl.formatMessage({ id: "common.amount" }),
        cell: ({ row }) => (
          <span className="table-number">{formatCurrency(row.original.amount)}</span>
        ),
      },
      {
        accessorKey: "isReconciled",
        header: intl.formatMessage({ id: "transactions.reconciled" }),
        cell: ({ row }) =>
          row.original.isReconciled
            ? intl.formatMessage({ id: "transactions.table.reconciledYes" })
            : intl.formatMessage({ id: "transactions.table.reconciledNo" }),
      },
      {
        id: "actions",
        enableSorting: false,
        header: intl.formatMessage({ id: "transactions.table.actions" }),
        cell: ({ row }) => {
          const transaction = transactions.find((item) => item.id === row.original.id);

          if (!transaction) {
            return null;
          }

          return (
            <div className="table-actions">
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
          );
        },
      },
    ],
    [intl, transactions, isOnline, deleteMutation],
  );

  const table = useReactTable({
    data: filteredRows,
    columns: tableColumns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const accountFilterOptions = useMemo(
    () => ["all", ...Array.from(new Set(tableRows.map((row) => row.accountLabel)))],
    [tableRows],
  );

  const categoryFilterOptions = useMemo(
    () => ["all", ...Array.from(new Set(tableRows.map((row) => row.categoryLabel)))],
    [tableRows],
  );

  const transactionTypeOptions = useMemo(
    () =>
      transactionTypes.map((type) => ({
        value: type,
        label: transactionTypeLabel(intl, type),
      })),
    [intl],
  );

  const clearFilters = () => {
    setGlobalSearch("");
    setTypeFilter("all");
    setAccountFilter("all");
    setCategoryFilter("all");
    setReconciledFilter("all");
    setDateFrom("");
    setDateTo("");
    setSorting([{ id: "dateCash", desc: true }]);
  };

  useEffect(() => {
    const next = new URLSearchParams();

    if (globalSearch.trim()) {
      next.set("q", globalSearch.trim());
    }
    if (typeFilter !== "all") {
      next.set("type", typeFilter);
    }
    if (accountFilter !== "all") {
      next.set("account", accountFilter);
    }
    if (categoryFilter !== "all") {
      next.set("category", categoryFilter);
    }
    if (reconciledFilter !== "all") {
      next.set("rec", reconciledFilter);
    }
    if (dateFrom) {
      next.set("from", dateFrom);
    }
    if (dateTo) {
      next.set("to", dateTo);
    }

    const primarySort = sorting[0];
    if (primarySort) {
      next.set("sort", `${String(primarySort.id)}:${primarySort.desc ? "desc" : "asc"}`);
    }

    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [
    accountFilter,
    categoryFilter,
    dateFrom,
    dateTo,
    globalSearch,
    reconciledFilter,
    searchParams,
    setSearchParams,
    sorting,
    typeFilter,
  ]);

  return (
    <AnimatedPage className="page-stack">
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
                  #{error.row_number}: {formatImportRowError(intl, error)}
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      <div className="content-grid">
        <TransactionsQuickCaptureCard
          accountOptions={accountOptions}
          captureForm={captureForm}
          categoryOptions={categoryOptions}
          error={captureMutation.error}
          isOnline={isOnline}
          isSubmitting={captureMutation.isPending}
          onSubmit={onCaptureSubmit}
        />

        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "transactions.ledgerTitle" })}</h3>
              <p className="muted-copy">
                {intl.formatMessage({ id: "transactions.recordedCount" }, { count: transactions.length })}
              </p>
            </div>
          </div>

          <TransactionsTableToolbar
            accountFilter={accountFilter}
            accountOptions={accountFilterOptions.slice(1)}
            categoryFilter={categoryFilter}
            categoryOptions={categoryFilterOptions.slice(1)}
            dateFrom={dateFrom}
            dateTo={dateTo}
            globalSearch={globalSearch}
            onAccountFilterChange={setAccountFilter}
            onCategoryFilterChange={setCategoryFilter}
            onClearFilters={clearFilters}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            onGlobalSearchChange={setGlobalSearch}
            onReconciledFilterChange={setReconciledFilter}
            onTypeFilterChange={setTypeFilter}
            reconciledFilter={reconciledFilter}
            transactionTypeOptions={transactionTypeOptions}
            typeFilter={typeFilter}
          />

          <DataTable
            emptyMessage={intl.formatMessage({ id: "transactions.table.emptyFiltered" })}
            table={table}
          />

          <div className="list-stack mobile-only">
            {transactionsQuery.isLoading ? (
              <SkeletonRows count={5} />
            ) : transactions.length ? (
              transactions.map((transaction) => (
                <article className="transaction-row" key={transaction.id}>
                  <div>
                    <div className="transaction-row__title">
                      {transaction.description ?? intl.formatMessage({ id: "transactions.untitled" })}
                    </div>
                    <div className="transaction-row__meta">
                      <span className={`status-badge status-badge--${transaction.type === "income" ? "income" : "expense"}`}>
                        {transactionTypeLabel(intl, transaction.type)}
                      </span>
                      {" · "}
                      {formatShortDate(transaction.date_cash)}
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
                {getFieldErrorMessage(transactionForm.formState.errors.account_id) ? (
                  <small className="field-error">
                    {getFieldErrorMessage(transactionForm.formState.errors.account_id)}
                  </small>
                ) : null}
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
              {getFieldErrorMessage(transactionForm.formState.errors.amount) ? (
                <small className="field-error">
                  {getFieldErrorMessage(transactionForm.formState.errors.amount)}
                </small>
              ) : null}
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
              {getFieldErrorMessage(transactionForm.formState.errors.date_accrual) ? (
                <small className="field-error">
                  {getFieldErrorMessage(transactionForm.formState.errors.date_accrual)}
                </small>
              ) : null}
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "transactions.cashDate" })}</span>
              <input type="datetime-local" {...transactionForm.register("date_cash")} />
              {getFieldErrorMessage(transactionForm.formState.errors.date_cash) ? (
                <small className="field-error">
                  {getFieldErrorMessage(transactionForm.formState.errors.date_cash)}
                </small>
              ) : null}
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...transactionForm.register("is_reconciled")} />
            <span>{intl.formatMessage({ id: "transactions.reconciled" })}</span>
          </label>

          {createMutation.error || patchMutation.error ? (
            <ApiErrorCallout error={createMutation.error ?? patchMutation.error} />
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
            <ApiErrorCallout error={importMutation.error} />
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
    </AnimatedPage>
  );
}
