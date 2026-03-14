import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { createCategory, deleteCategory, listCategories, updateCategory } from "@/shared/api/categories";
import type { Category, CategoryType } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { categoryTypeLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { AnimatedPage } from "@/shared/ui/AnimatedPage";
import { AnimatedList, AnimatedListItem } from "@/shared/ui/AnimatedList";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";
import { SkeletonRows } from "@/shared/ui/Skeleton";

const categoryTypes = ["income", "expense"] as const satisfies CategoryType[];

type CategoryFormValues = {
  name: string;
  type: CategoryType;
  description?: string;
  parent_id?: string;
  is_active: boolean;
  display_order: number;
};

export function CategoriesSettingsPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const validation = getValidationMessages(intl);
  const schema = useMemo(
    () =>
      z.object({
        name: z.string().trim().min(2, validation.shortName),
        type: z.enum(categoryTypes),
        description: z.string().optional(),
        parent_id: z.string().optional(),
        is_active: z.boolean().default(true),
        display_order: z.coerce.number({
          invalid_type_error: validation.invalidNumber,
        }).default(0),
      }),
    [validation],
  );
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const availableParents = useMemo(
    () =>
      (categoriesQuery.data ?? []).filter((category) => category.id !== editingCategory?.id),
    [categoriesQuery.data, editingCategory?.id],
  );

  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      type: "expense",
      description: "",
      parent_id: "",
      is_active: true,
      display_order: 0,
    },
  });

  useEffect(() => {
    if (!editingCategory) {
      form.reset({
        name: "",
        type: "expense",
        description: "",
        parent_id: "",
        is_active: true,
        display_order: 0,
      });
      return;
    }

    form.reset({
      name: editingCategory.name,
      type: editingCategory.type,
      description: editingCategory.description ?? "",
      parent_id: editingCategory.parent_id ?? "",
      is_active: editingCategory.is_active,
      display_order: editingCategory.display_order,
    });
  }, [editingCategory, form]);

  const refreshCategories = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["categories"] }),
      queryClient.invalidateQueries({ queryKey: ["transactions"] }),
      queryClient.invalidateQueries({ queryKey: ["plans"] }),
      queryClient.invalidateQueries({ queryKey: ["projections"] }),
      queryClient.invalidateQueries({ queryKey: ["reports"] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: createCategory,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.categoryCreated" }));
      setIsDialogOpen(false);
      await refreshCategories();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      categoryId,
      payload,
    }: {
      categoryId: string;
      payload: CategoryFormValues;
    }) => updateCategory(categoryId, normalizeCategoryPayload(payload)),
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.categoryUpdated" }));
      setEditingCategory(null);
      setIsDialogOpen(false);
      await refreshCategories();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: async () => {
      toast.success(intl.formatMessage({ id: "toast.categoryDeleted" }));
      await refreshCategories();
    },
    onError: () => {
      toast.error(intl.formatMessage({ id: "toast.genericError" }));
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    if (editingCategory) {
      await updateMutation.mutateAsync({
        categoryId: editingCategory.id,
        payload: values,
      });
      return;
    }

    await createMutation.mutateAsync(normalizeCategoryPayload(values));
  });

  return (
    <AnimatedPage className="page-stack">
      <div className="split-header">
        <div>
          <p className="eyebrow">{intl.formatMessage({ id: "settings.categoriesTitle" })}</p>
          <h2 className="section-title">{intl.formatMessage({ id: "categories.title" })}</h2>
        </div>
        <Button
          disabled={!isOnline}
          type="button"
          onClick={() => {
            setEditingCategory(null);
            setIsDialogOpen(true);
          }}
        >
          <Plus size={16} />
          {intl.formatMessage({ id: "categories.new" })}
        </Button>
      </div>

      <Card>
        <div className="list-stack">
          {categoriesQuery.isLoading ? (
            <SkeletonRows count={4} />
          ) : categoriesQuery.data?.length ? (
            <AnimatedList>
            {categoriesQuery.data.map((category) => (
              <AnimatedListItem key={category.id}>
              <article className="transaction-row">
                <div>
                  <div className="transaction-row__title">
                    <span className={`category-dot category-dot--${category.type}`} />
                    {category.name}
                  </div>
                  <div className="transaction-row__meta">
                    <span className={`status-badge status-badge--${category.type === "income" ? "income" : "expense"}`}>
                      {categoryTypeLabel(intl, category.type)}
                    </span>
                    {" · "}
                    {intl.formatMessage(
                      { id: "categories.orderMeta" },
                      { count: category.display_order },
                    )}
                  </div>
                </div>

                <div className="transaction-row__actions">
                  <strong>
                    {category.parent_id
                      ? intl.formatMessage({ id: "categories.child" })
                      : intl.formatMessage({ id: "categories.topLevel" })}
                  </strong>
                  <div className="row-button-group">
                    <button
                      className="inline-action"
                      disabled={!isOnline}
                      type="button"
                      onClick={() => {
                        setEditingCategory(category);
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
                          if (window.confirm(intl.formatMessage({ id: "categories.deleteConfirm" }))) {
                            void deleteMutation.mutateAsync(category.id);
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
              <div className="empty-state">{intl.formatMessage({ id: "categories.empty" })}</div>
            )}
          </div>
      </Card>

      <DialogSheet
        description={intl.formatMessage({ id: "categories.dialogDescription" })}
        onOpenChange={setIsDialogOpen}
        open={isDialogOpen}
        title={
          editingCategory
            ? intl.formatMessage({ id: "categories.edit" })
            : intl.formatMessage({ id: "categories.newDialog" })
        }
      >
        <form className="form-stack" onSubmit={onSubmit}>
          <label className="field">
            <span>{intl.formatMessage({ id: "common.name" })}</span>
            <input {...form.register("name")} />
            {getFieldErrorMessage(form.formState.errors.name) ? (
              <small className="field-error">{getFieldErrorMessage(form.formState.errors.name)}</small>
            ) : null}
          </label>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.type" })}</span>
              <select {...form.register("type")}>
                {categoryTypes.map((type) => (
                  <option key={type} value={type}>
                    {categoryTypeLabel(intl, type)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "common.parent" })}</span>
              <select {...form.register("parent_id")}>
                <option value="">{intl.formatMessage({ id: "common.none" })}</option>
                {availableParents.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="field-grid field-grid--two">
            <label className="field">
              <span>{intl.formatMessage({ id: "common.description" })}</span>
              <input {...form.register("description")} />
            </label>

            <label className="field">
              <span>{intl.formatMessage({ id: "categories.displayOrder" })}</span>
              <input inputMode="numeric" type="number" {...form.register("display_order")} />
              {getFieldErrorMessage(form.formState.errors.display_order) ? (
                <small className="field-error">
                  {getFieldErrorMessage(form.formState.errors.display_order)}
                </small>
              ) : null}
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...form.register("is_active")} />
            <span>{intl.formatMessage({ id: "categories.active" })}</span>
          </label>

          {createMutation.error || updateMutation.error ? (
            <ApiErrorCallout error={createMutation.error ?? updateMutation.error} />
          ) : null}

          <Button disabled={!isOnline || createMutation.isPending || updateMutation.isPending} type="submit">
            {editingCategory
              ? updateMutation.isPending
                ? intl.formatMessage({ id: "common.saving" })
                : intl.formatMessage({ id: "categories.save" })
              : createMutation.isPending
                ? intl.formatMessage({ id: "common.creating" })
                : intl.formatMessage({ id: "categories.create" })}
          </Button>
        </form>
      </DialogSheet>
    </AnimatedPage>
  );
}

function normalizeCategoryPayload(values: CategoryFormValues) {
  return {
    name: values.name,
    type: values.type,
    description: values.description || null,
    parent_id: values.parent_id || null,
    is_active: values.is_active,
    display_order: values.display_order,
  };
}
