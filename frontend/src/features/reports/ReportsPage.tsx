import * as Tabs from "@radix-ui/react-tabs";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  getCashflowReport,
  getForecast,
  getLedgerReport,
  getPnlReport,
} from "@/shared/api/reports";
import type { CashflowLedgerMode, ReportGroupBy } from "@/shared/api/types";
import { formatCurrency } from "@/shared/lib/utils";
import { Card } from "@/shared/ui/Card";

export function ReportsPage() {
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

  return (
    <div className="page-stack">
      <Card>
        <div className="field-grid field-grid--three">
          <label className="field">
            <span>From</span>
            <input type="date" value={aggregateStart} onChange={(event) => setAggregateStart(event.target.value)} />
          </label>

          <label className="field">
            <span>To</span>
            <input type="date" value={aggregateEnd} onChange={(event) => setAggregateEnd(event.target.value)} />
          </label>

          <label className="field">
            <span>Group</span>
            <select value={groupBy} onChange={(event) => setGroupBy(event.target.value as ReportGroupBy)}>
              <option value="by_category">By category</option>
              <option value="by_type">By type</option>
            </select>
          </label>
        </div>
      </Card>

      <Tabs.Root className="tabs-root" defaultValue="forecast">
        <Tabs.List className="tabs-list" aria-label="Report views">
          <Tabs.Trigger className="tab-trigger" value="forecast">
            Forecast
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="ledger">
            Unified ledger
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="pnl">
            P&amp;L
          </Tabs.Trigger>
          <Tabs.Trigger className="tab-trigger" value="cash">
            Cashflow
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content className="tab-panel" value="forecast">
          <Card>
            <div className="field-grid field-grid--two">
              <label className="field">
                <span>Target date</span>
                <input
                  type="date"
                  value={forecastTarget}
                  onChange={(event) => setForecastTarget(event.target.value)}
                />
              </label>
            </div>

            <div className="metric-grid">
              <MetricCard label="Current balance" value={forecastQuery.data?.current_balance} />
              <MetricCard label="Projected income" value={forecastQuery.data?.projected_income} />
              <MetricCard label="Projected expense" value={forecastQuery.data?.projected_expense} />
              <MetricCard label="Projected balance" value={forecastQuery.data?.projected_balance} />
            </div>
          </Card>
        </Tabs.Content>

        <Tabs.Content className="tab-panel" value="ledger">
          <Card>
            <div className="field-grid field-grid--two">
              <label className="field">
                <span>Mode</span>
                <select
                  value={ledgerMode}
                  onChange={(event) => setLedgerMode(event.target.value as CashflowLedgerMode)}
                >
                  <option value="mixed">Mixed</option>
                  <option value="actual_only">Actual only</option>
                  <option value="planned_only">Planned only</option>
                </select>
              </label>

              <label className="checkbox-field checkbox-field--inline">
                <input
                  checked={includeSkipped}
                  type="checkbox"
                  onChange={(event) => setIncludeSkipped(event.target.checked)}
                />
                <span>Include skipped projections</span>
              </label>
            </div>

            <div className="callout">
              Opening {formatCurrency(ledgerQuery.data?.opening_balance)} · Closing{" "}
              {formatCurrency(ledgerQuery.data?.closing_balance)}
            </div>

            <div className="list-stack">
              {ledgerQuery.data?.rows.length ? (
                ledgerQuery.data.rows.map((row) => (
                  <article className="ledger-row" key={row.row_id}>
                    <div>
                      <div className="ledger-row__title">{row.description ?? "Ledger row"}</div>
                      <div className="ledger-row__meta">
                        {row.row_type} · {row.status}
                      </div>
                    </div>
                    <div className="ledger-row__amount">
                      <strong>{formatCurrency(row.amount)}</strong>
                      <span>after {formatCurrency(row.balance_after)}</span>
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty-state">No ledger rows in this period.</div>
              )}
            </div>
          </Card>
        </Tabs.Content>

        <Tabs.Content className="tab-panel" value="pnl">
          <Card>
            <div className="callout">Total {formatCurrency(pnlQuery.data?.grand_total)}</div>
            <ReportTotalList
              emptyMessage="No P&amp;L totals yet."
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
              Cash total {formatCurrency(cashflowQuery.data?.grand_total)}
            </div>
            <ReportTotalList
              emptyMessage="No cashflow totals yet."
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
    </div>
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
