import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, CalendarClock, Sparkles, TrendingUp, Wallet } from "lucide-react";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";
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
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

type CaptureValues = {
  text: string;
  account_id: string;
  category_id?: string;
};

const DONUT_COLORS = ["#10B981", "#0D3B2E", "#F59E0B", "#3B82F6", "#8B5CF6", "#EC4899"];

export function DashboardPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const captureSchema = useMemo(
    () =>
      z.object({
        text: z.string().trim().min(3, validation.shortCapture),
        account_id: z.string().uuid(validation.invalidSelection),
        category_id: z.string().optional(),
      }),
    [validation],
  );
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
      toast.success(intl.formatMessage({ id: "toast.projectionsGenerated" }));
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["plans"] }),
        queryClient.invalidateQueries({ queryKey: ["projections"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      ]);
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
        account_id: accountsQuery.data?.[0]?.id ?? "",
        category_id: "",
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["transactions"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      ]);
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
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

  // Prepare cashflow trend data for area chart
  const cashflowChartData = useMemo(() => {
    if (!ledgerQuery.data?.rows) return [];
    return ledgerQuery.data.rows.map((row) => ({
      date: formatShortDate(row.date),
      balance: Number(row.balance_after),
      amount: Number(row.amount),
    }));
  }, [ledgerQuery.data]);

  // Prepare income vs expense donut
  const incomeExpenseData = useMemo(() => {
    if (!forecastQuery.data) return [];
    const income = Math.abs(Number(forecastQuery.data.projected_income));
    const expense = Math.abs(Number(forecastQuery.data.projected_expense));
    if (income === 0 && expense === 0) return [];
    return [
      { name: intl.formatMessage({ id: "common.income" }), value: income },
      { name: intl.formatMessage({ id: "common.expenses" }), value: expense },
    ];
  }, [forecastQuery.data, intl]);

  const isLoadingMetrics = forecastQuery.isLoading || pendingQuery.isLoading;

  return (
    <AnimatedPage className="page-stack">
      <section className="hero-panel">
        <div className="hero-copy">
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
        {isLoadingMetrics ? (
          <>
            <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
            <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
            <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
          </>
        ) : (
          <>
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
          </>
        )}
      </div>

      {/* Charts row */}
      <div className="content-grid">
        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">
                <TrendingUp size={16} style={{ marginRight: "0.5rem", verticalAlign: "middle" }} />
                {intl.formatMessage({ id: "dashboard.cashflowTrend" })}
              </h3>
            </div>
            <Link className="inline-link" to="/reports">
              {intl.formatMessage({ id: "dashboard.openReports" })} <ArrowRight size={16} />
            </Link>
          </div>

          {ledgerQuery.isLoading ? (
            <Skeleton variant="chart" />
          ) : cashflowChartData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={cashflowChartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={60} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.8125rem",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="balance"
                    stroke="var(--accent)"
                    strokeWidth={2}
                    fill="url(#balanceGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">{intl.formatMessage({ id: "dashboard.noCashflow" })}</div>
          )}
        </Card>

        <Card>
          <div className="section-header">
            <h3 className="section-title">{intl.formatMessage({ id: "dashboard.incomeVsExpense" })}</h3>
          </div>

          {forecastQuery.isLoading ? (
            <Skeleton variant="chart" />
          ) : incomeExpenseData.length > 0 ? (
            <div className="chart-container chart-container--donut">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={incomeExpenseData}
                    cx="50%"
                    cy="50%"
                    innerRadius="55%"
                    outerRadius="80%"
                    paddingAngle={4}
                    dataKey="value"
                    stroke="none"
                  >
                    {incomeExpenseData.map((_, index) => (
                      <Cell key={index} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatCurrency(String(value))}
                    contentStyle={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.8125rem",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="chart-legend">
                {incomeExpenseData.map((entry, index) => (
                  <div key={entry.name} className="chart-legend-item">
                    <span
                      className="chart-legend-dot"
                      style={{ background: DONUT_COLORS[index % DONUT_COLORS.length] }}
                    />
                    <span className="chart-legend-label">{entry.name}</span>
                    <span className="chart-legend-value">{formatCurrency(String(entry.value))}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state">{intl.formatMessage({ id: "dashboard.noForecastData" })}</div>
          )}
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
              {getFieldErrorMessage(captureForm.formState.errors.text) ? (
                <small className="field-error">
                  {getFieldErrorMessage(captureForm.formState.errors.text)}
                </small>
              ) : null}
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
                {getFieldErrorMessage(captureForm.formState.errors.account_id) ? (
                  <small className="field-error">
                    {getFieldErrorMessage(captureForm.formState.errors.account_id)}
                  </small>
                ) : null}
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
              <ApiErrorCallout error={captureMutation.error} />
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

          {ledgerQuery.isLoading ? (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {Array.from({ length: 4 }, (_, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "grid", gap: "0.25rem", flex: 1 }}>
                    <Skeleton variant="text" width="70%" />
                    <Skeleton variant="text" width="40%" />
                  </div>
                  <Skeleton variant="text" width="80px" />
                </div>
              ))}
            </div>
          ) : (
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
          )}
        </Card>
      </div>
    </AnimatedPage>
  );
}
