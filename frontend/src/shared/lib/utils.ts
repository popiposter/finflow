import { getCurrentLocale } from "@/shared/lib/i18n";

export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function formatCurrency(value: string | number | null | undefined) {
  const safe = Number(value ?? 0);

  return new Intl.NumberFormat(getCurrentLocale(), {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(safe) ? safe : 0);
}

export function formatShortDate(value: string | null | undefined) {
  if (!value) {
    return getCurrentLocale() === "ru" ? "н/д" : "n/a";
  }

  return new Intl.DateTimeFormat(getCurrentLocale(), {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function formatDateTimeInputValue(value: string | null | undefined) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const normalized = new Date(date.getTime() - offset * 60_000);
  return normalized.toISOString().slice(0, 16);
}

export function toIsoDateTime(value: string) {
  return new Date(value).toISOString();
}

export function todayOffset(days = 0) {
  const now = new Date();
  now.setDate(now.getDate() + days);
  return now.toISOString().slice(0, 10);
}
