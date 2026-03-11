# Backend issue roadmap

This roadmap captures the milestone sequence that shaped the current backend and
the remaining refinement direction after the core finance lifecycle landed.

1. Project bootstrap
2. Auth foundation
3. Core finance domain model
4. Free-form transaction ingestion
5. Planned payments template layer
6. Projected transactions and projection-first recurring lifecycle
7. Scheduler-backed recurring projection generation
8. Reports foundation plus unified cashflow ledger/forecast
9. Transaction/account/category CRUD refinement and editing
10. Planned-payment cleanup to remove legacy execute semantics
11. Parse-and-create refinement and ownership-aware persistence polish
12. Product refinement and operational polish

Current status:
- Milestones 1 through 11 are implemented in `main`.
- The next work is refinement rather than a missing foundation milestone.

Current refinement themes:
- richer reporting/product feedback loops
- optional default-account selection for parse-and-create
- targeted UX polish rather than new backend foundation

Prefer one issue per milestone unless a milestone is too large and needs a
follow-up split.
