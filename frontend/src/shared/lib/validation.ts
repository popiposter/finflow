import type { FieldError } from "react-hook-form";
import type { IntlShape } from "react-intl";

export function getValidationMessages(intl: IntlShape) {
  return {
    required: intl.formatMessage({ id: "validation.required" }),
    invalidEmail: intl.formatMessage({ id: "validation.invalidEmail" }),
    passwordMin: intl.formatMessage({ id: "validation.passwordMin" }, { count: 8 }),
    invalidSelection: intl.formatMessage({ id: "validation.invalidSelection" }),
    shortName: intl.formatMessage({ id: "validation.shortName" }, { count: 2 }),
    currencyCode: intl.formatMessage({ id: "validation.currencyCode" }, { count: 3 }),
    invalidNumber: intl.formatMessage({ id: "validation.invalidNumber" }),
    shortCapture: intl.formatMessage({ id: "validation.shortCapture" }, { count: 3 }),
  };
}

export function getFieldErrorMessage(error: FieldError | undefined) {
  return typeof error?.message === "string" ? error.message : null;
}

