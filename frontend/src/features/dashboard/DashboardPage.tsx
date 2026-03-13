import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, CalendarClock, Sparkles, Wallet } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { listAccounts } from "@/shared/api/accounts";
import { listCategories } from "@/shared/api/categories";
import { generateDueProjections } from "@/shared/api/plans";
import { listProjectedTransactions } from "@/shared/api/projections";
import { getForecast, getLedgerReport } from "@/shared/api/reports";
import { parseAndCreateTransaction } from "@/shared/api/transactions";
import { useAppIntl } from "@/shared/lib/i18n";
import { projectionStatusLabel, transactionTypeLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";

const captureSchema = z.object({
  text: z.string().min(3),
  account_id: z.string().uuid(),
  category_id: z.string().optional(),
});

type CaptureValues = z.infer<typeof captureSchema>;

export function DashboardPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const captureForm = useForm<CaptureValues>({
    resolver: zodResolver(captureSchema),
    defaultValues: {
      text: "",
      account_id: "",
      category_id: "",
    },
  });

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });
  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: listCategories,
  });
  const forecastQuery = useQuery({
    queryKey: ["cashflow", "forecast", todayOffset(30)],
    queryFn: () => getForecast(todayOffset(30)),
  });
  const ledgerQuery = useQuery({
    queryKey: ["dashboard", "ledger", todayOffset(-7), todayOffset(14)],
    queryFn: () =>
      getLedgerReport({
        from: todayOffset(-7),
        to: todayOffset(14),
        mode: "mixed",
      }),
  });
  const pendingQuery = useQuery({
    queryKey: ["projections", "dashboard-pending"],
    queryFn: () => listProjectedTransactions({ status: "pending" }),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateDueProjections(todayOffset(0)),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["plans"] }),
        queryClient.invalidateQueries({ queryKey: ["projections"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      ]);
    },
  });

  const captureMutation = useMutation({
    mutationFn: parseAndCreateTransaction,
    onSuccess: async () => {
      captureForm.reset({
        text: "",
        account_id: accountsQuery.data?.[0]?.id ?? "",
        category_id: "",
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      ]);
    },
  });

  useEffect(() => {
    captureForm.reset((current) => ({
      text: current.text,
      account_id: current.account_id || accountsQuery.data?.[0]?.id || "",
      category_id: current.category_id,
    }));
  }, [accountsQuery.data, captureForm]);

  const onCaptureSubmit = captureForm.handleSubmit(async (values) => {
    await captureMutation.mutateAsync({
      text: values.text,
      account_id: values.account_id,
      category_id: values.category_id || null,
    });
  });

  const pendingCount = pendingQuery.data?.length ?? 0;
  const recentRows = ledgerQuery.data?.rows.slice(0, 6) ?? [];

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Installable finance cockpit</p>
          <p className="eyebrow">{intl.formatMessage({ id: "dashboard.eyebrow" })}</p>
          <h2 className="hero-title">{intl.formatMessage({ id: "dashboard.title" })}</h2>
          <p className="hero-subtitle">{intl.formatMessage({ id: "dashboard.subtitle" })}</p>
        </div>

        <div className="hero-actions">
          <Link className="button button--primary button-link" to="/transactions/new">
            {intl.formatMessage({ id: "dashboard.addTransaction" })}
          </Link>
          <Button
            disabled={!isOnline || generateMutation.isPending}
            type="button"
            variant="secondary"
            onClick={() => void generateMutation.mutateAsync()}
          >
            {generateMutation.isPending
              ? intl.formatMessage({ id: "dashboard.generating" })
              : intl.formatMessage({ id: "dashboard.generateDueProjections" })}
          </Button>
        </div>
      </section>

      <div className="metric-grid">
        <Card className="metric-card">
          <div className="metric-icon">
            <Wallet size={20} />
          </div>
          <div className="metric-label">{intl.formatMessage({ id: "common.projectedBalance" })}</div>
          <div className="metric-value">
            {formatCurrency(forecastQuery.data?.projected_balance)}
          </div>
          <div className="metric-meta">
            {intl.formatMessage(
              { id: "dashboard.currentValue" },
              { value: formatCurrency(forecastQuery.data?.current_balance) },
            )}
          </div>
        </Card>

        <Card className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={20} />
          </div>
          <div className="metric-label">{intl.formatMessage({ id: "dashboard.pendingProjections" })}</div>
          <div className="metric-value">{pendingCount}</div>
          <div className="metric-meta">
            {intl.formatMessage(
              { id: "dashboard.throughDate" },
              { date: formatShortDate(todayOffset(30)) },
            )}
          </div>
        </Card>

        <Card className="metric-card">
          <div className="metric-icon">
            <Sparkles size={20} />
          </div>
          <div className="metric-label">{intl.formatMessage({ id: "common.projectedIncome" })}</div>
          <div className="metric-value">
            {formatCurrency(forecastQuery.data?.projected_income)}
          </div>
          <div className="metric-meta">
            {intl.formatMessage(
              { id: "dashboard.expensesValue" },
              { value: formatCurrency(forecastQuery.data?.projected_expense) },
            )}
          </div>
        </Card>
      </div>

      <div className="content-grid">
        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "dashboard.quickCaptureTitle" })}</h3>
              <p className="muted-copy">{intl.formatMessage({ id: "dashboard.quickCaptureCopy" })}</p>
            </div>
          </div>

          {!isOnline ? (
            <div className="callout">{intl.formatMessage({ id: "dashboard.quickCaptureOffline" })}</div>
          ) : null}

          <form className="form-stack" onSubmit={onCaptureSubmit}>
            <label className="field">
              <span>{intl.formatMessage({ id: "dashboard.text" })}</span>
              <textarea
                placeholder={intl.formatMessage({ id: "dashboard.quickCapturePlaceholder" })}
                rows={3}
                {...captureForm.register("text")}
              />
            </label>

            <div className="field-grid field-grid--two">
              <label className="field">
                <span>{intl.formatMessage({ id: "common.account" })}</span>
                <select {...captureForm.register("account_id")}>
                  <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
                  {accountsQuery.data?.map((account) => (
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
                  {categoriesQuery.data?.map((category) => (
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
              disabled={!isOnline || captureMutation.isPending || !accountsQuery.data?.length}
              type="submit"
            >
              {captureMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "dashboard.parseAndCreate" })}
            </Button>
          </form>
        </Card>

        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">{intl.formatMessage({ id: "dashboard.recentCashflowTitle" })}</h3>
              <p className="muted-copy">{intl.formatMessage({ id: "dashboard.recentCashflowCopy" })}</p>
            </div>
            <Link className="inline-link" to="/reports">
              {intl.formatMessage({ id: "dashboard.openReports" })} <ArrowRight size={16} />
            </Link>
          </div>

          <div className="list-stack">
            {recentRows.length ? (
              recentRows.map((row) => (
                <article className="ledger-row" key={row.row_id}>
                  <div>
                    <div className="ledger-row__title">
                      {row.description ?? intl.formatMessage({ id: "dashboard.untitledRow" })}
                    </div>
                    <div className="ledger-row__meta">
                      {typeof row.type === "string" ? row.type : transactionTypeLabel(intl, row.type)} ·{" "}
                      {formatShortDate(row.date)}
                    </div>
                  </div>
                  <div className="ledger-row__amount">
                    <strong>{formatCurrency(row.amount)}</strong>
                    <span>{projectionStatusLabel(intl, row.status as "pending" | "confirmed" | "skipped")}</span>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state">{intl.formatMessage({ id: "dashboard.noCashflow" })}</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
