import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarCheck2, CircleOff, Pencil } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { listCategories } from "@/shared/api/categories";
import {
  confirmProjectedTransaction,
  listProjectedTransactions,
  skipProjectedTransaction,
  updateProjectedTransaction,
} from "@/shared/api/projections";
import type { ProjectedTransaction, ProjectedTransactionStatus } from "@/shared/api/types";
import { useOnlineStatus } from "@/shared/lib/offline";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";

const statuses = ["pending", "confirmed", "skipped"] as const satisfies ProjectedTransactionStatus[];

const projectionSchema = z.object({
  projected_amount: z.string().min(1),
  projected_date: z.string().min(1),
  projected_description: z.string().optional(),
  projected_category_id: z.string().optional(),
});

type ProjectionFormValues = z.infer<typeof projectionSchema>;

export function ProjectionsPage() {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const [editingProjection, setEditingProjection] = useState<ProjectedTransaction | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<ProjectedTransactionStatus | "">("pending");
  const [fromDate, setFromDate] = useState(todayOffset(-14));
  const [toDate, setToDate] = useState(todayOffset(45));

  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const projectionsQuery = useQuery({
    queryKey: ["projections", statusFilter, fromDate, toDate],
    queryFn: () =>
      listProjectedTransactions({
        status: statusFilter,
        from: fromDate,
        to: toDate,
      }),
  });

  const projectionForm = useForm<ProjectionFormValues>({
    resolver: zodResolver(projectionSchema),
    defaultValues: {
      projected_amount: "",
      projected_date: todayOffset(0),
      projected_description: "",
      projected_category_id: "",
    },
  });

  useEffect(() => {
    if (!editingProjection) {
      projectionForm.reset({
        projected_amount: "",
        projected_date: todayOffset(0),
        projected_description: "",
        projected_category_id: "",
      });
      return;
    }

    projectionForm.reset({
      projected_amount: editingProjection.projected_amount,
      projected_date: editingProjection.projected_date,
      projected_description: editingProjection.projected_description ?? "",
      projected_category_id: editingProjection.projected_category_id ?? "",
    });
  }, [editingProjection, projectionForm]);

  const refreshWorkspace = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["projections"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      queryClient.invalidateQueries({ queryKey: ["reports"] }),
    ]);
  };

  const updateMutation = useMutation({
    mutationFn: ({
      projectionId,
      payload,
    }: {
      projectionId: string;
      payload: ProjectionFormValues;
    }) =>
      updateProjectedTransaction(projectionId, {
        projected_amount: payload.projected_amount,
        projected_date: payload.projected_date,
        projected_description: payload.projected_description || null,
        projected_category_id: payload.projected_category_id || null,
      }),
    onSuccess: async () => {
      setEditingProjection(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (projectionId: string) => confirmProjectedTransaction(projectionId),
    onSuccess: refreshWorkspace,
  });

  const skipMutation = useMutation({
    mutationFn: skipProjectedTransaction,
    onSuccess: refreshWorkspace,
  });

  const onSubmit = projectionForm.handleSubmit(async (values) => {
    if (!editingProjection) {
      return;
    }

    await updateMutation.mutateAsync({
      projectionId: editingProjection.id,
      payload: values,
    });
  });

  const projections = useMemo(() => projectionsQuery.data ?? [], [projectionsQuery.data]);

  return (
    <div className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">Forecast layer</p>
          <h2 className="section-title">Edit expectations first, then confirm or skip them.</h2>
        </div>
      </div>

      <Card>
        <div className="field-grid field-grid--three">
          <label className="field">
            <span>Status</span>
            <select
              aria-label="Projection status filter"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as ProjectedTransactionStatus | "")}
            >
              <option value="">Any status</option>
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>From</span>
            <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
          </label>

          <label className="field">
            <span>To</span>
            <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
          </label>
        </div>
      </Card>

      <Card>
        <div className="list-stack">
          {projections.length ? (
            projections.map((projection) => {
              const isPending = projection.status === "pending";
              return (
                <article className="projection-row" key={projection.id}>
                  <div>
                    <div className="transaction-row__title">
                      {projection.projected_description ?? projection.origin_description ?? "Projection"}
                    </div>
                    <div className="transaction-row__meta">
                      {projection.type} · {formatShortDate(projection.projected_date)}
                    </div>
                  </div>

                  <div className="projection-row__right">
                    <div className="projection-row__summary">
                      <strong>{formatCurrency(projection.projected_amount)}</strong>
                      <span className={`status-badge status-badge--${projection.status}`}>
                        {projection.status}
                      </span>
                    </div>

                    <div className="row-button-group">
                      <button
                        className="inline-action"
                        disabled={!isOnline || !isPending}
                        type="button"
                        onClick={() => {
                          setEditingProjection(projection);
                          setIsDialogOpen(true);
                        }}
                      >
                        <Pencil size={14} />
                        Edit
                      </button>
                      <button
                        className="inline-action"
                        disabled={!isOnline || !isPending || confirmMutation.isPending}
                        type="button"
                        onClick={() => void confirmMutation.mutateAsync(projection.id)}
                      >
                        <CalendarCheck2 size={14} />
                        Confirm
                      </button>
                      <button
                        className="inline-action inline-action--danger"
                        disabled={!isOnline || !isPending || skipMutation.isPending}
                        type="button"
                        onClick={() => void skipMutation.mutateAsync(projection.id)}
                      >
                        <CircleOff size={14} />
                        Skip
                      </button>
                    </div>
                  </div>
                </article>
              );
            })
          ) : (
            <div className="empty-state">No projected transactions match this filter set.</div>
          )}
        </div>
      </Card>

      <DialogSheet
        description="Pending projections can be adjusted before they become actual transactions."
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title="Edit projected transaction"
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <div className="field-grid field-grid--two">
            <label className="field">
              <span>Projected amount</span>
              <input inputMode="decimal" {...projectionForm.register("projected_amount")} />
            </label>

            <label className="field">
              <span>Projected date</span>
              <input type="date" {...projectionForm.register("projected_date")} />
            </label>
          </div>

          <label className="field">
            <span>Projected description</span>
            <input {...projectionForm.register("projected_description")} />
          </label>

          <label className="field">
            <span>Projected category</span>
            <select {...projectionForm.register("projected_category_id")}>
              <option value="">None</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          {updateMutation.error ? (
            <div className="callout callout--danger">{updateMutation.error.message}</div>
          ) : null}

          <Button disabled={!isOnline || updateMutation.isPending} type="submit">
            {updateMutation.isPending ? "Saving..." : "Save projection"}
          </Button>
        </form>
      </DialogSheet>
    </div>
  );
}
