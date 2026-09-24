# Implementation Decisions

Record only implementation decisions that are not already resolved by
`.specs/plan.md`. This is not a work diary and must not redefine requirements.

## Decision index

## DEC-001 — Death penalty is cumulative with movement cost

Date: 2026-09-24
Status: ACCEPTED
Affected phase(s): FASE 4 — Ambiente

Context:
Section 11 says every non-shooting action costs `-1`, while section 89
summarizes entering a lethal hazard as `score -= 1000`.

Decision:
Entering a pit or live Wumpus through `MOVE_FORWARD` applies both the `-1`
movement cost and the `-1000` death penalty, for a total delta of `-1001`.

Reason:
This preserves the unconditional action-cost rule and treats `-1000` as the
separate penalty named in section 12, consistently with the explicit gold
example that combines action cost and event reward.

Consequences:
Death tests assert `-1001` for the complete action result while independently
proving that the centralized death penalty remains exactly `-1000`.

Evidence:
Sections 11, 12, 89, and `tests/unit/test_world.py`.

## Entry format

Use the next sequential identifier and keep each entry concise.

```text
## DEC-NNN — Short title

Date: YYYY-MM-DD
Status: PROPOSED | ACCEPTED | SUPERSEDED | REJECTED
Affected phase(s): Phase number/title

Context:
The unresolved question and the relevant plan references.

Decision:
The selected implementation choice.

Reason:
Why this choice preserves the plan and project constraints.

Consequences:
Expected trade-offs, follow-up work, or test implications.

Evidence:
Files, tests, or user instruction supporting the decision.
```

## Rules

- Do not record trivial coding choices.
- Do not duplicate requirements from `.specs/plan.md`.
- Do not use a decision to override the plan.
- If a genuine requirement conflict cannot be resolved, mark the work
  `BLOCKED` in `implementation-status.md` and ask the user.
- Never change an accepted entry silently; add a superseding decision.
