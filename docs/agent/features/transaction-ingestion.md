# Transaction ingestion knowledge pack

## Goal
Implement the first end-to-end transaction ingestion flow from free-form text to stored transaction.

## Scope
- request/response schemas for parse-and-create endpoint
- transaction creation service
- heuristic parser fallback for free-form text
- endpoint for iOS Shortcut ingestion
- tests for happy path and invalid input

## Primary endpoint
- `POST /api/v1/transactions/parse-and-create`

## Input contract
Expected request body should support at least:
- `text`
- `source`
- `created_at` optional
- `default_account_id` optional
- `default_currency` optional

## Parsing rules for MVP
- Extract amount from text using regex/heuristics.
- Normalize currency, defaulting to project default when omitted.
- Preserve original text in description.
- Extract merchant when obvious, but never block creation if merchant is missing.
- Infer category only when confidence is reasonable; otherwise allow uncategorized transaction.
- If parsing is uncertain, prefer partial structured output over failure.

## Architecture rules
- Route remains thin.
- Parsing logic lives in a service/helper module.
- Keep parser implementation replaceable by future LLM-based parsing.
- Log parse decisions carefully, but never log secrets.

## Do not do
- Do not call external LLM APIs in this milestone unless the issue explicitly asks for it.
- Do not over-engineer NLP.
- Do not reject valid transactions just because merchant/category inference failed.

## Tests
- Parse amount from simple Russian phrase.
- Create expense transaction from text.
- Missing amount returns validation/business error.
- Merchant/category inference is optional.

## Suggested implementation order
1. Add request/response schemas.
2. Add parser helper/service.
3. Add transaction creation service.
4. Add endpoint.
5. Add tests.
6. Update docs if parser conventions stabilize.
