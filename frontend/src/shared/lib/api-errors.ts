import type { IntlShape } from "react-intl";
import type {
  FieldPath,
  FieldValues,
  UseFormSetError,
} from "react-hook-form";

import { ApiError, isApiError } from "@/shared/api/client";
import type { TransactionImportError } from "@/shared/api/types";

export function formatApiErrorMessage(intl: IntlShape, error: unknown) {
  if (!isApiError(error)) {
    return intl.formatMessage({ id: "errors.request_failed" });
  }

  const translated = tryFormatMessage(intl, `errors.${error.code}`);
  return translated ?? error.message ?? intl.formatMessage({ id: "errors.request_failed" });
}

export function formatImportRowError(intl: IntlShape, error: TransactionImportError) {
  const translated = tryFormatMessage(intl, `errors.${error.code}`);
  return translated ?? error.message;
}

export function applyApiFieldErrors<TFieldValues extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<TFieldValues>,
  intl: IntlShape,
) {
  if (!isApiError(error)) {
    return;
  }

  Object.entries(error.fields).forEach(([field, message]) => {
    setError(field as FieldPath<TFieldValues>, {
      type: "server",
      message: localizeFieldMessage(intl, message),
    });
  });
}

function localizeFieldMessage(intl: IntlShape, message: string) {
  const normalized = message.trim().toLowerCase();
  const mapping: Record<string, string> = {
    "field required": "errors.field_required",
    "invalid uuid": "errors.invalid_uuid",
    "value is not a valid email address: an email address must have an @-sign.": "errors.invalid_email",
    "string should have at least 8 characters": "errors.password_too_short",
    "value error, invalid email or password": "errors.authentication_failed",
  };

  const id = mapping[normalized];
  return id ? intl.formatMessage({ id }) : message;
}

function tryFormatMessage(intl: IntlShape, id: string) {
  return Object.prototype.hasOwnProperty.call(intl.messages, id)
    ? intl.formatMessage({ id })
    : null;
}

export { ApiError, isApiError };

