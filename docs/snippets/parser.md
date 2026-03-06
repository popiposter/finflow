# Parser snippet pack

## MVP transaction parsing heuristics
- First extract amount.
- Then normalize currency.
- Preserve full raw text as description.
- Infer merchant when obvious from known patterns.
- Infer category only when confidence is reasonable.
- If minimal required fields exist, create the transaction even with partial inference.

## Error strategy
- Missing amount should produce a clear validation or business error.
- Unknown merchant/category should not block creation.

## Future extension rule
- Keep the parser wrapped behind a service interface so LLM-based parsing can replace the heuristic implementation later.
