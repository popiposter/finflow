import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { createCategory, deleteCategory, listCategories, updateCategory } from "@/shared/api/categories";
import type { Category, CategoryType } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { categoryTypeLabel } from "@/shared/lib/labels";
import { useOnlineStatus } from "@/shared/lib/offline";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DialogSheet } from "@/shared/ui/DialogSheet";

const categoryTypes = ["income", "expense"] as const satisfies CategoryType[];

const schema = z.object({
  name: z.string().min(2),
  type: z.enum(categoryTypes),
  description: z.string().optional(),
  parent_id: z.string().optional(),
  is_active: z.boolean().default(true),
  display_order: z.coerce.number().default(0),
});

type CategoryFormValues = z.infer<typeof schema>;

export function CategoriesSettingsPage() {
  const intl = useAppIntl();
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
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
      setIsDialogOpen(false);
      await refreshCategories();
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
      setEditingCategory(null);
      setIsDialogOpen(false);
      await refreshCategories();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: refreshCategories,
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
    <div className="page-stack">
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
          {categoriesQuery.data?.length ? (
            categoriesQuery.data.map((category) => (
              <article className="transaction-row" key={category.id}>
                <div>
                  <div className="transaction-row__title">{category.name}</div>
                  <div className="transaction-row__meta">
                    {categoryTypeLabel(intl, category.type)} ·{" "}
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
            ))
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
            </label>
          </div>

          <label className="checkbox-field">
            <input type="checkbox" {...form.register("is_active")} />
            <span>{intl.formatMessage({ id: "categories.active" })}</span>
          </label>

          {createMutation.error || updateMutation.error ? (
            <div className="callout callout--danger">
              {createMutation.error?.message ?? updateMutation.error?.message}
            </div>
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
    </div>
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
