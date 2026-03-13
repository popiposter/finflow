# Transaction ingestion knowledge pack

## Goal
Implement and refine end-to-end transaction ingestion from free-form text to a
stored transaction.

## Scope
- request/response schemas for parse-and-create endpoint
- request/response schemas for workbook bulk import
- transaction creation service
- workbook import service
- heuristic parser fallback for free-form text
- endpoint for iOS Shortcut ingestion
- endpoint for `.xlsx` batch import into actual transactions
- tests for happy path, invalid input, auth, and real persistence behavior

## Primary endpoint
- `POST /api/v1/transactions/parse-and-create`
- `POST /api/v1/transactions/import`

## Input contract
Current request body:
- `text`
- `account_id` required for now
- `category_id` optional

Bulk import contract:
- multipart form-data
- `account_id` required
- `file` required, `.xlsx` only
- first sheet interpreted as `date`, `description`, `amount`
- negative amount -> expense, positive amount -> income
- response summarizes imported IDs plus skipped row errors

## Parsing rules
- Extract amount from text using regex/heuristics.
- Prefer the amount explicitly marked as money when multiple numbers appear.
- If no money marker is present, prefer the trailing amount over an earlier count.
- Preserve a cleaned human-readable description rather than storing raw text unchanged.
- Infer category only when confidence is reasonable; otherwise allow uncategorized transaction.
- Infer transaction type only for simple high-confidence cases such as income/refund keywords.
- If a parsed category name matches a user category exactly, auto-attach it.
- If parsing is uncertain, prefer partial structured output over failure.

## Architecture rules
- Route remains thin.
- Parsing logic lives in a service/helper module.
- Keep parser implementation replaceable by future LLM-based parsing.
- Validate real account/category ownership before persisting.
- Use authenticated DB lookups for account and optional category before creating the transaction.
- For workbook import, validate the selected account once before row ingestion and report row-level parse issues without failing the whole file.
- API errors should use the normalized envelope with stable codes for frontend localization.

## Do not do
- Do not call external LLM APIs in this milestone unless the issue explicitly asks for it.
- Do not over-engineer NLP.
- Do not reject valid transactions just because category inference failed.
- Do not silently write into another user's account or category.
- Do not pretend default-account selection exists until the product issue for it is implemented.

## Tests
- Parse amount from simple Russian phrase.
- Create transaction from text with authenticated persistence.
- Missing amount returns validation/business error.
- Category inference is optional.
- Multiple-number phrases pick the expected amount.
- Auth and ownership validation are covered.
- Parser can infer simple `income` and `refund` cases from high-confidence keywords.
- If category text matches an existing user category, the persisted transaction should attach it.
- Workbook import covers success path, foreign-account rejection, and invalid-file rejection.
