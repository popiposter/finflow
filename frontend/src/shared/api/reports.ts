import { apiFetch, toQueryString } from "@/shared/api/client";
import type {
  CashflowForecast,
  CashflowLedgerMode,
  CashflowLedgerReport,
  CashflowReport,
  PnlReport,
  ReportGroupBy,
} from "@/shared/api/types";

type AggregateParams = {
  start_date?: string;
  end_date?: string;
  group_by?: ReportGroupBy;
};

type LedgerParams = {
  from: string;
  to: string;
  mode?: CashflowLedgerMode;
  include_skipped?: boolean;
};

export function getPnlReport(params: AggregateParams) {
  return apiFetch<PnlReport>(`/reports/pnl${toQueryString(params)}`);
}

export function getCashflowReport(params: AggregateParams) {
  return apiFetch<CashflowReport>(`/reports/cashflow${toQueryString(params)}`);
}

export function getLedgerReport(params: LedgerParams) {
  return apiFetch<CashflowLedgerReport>(`/cashflow/report${toQueryString(params)}`);
}

export function getForecast(target_date?: string) {
  return apiFetch<CashflowForecast>(
    `/cashflow/forecast${toQueryString({ target_date })}`,
  );
}
