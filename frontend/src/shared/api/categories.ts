import { apiFetch } from "@/shared/api/client";
import type { Category, CategoryInput, UUID } from "@/shared/api/types";

export function listCategories() {
  return apiFetch<Category[]>("/categories");
}

export function createCategory(payload: CategoryInput) {
  return apiFetch<Category>("/categories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCategory(categoryId: UUID, payload: CategoryInput) {
  return apiFetch<Category>(`/categories/${categoryId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteCategory(categoryId: UUID) {
  return apiFetch<void>(`/categories/${categoryId}`, {
    method: "DELETE",
  });
}
