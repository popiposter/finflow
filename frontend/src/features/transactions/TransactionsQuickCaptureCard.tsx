import type { UseFormReturn } from "react-hook-form";
import { WandSparkles } from "lucide-react";

import type { Account, Category } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { getFieldErrorMessage } from "@/shared/lib/validation";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";

export type CaptureValues = {
  text: string;
  account_id: string;
  category_id?: string;
};

type TransactionsQuickCaptureCardProps = {
  isOnline: boolean;
  accountOptions: Account[];
  categoryOptions: Category[];
  captureForm: UseFormReturn<CaptureValues>;
  onSubmit: (event?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  error: unknown;
};

export function TransactionsQuickCaptureCard({
  isOnline,
  accountOptions,
  categoryOptions,
  captureForm,
  onSubmit,
  isSubmitting,
  error,
}: TransactionsQuickCaptureCardProps) {
  const intl = useAppIntl();

  return (
    <Card>
      <div className="section-header">
        <div>
          <h3 className="section-title">{intl.formatMessage({ id: "dashboard.quickCaptureTitle" })}</h3>
          <p className="muted-copy">{intl.formatMessage({ id: "transactions.quickCaptureCopy" })}</p>
        </div>
        <span className="pill">
          <WandSparkles size={14} />
          {intl.formatMessage({ id: "transactions.parsePill" })}
        </span>
      </div>

      <form className="form-stack" onSubmit={onSubmit}>
        <label className="field">
          <span>{intl.formatMessage({ id: "dashboard.text" })}</span>
          <textarea
            rows={3}
            placeholder={intl.formatMessage({ id: "transactions.placeholder" })}
            {...captureForm.register("text")}
          />
          {getFieldErrorMessage(captureForm.formState.errors.text) ? (
            <small className="field-error">
              {getFieldErrorMessage(captureForm.formState.errors.text)}
            </small>
          ) : null}
        </label>

        <div className="field-grid field-grid--two">
          <label className="field">
            <span>{intl.formatMessage({ id: "common.account" })}</span>
            <select {...captureForm.register("account_id")}>
              <option value="">{intl.formatMessage({ id: "common.chooseAccount" })}</option>
              {accountOptions.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
            {getFieldErrorMessage(captureForm.formState.errors.account_id) ? (
              <small className="field-error">
                {getFieldErrorMessage(captureForm.formState.errors.account_id)}
              </small>
            ) : null}
          </label>

          <label className="field">
            <span>{intl.formatMessage({ id: "common.category" })}</span>
            <select {...captureForm.register("category_id")}>
              <option value="">{intl.formatMessage({ id: "common.autoOrNone" })}</option>
              {categoryOptions.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error ? <ApiErrorCallout error={error} /> : null}

        <Button
          disabled={!isOnline || isSubmitting || !accountOptions.length}
          type="submit"
        >
          {isSubmitting
            ? intl.formatMessage({ id: "common.creating" })
            : intl.formatMessage({ id: "transactions.parse" })}
        </Button>
      </form>
    </Card>
  );
}
