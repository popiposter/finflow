# Refactoring playbook

Use this playbook for cleanup tasks.

## Rules
- Preserve behavior first.
- Add or update characterization tests before large refactors.
- Move code in small steps.
- Keep public contracts stable unless the issue explicitly allows changes.
- Separate refactor commits from feature commits when practical.

## Safe sequence
1. Identify target smell or problem.
2. Add tests around current behavior.
3. Extract helper/service/repository.
4. Re-run tests.
5. Remove dead code.
6. Update docs if architecture changed.
