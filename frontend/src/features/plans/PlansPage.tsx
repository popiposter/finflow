import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarSync, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

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
import { useOnlineStatus } from "@/shared/lib/offline";
import { formatCurrency, formatShortDate, todayOffset } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";

const recurrences = ["daily", "weekly", "monthly"] as const satisfies Recurrence[];

const planSchema = z.object({
  account_id: z.string().uuid(),
  category_id: z.string().optional(),
  amount: z.string().min(1),
  description: z.string().optional(),
  recurrence: z.enum(recurrences),
  start_date: z.string().min(1),
  next_due_at: z.string().optional(),
  end_date: z.string().optional(),
  is_active: z.boolean().default(true),
});

type PlanFormValues = z.infer<typeof planSchema>;

export function PlansPage() {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
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
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ planId, payload }: { planId: string; payload: PlanFormValues }) =>
      updatePlan(planId, normalizePlanPayload(payload)),
    onSuccess: async () => {
      setEditingPlan(null);
      setIsDialogOpen(false);
      await refreshWorkspace();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deletePlan,
    onSuccess: refreshWorkspace,
  });

  const generateMutation = useMutation({
    mutationFn: () => generateDueProjections(todayOffset(0)),
    onSuccess: async (results) => {
      const generatedCount = results.reduce(
        (sum, item) => sum + item.generated_projections.length,
        0,
      );
      setGenerationSummary(`${generatedCount} projections generated.`);
      await refreshWorkspace();
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
    <div className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">Template-first recurring layer</p>
          <h2 className="section-title">Build recurring templates before they turn into facts.</h2>
        </div>

        <div className="action-group">
          <Button
            disabled={!isOnline || generateMutation.isPending}
            type="button"
            variant="secondary"
            onClick={() => void generateMutation.mutateAsync()}
          >
            <CalendarSync size={16} />
            {generateMutation.isPending ? "Generating..." : "Generate due"}
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
            New plan
          </Button>
        </div>
      </div>

      {generationSummary ? <div className="callout">{generationSummary}</div> : null}

      <Card>
        <div className="list-stack">
          {plansQuery.data?.length ? (
            plansQuery.data.map((plan) => (
              <article className="transaction-row" key={plan.id}>
                <div>
                  <div className="transaction-row__title">
                    {plan.description ?? "Untitled planned payment"}
                  </div>
                  <div className="transaction-row__meta">
                    {plan.recurrence} · next due {formatShortDate(plan.next_due_at)}
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
                      Edit
                    </button>
                    <button
                      className="inline-action inline-action--danger"
                      disabled={!isOnline || deleteMutation.isPending}
                      type="button"
                      onClick={() => {
                        if (window.confirm("Delete this planned payment?")) {
                          void deleteMutation.mutateAsync(plan.id);
                        }
                      }}
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">No planned payments yet.</div>
          )}
        </div>
      </Card>

      <DialogSheet
        description="Templates generate pending projected transactions on schedule."
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title={editingPlan ? "Edit plan" : "New planned payment"}
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <div className="field-grid field-grid--two">
            <label className="field">
              <span>Account</span>
              <select {...planForm.register("account_id")}>
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
              <select {...planForm.register("category_id")}>
                <option value="">None</option>
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
              <span>Amount</span>
              <input inputMode="decimal" placeholder="0.00" {...planForm.register("amount")} />
            </label>

            <label className="field">
              <span>Recurrence</span>
              <select {...planForm.register("recurrence")}>
                {recurrences.map((recurrence) => (
                  <option key={recurrence} value={recurrence}>
                    {recurrence}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span>Description</span>
            <input placeholder="Rent, payroll, subscriptions..." {...planForm.register("description")} />
          </label>

          <div className="field-grid field-grid--three">
            <label className="field">
              <span>Start</span>
              <input type="date" {...planForm.register("start_date")} />
            </label>

            <label className="field">
              <span>Next due</span>
              <input type="date" {...planForm.register("next_due_at")} />
            </label>

            <label className="field">
              <span>End</span>
              <input type="date" {...planForm.register("end_date")} />
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...planForm.register("is_active")} />
            <span>Plan is active</span>
          </label>

          {createMutation.error || updateMutation.error ? (
            <div className="callout callout--danger">
              {createMutation.error?.message ?? updateMutation.error?.message}
            </div>
          ) : null}

          <Button
            disabled={!isOnline || createMutation.isPending || updateMutation.isPending}
            type="submit"
          >
            {editingPlan
              ? updateMutation.isPending
                ? "Saving..."
                : "Save plan"
              : createMutation.isPending
                ? "Creating..."
                : "Create plan"}
          </Button>
        </form>
      </DialogSheet>
    </div>
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
