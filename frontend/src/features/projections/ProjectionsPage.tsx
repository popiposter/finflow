import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarCheck2, CircleOff, Pencil } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { listCategories } from "@/shared/api/categories";
import {
  confirmProjectedTransaction,
  listProjectedTransactions,
  skipProjectedTransaction,
  updateProjectedTransaction,
} from "@/shared/api/projections";
import type { ProjectedTransaction, ProjectedTransactionStatus } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { projectionStatusLabel, transactionTypeLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { AnimatedList, AnimatedListItem } from "@/shared/ui/AnimatedList";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";
import { SkeletonRows } from "@/shared/ui/Skeleton";

const statuses = ["pending", "confirmed", "skipped"] as const satisfies ProjectedTransactionStatus[];

type ProjectionFormValues = {
  projected_amount: string;
  projected_date: string;
  projected_description?: string;
  projected_category_id?: string;
};

export function ProjectionsPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const projectionSchema = useMemo(
    () =>
      z.object({
        projected_amount: z.string().trim().min(1, validation.required),
        projected_date: z.string().min(1, validation.required),
        projected_description: z.string().optional(),
        projected_category_id: z.string().optional(),
      }),
    [validation],
  );
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
      toast.success(intl.formatMessage({ id: "toast.projectionUpdated" }));
      setEditingProjection(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (projectionId: string) => confirmProjectedTransaction(projectionId),
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.projectionConfirmed" }));
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const skipMutation = useMutation({
    mutationFn: skipProjectedTransaction,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.projectionSkipped" }));
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
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
    <AnimatedPage className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "projections.eyebrow" })}</p>
          <h2 className="section-title">{intl.formatMessage({ id: "projections.title" })}</h2>
        </div>
      </div>

      <Card>
        <div className="field-grid field-grid--three">
          <label className="field">
            <span>{intl.formatMessage({ id: "common.status" })}</span>
            <select
              aria-label="Projection status filter"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as ProjectedTransactionStatus | "")}
            >
              <option value="">{intl.formatMessage({ id: "projections.anyStatus" })}</option>
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {projectionStatusLabel(intl, status)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.from" })}</span>
            <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.to" })}</span>
            <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
          </label>
        </div>
      </Card>

      <Card>
        <div className="list-stack">
          {projectionsQuery.isLoading ? (
            <SkeletonRows count={5} />
          ) : projections.length ? (
            <AnimatedList>
            {projections.map((projection) => {
              const isPending = projection.status === "pending";
              return (
                <AnimatedListItem key={projection.id}>
                <article className="projection-row">
                  <div>
                    <div className="transaction-row__title">
                      {projection.projected_description ??
                        projection.origin_description ??
                        intl.formatMessage({ id: "projections.label" })}
                    </div>
                    <div className="transaction-row__meta">
                      {transactionTypeLabel(intl, projection.type)} ·{" "}
                      {formatShortDate(projection.projected_date)}
                    </div>
                  </div>

                  <div className="projection-row__right">
                    <div className="projection-row__summary">
                      <strong>{formatCurrency(projection.projected_amount)}</strong>
                      <span className={`status-badge status-badge--${projection.status}`}>
                        {projectionStatusLabel(intl, projection.status)}
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
                        {intl.formatMessage({ id: "common.edit" })}
                      </button>
                      <button
                        className="inline-action"
                        disabled={!isOnline || !isPending || confirmMutation.isPending}
                        type="button"
                        onClick={() => void confirmMutation.mutateAsync(projection.id)}
                      >
                        <CalendarCheck2 size={14} />
                        {intl.formatMessage({ id: "projections.confirm" })}
                      </button>
                      <button
                        className="inline-action inline-action--danger"
                        disabled={!isOnline || !isPending || skipMutation.isPending}
                        type="button"
                        onClick={() => void skipMutation.mutateAsync(projection.id)}
                      >
                        <CircleOff size={14} />
                        {intl.formatMessage({ id: "projections.skip" })}
                      </button>
                    </div>
                  </div>
                </article>
                </AnimatedListItem>
              );
            })}
            </AnimatedList>
          ) : (
            <div className="empty-state">{intl.formatMessage({ id: "projections.empty" })}</div>
          )}
        </div>
      </Card>

      <DialogSheet
        description={intl.formatMessage({ id: "projections.dialogDescription" })}
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title={intl.formatMessage({ id: "projections.editTitle" })}
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "projections.projectedAmount" })}</span>
              <input inputMode="decimal" {...projectionForm.register("projected_amount")} />
              {getFieldErrorMessage(projectionForm.formState.errors.projected_amount) ? (
                <small className="field-error">
                  {getFieldErrorMessage(projectionForm.formState.errors.projected_amount)}
                </small>
              ) : null}
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "projections.projectedDate" })}</span>
              <input type="date" {...projectionForm.register("projected_date")} />
              {getFieldErrorMessage(projectionForm.formState.errors.projected_date) ? (
                <small className="field-error">
                  {getFieldErrorMessage(projectionForm.formState.errors.projected_date)}
                </small>
              ) : null}
            </label>
          </div>

          <label className="field">
            <span>{intl.formatMessage({ id: "projections.projectedDescription" })}</span>
            <input {...projectionForm.register("projected_description")} />
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "projections.projectedCategory" })}</span>
            <select {...projectionForm.register("projected_category_id")}>
              <option value="">{intl.formatMessage({ id: "common.none" })}</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          {updateMutation.error ? (
            <ApiErrorCallout error={updateMutation.error} />
          ) : null}

          <Button disabled={!isOnline || updateMutation.isPending} type="submit">
            {updateMutation.isPending
              ? intl.formatMessage({ id: "common.saving" })
              : intl.formatMessage({ id: "projections.save" })}
          </Button>
        </form>
      </DialogSheet>
    </AnimatedPage>
  );
}
