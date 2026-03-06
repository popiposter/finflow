# Backend specification

## Domain scope
FinFlow backend supports:
- user authentication via login/password
- browser sessions with rotating JWT cookies
- long-lived API tokens for iOS Shortcut
- accounts, categories, transactions, planned payments
- BDR/accrual and BDDS/cashflow reports

## First milestone
Implement project skeleton, health endpoint, settings, database wiring, and test setup.

## Conventions
- API prefix: `/api/v1`
- Primary response format: JSON
- Timezone-aware datetimes in UTC at API/storage boundary unless a field is explicitly date-only
- Decimal for money values
