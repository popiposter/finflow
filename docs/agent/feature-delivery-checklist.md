# Feature delivery checklist

For every issue Claude should follow this sequence.

1. Restate the goal and scope.
2. Identify files likely to change.
3. Check existing models/schemas/services before creating new ones.
4. Implement the smallest vertical slice that satisfies the issue.
5. Add or update tests in the same change.
6. Update docs if a reusable pattern was introduced.
7. Summarize changed files, validation commands, and remaining follow-ups.

## Definition of done
- Acceptance criteria satisfied.
- Tests for changed behavior exist.
- No unrelated refactors mixed in.
- Docs updated where necessary.
