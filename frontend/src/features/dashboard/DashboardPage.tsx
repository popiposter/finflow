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
          <h2 className="hero-title">Keep facts, projections, and drift in one rhythm.</h2>
          <p className="hero-subtitle">
            Review forecast pressure, confirm projections, and capture fresh transactions
            without leaving the app shell.
          </p>
        </div>

        <div className="hero-actions">
          <Link className="button button--primary button-link" to="/transactions/new">
            Add transaction
          </Link>
          <Button
            disabled={!isOnline || generateMutation.isPending}
            type="button"
            variant="secondary"
            onClick={() => void generateMutation.mutateAsync()}
          >
            {generateMutation.isPending ? "Generating..." : "Generate due projections"}
          </Button>
        </div>
      </section>

      <div className="metric-grid">
        <Card className="metric-card">
          <div className="metric-icon">
            <Wallet size={20} />
          </div>
          <div className="metric-label">Projected balance</div>
          <div className="metric-value">
            {formatCurrency(forecastQuery.data?.projected_balance)}
          </div>
          <div className="metric-meta">
            Current {formatCurrency(forecastQuery.data?.current_balance)}
          </div>
        </Card>

        <Card className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={20} />
          </div>
          <div className="metric-label">Pending projections</div>
          <div className="metric-value">{pendingCount}</div>
          <div className="metric-meta">
            Through {formatShortDate(todayOffset(30))}
          </div>
        </Card>

        <Card className="metric-card">
          <div className="metric-icon">
            <Sparkles size={20} />
          </div>
          <div className="metric-label">Projected income</div>
          <div className="metric-value">
            {formatCurrency(forecastQuery.data?.projected_income)}
          </div>
          <div className="metric-meta">
            Expenses {formatCurrency(forecastQuery.data?.projected_expense)}
          </div>
        </Card>
      </div>

      <div className="content-grid">
        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">Quick capture</h3>
              <p className="muted-copy">
                Use parse-and-create for quick mobile entry from natural language.
              </p>
            </div>
          </div>

          {!isOnline ? (
            <div className="callout">Quick capture needs a live connection.</div>
          ) : null}

          <form className="form-stack" onSubmit={onCaptureSubmit}>
            <label className="field">
              <span>Text</span>
              <textarea
                placeholder="Coffee 4.50, salary 2400, groceries 82"
                rows={3}
                {...captureForm.register("text")}
              />
            </label>

            <div className="field-grid field-grid--two">
              <label className="field">
                <span>Account</span>
                <select {...captureForm.register("account_id")}>
                  <option value="">Choose account</option>
                  {accountsQuery.data?.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Category</span>
                <select {...captureForm.register("category_id")}>
                  <option value="">Auto or none</option>
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
              {captureMutation.isPending ? "Creating..." : "Parse and create"}
            </Button>
          </form>
        </Card>

        <Card>
          <div className="section-header">
            <div>
              <h3 className="section-title">Recent cashflow</h3>
              <p className="muted-copy">Latest rows from the unified ledger.</p>
            </div>
            <Link className="inline-link" to="/reports">
              Open reports <ArrowRight size={16} />
            </Link>
          </div>

          <div className="list-stack">
            {recentRows.length ? (
              recentRows.map((row) => (
                <article className="ledger-row" key={row.row_id}>
                  <div>
                    <div className="ledger-row__title">{row.description ?? "Untitled row"}</div>
                    <div className="ledger-row__meta">
                      {row.row_type} · {formatShortDate(row.date)}
                    </div>
                  </div>
                  <div className="ledger-row__amount">
                    <strong>{formatCurrency(row.amount)}</strong>
                    <span>{row.status}</span>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state">No cashflow rows yet.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
