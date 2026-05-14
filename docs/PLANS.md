# ExecPlans

Use an ExecPlan for work that is complex, risky, multi-step, or likely to span multiple agent turns.

## Location

- Active plans: `docs/exec-plans/active/`
- Completed plans: `docs/exec-plans/completed/`

Move a plan to completed only when implementation and validation are done.

## Required Sections

Every active ExecPlan must include these headings:

- `Purpose / Big Picture`
- `Progress`
- `Surprises & Discoveries`
- `Decision Log`
- `Outcomes & Retrospective`
- `Context and Orientation`
- `Plan of Work`
- `Concrete Steps`
- `Validation and Acceptance`
- `Idempotence and Recovery`

## Expectations

- Keep plans self-contained enough that a future agent can resume without chat history.
- Update `Progress` as work completes.
- Record important choices in `Decision Log`.
- Record failed commands and known blockers in `Surprises & Discoveries` or `Outcomes & Retrospective`.
- Link related docs and files rather than pasting huge source excerpts.

## Validation

`scripts/agent/check-docs` verifies required ExecPlan headings for active plans.
