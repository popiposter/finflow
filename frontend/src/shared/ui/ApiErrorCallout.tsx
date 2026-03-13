import { useAppIntl } from "@/shared/lib/i18n";
import { formatApiErrorMessage } from "@/shared/lib/api-errors";

type ApiErrorCalloutProps = {
  error: unknown;
};

export function ApiErrorCallout({ error }: ApiErrorCalloutProps) {
  const intl = useAppIntl();

  return (
    <div className="callout callout--danger">
      {formatApiErrorMessage(intl, error)}
    </div>
  );
}

