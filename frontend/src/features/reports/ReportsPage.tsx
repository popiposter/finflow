import * as Tabs from "@radix-ui/react-tabs";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getCashflowReport,
  getForecast,
  getLedgerReport,
  getPnlReport,
} from "@/shared/api/reports";
import type { CashflowLedgerMode, ReportGroupBy } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { ledgerModeLabel } from "@/shared/lib/labels";
import { formatCurrency } from "@/shared/lib/utils";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { AnimatedList, AnimatedListItem } from "@/shared/ui/AnimatedList";
import { Card } from "@/shared/ui/Card";
import { Skeleton, SkeletonRows } from "@/shared/ui/Skeleton";

export function ReportsPage() {
  const intl = useAppIntl();
  const [aggregateStart, setAggregateStart] = useState(offsetDate(-30));
  const [aggregateEnd, setAggregateEnd] = useState(offsetDate(30));
  const [groupBy, setGroupBy] = useState<ReportGroupBy>("by_category");
  const [ledgerMode, setLedgerMode] = useState<CashflowLedgerMode>("mixed");
  const [includeSkipped, setIncludeSkipped] = useState(false);
  const [forecastTarget, setForecastTarget] = useState(offsetDate(30));

  const pnlQuery = useQuery({
    queryKey: ["reports", "pnl", aggregateStart, aggregateEnd, groupBy],
    queryFn: () =>
      getPnlReport({
        start_date: aggregateStart,
        end_date: aggregateEnd,
        group_by: groupBy,
      }),
  });

  const cashflowQuery = useQuery({
    queryKey: ["reports", "cashflow", aggregateStart, aggregateEnd, groupBy],
    queryFn: () =>
      getCashflowReport({
        start_date: aggregateStart,
        end_date: aggregateEnd,
        group_by: groupBy,
      }),
  });

  const ledgerQuery = useQuery({
    queryKey: ["cashflow", "report", aggregateStart, aggregateEnd, ledgerMode, includeSkipped],
    queryFn: () =>
      getLedgerReport({
        from: aggregateStart,
        to: aggregateEnd,
        mode: ledgerMode,
        include_skipped: includeSkipped,
      }),
  });

  const forecastQuery = useQuery({
    queryKey: ["cashflow", "forecast", forecastTarget],
    queryFn: () => getForecast(forecastTarget),
  });

  const CHART_COLORS = ["#10B981", "#0D3B2E", "#F59E0B", "#3B82F6", "#8B5CF6", "#EC4899"];

  const pnlChartData = useMemo(() => {
    if (!pnlQuery.data) return [];
    const source =
      groupBy === "by_type"
        ? pnlQuery.data.totals_by_type.map((item) => ({
            name: item.type,
            value: Math.abs(Number(item.total)),
          }))
        : pnlQuery.data.totals_by_category.map((item) => ({
            name: item.category_name ?? "Uncategorized",
            value: Math.abs(Number(item.total)),
          }));
    return source.filter((d) => d.value > 0);
  }, [pnlQuery.data, groupBy]);

  const cashflowChartData = useMemo(() => {
    if (!cashflowQuery.data) return [];
    const source =
      groupBy === "by_type"
        ? cashflowQuery.data.totals_by_type.map((item) => ({
            name: item.type,
            value: Math.abs(Number(item.total)),
          }))
        : cashflowQuery.data.totals_by_category.map((item) => ({
            name: item.category_name ?? "Uncategorized",
            value: Math.abs(Number(item.total)),
          }));
    return source.filter((d) => d.value > 0);
  }, [cashflowQuery.data, groupBy]);

  return (
    <AnimatedPage className="page-stack">
      <Card>
        <div className="field-grid field-grid--three">
          <label className="field">
            <span>{intl.formatMessage({ id: "common.from" })}</span>
            <input type="date" value={aggregateStart} onChange={(event) => setAggregateStart(event.target.value)} />
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.to" })}</span>
            <input type="date" value={aggregateEnd} onChange={(event) => setAggregateEnd(event.target.value)} />
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "reports.group" })}</span>
            <select value={groupBy} onChange={(event) => setGroupBy(event.target.value as ReportGroupBy)}>
              <option value="by_category">{intl.formatMessage({ id: "reports.groupByCategory" })}</option>
              <option value="by_type">{intl.formatMessage({ id: "reports.groupByType" })}</option>
            </select>
          </label>
        </div>
      </Card>

      <Tabs.Root className="tabs-root" defaultValue="forecast">
        <Tabs.List className="tabs-list" aria-label={intl.formatMessage({ id: "reports.views" })}>
          <Tabs.Trigger className="tab-trigger" value="forecast">
            {intl.formatMessage({ id: "reports.forecast" })}
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="ledger">
            {intl.formatMessage({ id: "reports.unifiedLedger" })}
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="pnl">
            {intl.formatMessage({ id: "reports.pnl" })}
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="cash">
            {intl.formatMessage({ id: "reports.cashflow" })}
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content className="tab-panel" value="forecast">
          <Card>
            <div className="field-grid field-grid--two">
              <label className="field">
                <span>{intl.formatMessage({ id: "reports.targetDate" })}</span>
                <input
                  type="date"
                  value={forecastTarget}
                  onChange={(event) => setForecastTarget(event.target.value)}
                />
              </label>
            </div>

            {forecastQuery.isLoading ? (
              <div className="metric-grid">
                <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
                <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
                <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
                <Card className="metric-card"><Skeleton variant="metric" /><Skeleton variant="text" width="60%" /></Card>
              </div>
            ) : (
              <div className="metric-grid">
                <MetricCard label={intl.formatMessage({ id: "common.currentBalance" })} value={forecastQuery.data?.current_balance} />
                <MetricCard label={intl.formatMessage({ id: "common.projectedIncome" })} value={forecastQuery.data?.projected_income} />
                <MetricCard label={intl.formatMessage({ id: "common.projectedExpense" })} value={forecastQuery.data?.projected_expense} />
                <MetricCard label={intl.formatMessage({ id: "common.projectedBalance" })} value={forecastQuery.data?.projected_balance} />
              </div>
            )}
          </Card>
        </Tabs.Content>

        <Tabs.Content className="tab-panel" value="ledger">
          <Card>
            <div className="field-grid field-grid--two">
              <label className="field">
                <span>{intl.formatMessage({ id: "reports.mode" })}</span>
                <select
                  value={ledgerMode}
                  onChange={(event) => setLedgerMode(event.target.value as CashflowLedgerMode)}
                >
                  <option value="mixed">{ledgerModeLabel(intl, "mixed")}</option>
                  <option value="actual_only">{ledgerModeLabel(intl, "actual_only")}</option>
                  <option value="planned_only">{ledgerModeLabel(intl, "planned_only")}</option>
                </select>
              </label>

              <label className="checkbox-field checkbox-field--inline">
                <input
                  checked={includeSkipped}
                  type="checkbox"
                  onChange={(event) => setIncludeSkipped(event.target.checked)}
                />
                <span>{intl.formatMessage({ id: "reports.includeSkipped" })}</span>
              </label>
            </div>

            <div className="callout">
              {intl.formatMessage(
                { id: "reports.openingClosing" },
                {
                  opening: formatCurrency(ledgerQuery.data?.opening_balance),
                  closing: formatCurrency(ledgerQuery.data?.closing_balance),
                },
              )}
            </div>

            <div className="list-stack">
              {ledgerQuery.isLoading ? (
                <SkeletonRows count={5} />
              ) : ledgerQuery.data?.rows.length ? (
                <AnimatedList>
                  {ledgerQuery.data.rows.map((row) => (
                    <AnimatedListItem key={row.row_id}>
                      <article className="ledger-row">
                        <div>
                          <div className="ledger-row__title">
                            {row.description ?? intl.formatMessage({ id: "reports.ledgerRow" })}
                          </div>
                          <div className="ledger-row__meta">
                            <span className={`status-badge status-badge--${row.status}`}>{row.status}</span>
                            {" · "}
                            {row.row_type}
                          </div>
                        </div>
                        <div className="ledger-row__amount">
                          <strong>{formatCurrency(row.amount)}</strong>
                          <span>
                            {intl.formatMessage(
                              { id: "reports.balanceAfter" },
                              { value: formatCurrency(row.balance_after) },
                            )}
                          </span>
                        </div>
                      </article>
                    </AnimatedListItem>
                  ))}
                </AnimatedList>
              ) : (
                <div className="empty-state">{intl.formatMessage({ id: "reports.noLedger" })}</div>
              )}
            </div>
          </Card>
        </Tabs.Content>

        <Tabs.Content className="tab-panel" value="pnl">
          <Card>
            <div className="callout">
              {intl.formatMessage(
                { id: "reports.total" },
                { value: formatCurrency(pnlQuery.data?.grand_total) },
              )}
            </div>

            {pnlQuery.isLoading ? (
              <Skeleton variant="chart" />
            ) : pnlChartData.length > 0 ? (
              <div className="content-grid">
                <div className="chart-container chart-container--donut">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pnlChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius="55%"
                        outerRadius="80%"
                        paddingAngle={4}
                        dataKey="value"
                        stroke="none"
                      >
                        {pnlChartData.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
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
                    {pnlChartData.map((entry, index) => (
                      <div key={entry.name} className="chart-legend-item">
                        <span
                          className="chart-legend-dot"
                          style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                        />
                        <span className="chart-legend-label">{entry.name}</span>
                        <span className="chart-legend-value">{formatCurrency(String(entry.value))}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={pnlChartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={60} />
                      <Tooltip
                        formatter={(value) => formatCurrency(String(value))}
                        contentStyle={{
                          background: "var(--surface)",
                          border: "1px solid var(--border)",
                          borderRadius: "var(--radius-md)",
                          fontSize: "0.8125rem",
                        }}
                      />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {pnlChartData.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : null}

            <ReportTotalList
              emptyMessage={intl.formatMessage({ id: "reports.noPnl" })}
              items={
                groupBy === "by_type"
                  ? pnlQuery.data?.totals_by_type.map((item) => ({
                      label: item.type,
                      total: item.total,
                    })) ?? []
                  : pnlQuery.data?.totals_by_category.map((item) => ({
                      label: item.category_name ?? "Uncategorized",
                      total: item.total,
                    })) ?? []
              }
            />
          </Card>
        </Tabs.Content>

        <Tabs.Content className="tab-panel" value="cash">
          <Card>
            <div className="callout">
              {intl.formatMessage(
                { id: "reports.cashTotal" },
                { value: formatCurrency(cashflowQuery.data?.grand_total) },
              )}
            </div>

            {cashflowQuery.isLoading ? (
              <Skeleton variant="chart" />
            ) : cashflowChartData.length > 0 ? (
              <div className="content-grid">
                <div className="chart-container chart-container--donut">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={cashflowChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius="55%"
                        outerRadius="80%"
                        paddingAngle={4}
                        dataKey="value"
                        stroke="none"
                      >
                        {cashflowChartData.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
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
                    {cashflowChartData.map((entry, index) => (
                      <div key={entry.name} className="chart-legend-item">
                        <span
                          className="chart-legend-dot"
                          style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                        />
                        <span className="chart-legend-label">{entry.name}</span>
                        <span className="chart-legend-value">{formatCurrency(String(entry.value))}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={cashflowChartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={60} />
                      <Tooltip
                        formatter={(value) => formatCurrency(String(value))}
                        contentStyle={{
                          background: "var(--surface)",
                          border: "1px solid var(--border)",
                          borderRadius: "var(--radius-md)",
                          fontSize: "0.8125rem",
                        }}
                      />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {cashflowChartData.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : null}

            <ReportTotalList
              emptyMessage={intl.formatMessage({ id: "reports.noCashflow" })}
              items={
                groupBy === "by_type"
                  ? cashflowQuery.data?.totals_by_type.map((item) => ({
                      label: item.type,
                      total: item.total,
                    })) ?? []
                  : cashflowQuery.data?.totals_by_category.map((item) => ({
                      label: item.category_name ?? "Uncategorized",
                      total: item.total,
                    })) ?? []
              }
            />
          </Card>
        </Tabs.Content>
      </Tabs.Root>
    </AnimatedPage>
  );
}

function MetricCard({ label, value }: { label: string; value: string | undefined }) {
  return (
    <Card className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{formatCurrency(value)}</div>
    </Card>
  );
}

function ReportTotalList({
  items,
  emptyMessage,
}: {
  items: Array<{ label: string; total: string }>;
  emptyMessage: string;
}) {
  if (!items.length) {
    return <div className="empty-state">{emptyMessage}</div>;
  }

  return (
    <div className="list-stack">
      {items.map((item) => (
        <article className="ledger-row" key={`${item.label}-${item.total}`}>
          <div className="ledger-row__title">{item.label}</div>
          <div className="ledger-row__amount">
            <strong>{formatCurrency(item.total)}</strong>
          </div>
        </article>
      ))}
    </div>
  );
}

function offsetDate(days: number) {
  const now = new Date();
  now.setDate(now.getDate() + days);
  return now.toISOString().slice(0, 10);
}
