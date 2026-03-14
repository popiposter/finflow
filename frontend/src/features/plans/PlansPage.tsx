import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarSync, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { toast } from "sonner";

import { listAccounts } from "@/shared/api/accounts";
import { listCategories } from "@/shared/api/categories";
import {
  createPlan,
  deletePlan,
  generateDueProjections,
  listPlans,
  updatePlan,
} from "@/shared/api/plans";
import type { PlannedPayment, Recurrence } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { AnimatedList, AnimatedListItem } from "@/shared/ui/AnimatedList";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { recurrenceLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";
import { SkeletonRows } from "@/shared/ui/Skeleton";

const recurrences = ["daily", "weekly", "monthly"] as const satisfies Recurrence[];

type PlanFormValues = {
  account_id: string;
  category_id?: string;
  amount: string;
  description?: string;
  recurrence: Recurrence;
  start_date: string;
  next_due_at?: string;
  end_date?: string;
  is_active: boolean;
};

export function PlansPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const planSchema = useMemo(
    () =>
      z.object({
        account_id: z.string().uuid(validation.invalidSelection),
        category_id: z.string().optional(),
        amount: z.string().trim().min(1, validation.required),
        description: z.string().optional(),
        recurrence: z.enum(recurrences),
        start_date: z.string().min(1, validation.required),
        next_due_at: z.string().optional(),
        end_date: z.string().optional(),
        is_active: z.boolean().default(true),
      }),
    [validation],
  );
  const [editingPlan, setEditingPlan] = useState<PlannedPayment | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [generationSummary, setGenerationSummary] = useState<string | null>(null);

  const accountsQuery = useQuery({ queryKey: ["accounts"], queryFn: listAccounts });
  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const plansQuery = useQuery({ queryKey: ["plans"], queryFn: listPlans });

  const planForm = useForm<PlanFormValues>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      account_id: "",
      category_id: "",
      amount: "",
      description: "",
      recurrence: "monthly",
      start_date: todayOffset(0),
      next_due_at: todayOffset(0),
      end_date: "",
      is_active: true,
    },
  });

  useEffect(() => {
    const defaultAccount = accountsQuery.data?.[0]?.id ?? "";

    if (editingPlan) {
      planForm.reset({
        account_id: editingPlan.account_id,
        category_id: editingPlan.category_id ?? "",
        amount: editingPlan.amount,
        description: editingPlan.description ?? "",
        recurrence: editingPlan.recurrence,
        start_date: editingPlan.start_date,
        next_due_at: editingPlan.next_due_at,
        end_date: editingPlan.end_date ?? "",
        is_active: editingPlan.is_active,
      });
      return;
    }

    planForm.reset({
      account_id: defaultAccount,
      category_id: "",
      amount: "",
      description: "",
      recurrence: "monthly",
      start_date: todayOffset(0),
      next_due_at: todayOffset(0),
      end_date: "",
      is_active: true,
    });
  }, [accountsQuery.data, editingPlan, planForm]);

  const refreshWorkspace = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["plans"] }),
      queryClient.invalidateQueries({ queryKey: ["projections"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["cashflow"] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: createPlan,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.planCreated" }));
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ planId, payload }: { planId: string; payload: PlanFormValues }) =>
      updatePlan(planId, normalizePlanPayload(payload)),
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.planUpdated" }));
      setEditingPlan(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deletePlan,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.planDeleted" }));
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => generateDueProjections(todayOffset(0)),
    onSuccess: async (results) => {
      const generatedCount = results.reduce(
        (sum, item) => sum + item.generated_projections.length,
        0,
      );
      toast.success(intl.formatMessage({ id: "toast.projectionsGenerated" }));
      setGenerationSummary(
        intl.formatMessage({ id: "plans.generatedSummary" }, { count: generatedCount }),
      );
      await refreshWorkspace();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const onSubmit = planForm.handleSubmit(async (values) => {
    if (editingPlan) {
      await updateMutation.mutateAsync({
        planId: editingPlan.id,
        payload: values,
      });
      return;
    }

    await createMutation.mutateAsync(normalizePlanPayload(values));
  });

  return (
    <AnimatedPage className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "plans.eyebrow" })}</p>
          <h2 className="section-title">{intl.formatMessage({ id: "plans.title" })}</h2>
        </div>

        <div className="action-group">
          <Button
            disabled={!isOnline || generateMutation.isPending}
            type="button"
            variant="secondary"
            onClick={() => void generateMutation.mutateAsync()}
          >
            <CalendarSync size={16} />
            {generateMutation.isPending
              ? intl.formatMessage({ id: "dashboard.generating" })
              : intl.formatMessage({ id: "plans.generateDue" })}
          </Button>
          <Button
            disabled={!isOnline || !accountsQuery.data?.length}
            type="button"
            onClick={() => {
              setEditingPlan(null);
              setIsDialogOpen(true);
            }}
          >
            <Plus size={16} />
            {intl.formatMessage({ id: "plans.new" })}
          </Button>
        </div>
      </div>

      {generationSummary ? <div className="callout">{generationSummary}</div> : null}

      <Card>
        <div className="list-stack">
          {plansQuery.isLoading ? (
            <SkeletonRows count={4} />
          ) : plansQuery.data?.length ? (
            <AnimatedList>
              {plansQuery.data.map((plan) => (
                <AnimatedListItem key={plan.id}>
                  <article className="transaction-row">
                    <div>
                      <div className="transaction-row__title">
                        {plan.description ?? intl.formatMessage({ id: "plans.untitled" })}
                        {!plan.is_active && (
                          <span className="status-badge status-badge--skipped" style={{ marginLeft: "0.5rem" }}>
                            {intl.formatMessage({ id: "plans.inactive" })}
                          </span>
                        )}
                      </div>
                      <div className="transaction-row__meta">
                        <span className="recurrence-badge">
                          {recurrenceLabel(intl, plan.recurrence)}
                        </span>
                        {" · "}
                        {intl.formatMessage(
                          { id: "plans.nextDue" },
                          { date: formatShortDate(plan.next_due_at) },
                        )}
                      </div>
                    </div>

                    <div className="transaction-row__actions">
                      <strong>{formatCurrency(plan.amount)}</strong>
                      <div className="row-button-group">
                        <button
                          className="inline-action"
                          disabled={!isOnline}
                          type="button"
                          onClick={() => {
                            setEditingPlan(plan);
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
                            if (window.confirm(intl.formatMessage({ id: "plans.deleteConfirm" }))) {
                              void deleteMutation.mutateAsync(plan.id);
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
            <div className="empty-state">{intl.formatMessage({ id: "plans.empty" })}</div>
          )}
        </div>
      </Card>

      <DialogSheet
        description={intl.formatMessage({ id: "plans.dialogDescription" })}
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title={
          editingPlan
            ? intl.formatMessage({ id: "plans.edit" })
            : intl.formatMessage({ id: "plans.newDialog" })
        }
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.account" })}</span>
                <select {...planForm.register("account_id")}>
                <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
                {accountsQuery.data?.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
                </select>
                {getFieldErrorMessage(planForm.formState.errors.account_id) ? (
                  <small className="field-error">
                    {getFieldErrorMessage(planForm.formState.errors.account_id)}
                  </small>
                ) : null}
              </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.category" })}</span>
              <select {...planForm.register("category_id")}>
                <option value="">{intl.formatMessage({ id: "common.none" })}</option>
                {categoriesQuery.data?.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.amount" })}</span>
              <input inputMode="decimal" placeholder="0.00" {...planForm.register("amount")} />
              {getFieldErrorMessage(planForm.formState.errors.amount) ? (
                <small className="field-error">
                  {getFieldErrorMessage(planForm.formState.errors.amount)}
                </small>
              ) : null}
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.recurrence" })}</span>
              <select {...planForm.register("recurrence")}>
                {recurrences.map((recurrence) => (
                  <option key={recurrence} value={recurrence}>
                    {recurrenceLabel(intl, recurrence)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.description" })}</span>
            <input
              placeholder={intl.formatMessage({ id: "plans.descriptionPlaceholder" })}
              {...planForm.register("description")}
            />
          </label>

          <div className="field-grid field-grid--three">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.start" })}</span>
              <input type="date" {...planForm.register("start_date")} />
              {getFieldErrorMessage(planForm.formState.errors.start_date) ? (
                <small className="field-error">
                  {getFieldErrorMessage(planForm.formState.errors.start_date)}
                </small>
              ) : null}
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "plans.nextDueLabel" })}</span>
              <input type="date" {...planForm.register("next_due_at")} />
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.end" })}</span>
              <input type="date" {...planForm.register("end_date")} />
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...planForm.register("is_active")} />
            <span>{intl.formatMessage({ id: "plans.active" })}</span>
          </label>

          {createMutation.error || updateMutation.error ? (
            <ApiErrorCallout error={createMutation.error ?? updateMutation.error} />
          ) : null}

          <Button
            disabled={!isOnline || createMutation.isPending || updateMutation.isPending}
            type="submit"
          >
            {editingPlan
              ? updateMutation.isPending
                ? intl.formatMessage({ id: "common.saving" })
                : intl.formatMessage({ id: "plans.save" })
              : createMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "plans.create" })}
          </Button>
        </form>
      </DialogSheet>
    </AnimatedPage>
  );
}

function normalizePlanPayload(values: PlanFormValues) {
  return {
    account_id: values.account_id,
    category_id: values.category_id || null,
    amount: values.amount,
    description: values.description || null,
    recurrence: values.recurrence,
    start_date: values.start_date,
    next_due_at: values.next_due_at || values.start_date,
    end_date: values.end_date || null,
    is_active: values.is_active,
  };
}
