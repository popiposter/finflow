import type { TransactionType } from "@/shared/api/types";
import { useAppIntl } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/Button";

type ReconciledFilter = "all" | "yes" | "no";

type ToolbarOption<T extends string> = {
  value: T;
  label: string;
};

type TransactionsTableToolbarProps = {
  globalSearch: string;
  onGlobalSearchChange: (value: string) => void;
  typeFilter: "all" | TransactionType;
  onTypeFilterChange: (value: "all" | TransactionType) => void;
  accountFilter: string;
  onAccountFilterChange: (value: string) => void;
  categoryFilter: string;
  onCategoryFilterChange: (value: string) => void;
  reconciledFilter: ReconciledFilter;
  onReconciledFilterChange: (value: ReconciledFilter) => void;
  dateFrom: string;
  onDateFromChange: (value: string) => void;
  dateTo: string;
  onDateToChange: (value: string) => void;
  transactionTypeOptions: Array<ToolbarOption<TransactionType>>;
  accountOptions: string[];
  categoryOptions: string[];
  onClearFilters: () => void;
};

export function TransactionsTableToolbar({
  globalSearch,
  onGlobalSearchChange,
  typeFilter,
  onTypeFilterChange,
  accountFilter,
  onAccountFilterChange,
  categoryFilter,
  onCategoryFilterChange,
  reconciledFilter,
  onReconciledFilterChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  transactionTypeOptions,
  accountOptions,
  categoryOptions,
  onClearFilters,
}: TransactionsTableToolbarProps) {
  const intl = useAppIntl();

  return (
    <div className="table-toolbar desktop-only">
      <label className="field">
        <span>{intl.formatMessage({ id: "transactions.table.search" })}</span>
        <input
          placeholder={intl.formatMessage({ id: "transactions.table.searchPlaceholder" })}
          type="search"
          value={globalSearch}
          onChange={(event) => onGlobalSearchChange(event.target.value)}
        />
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "common.type" })}</span>
        <select
          value={typeFilter}
          onChange={(event) => onTypeFilterChange(event.target.value as "all" | TransactionType)}
        >
          <option value="all">{intl.formatMessage({ id: "transactions.table.anyType" })}</option>
          {transactionTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "common.account" })}</span>
        <select value={accountFilter} onChange={(event) => onAccountFilterChange(event.target.value)}>
          <option value="all">{intl.formatMessage({ id: "transactions.table.anyAccount" })}</option>
          {accountOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "common.category" })}</span>
        <select value={categoryFilter} onChange={(event) => onCategoryFilterChange(event.target.value)}>
          <option value="all">{intl.formatMessage({ id: "transactions.table.anyCategory" })}</option>
          {categoryOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "transactions.reconciled" })}</span>
        <select
          value={reconciledFilter}
          onChange={(event) => onReconciledFilterChange(event.target.value as ReconciledFilter)}
        >
          <option value="all">{intl.formatMessage({ id: "transactions.table.reconciledAny" })}</option>
          <option value="yes">{intl.formatMessage({ id: "transactions.table.reconciledYes" })}</option>
          <option value="no">{intl.formatMessage({ id: "transactions.table.reconciledNo" })}</option>
        </select>
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "common.from" })}</span>
        <input type="date" value={dateFrom} onChange={(event) => onDateFromChange(event.target.value)} />
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "common.to" })}</span>
        <input type="date" value={dateTo} onChange={(event) => onDateToChange(event.target.value)} />
      </label>

      <Button type="button" variant="secondary" onClick={onClearFilters}>
        {intl.formatMessage({ id: "transactions.table.clearFilters" })}
      </Button>
    </div>
  );
}
