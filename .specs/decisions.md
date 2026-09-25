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

## DEC-002 — Start position and direction live in game configuration

Date: 2026-09-24
Status: ACCEPTED
Affected phase(s): FASE 7 — Engine

Context:
Section 5 fixes the start at `[1,1]` facing North, and sections 57 and 58
forbid any agent dependency on the environment. The temporary agent of FASE 7
needs the exit position to decide `CLIMB`.

Decision:
`START_POSITION` and `START_DIRECTION` are defined once in
`src/wumpus/game/config.py`. `World` imports them and `wumpus.environment`
keeps re-exporting them for existing callers.

Reason:
It preserves a single source of truth for a game rule and lets the agent layer
know the exit without importing the environment package.

Consequences:
Agent modules depend on `wumpus.game.config` only. `wumpus.game.__init__` must
not be imported by the environment, so `World` and `MapGenerator` import
`wumpus.game.config` directly to avoid an import cycle.

Evidence:
Sections 5, 57, and 58; `src/wumpus/game/config.py`;
`tests/unit/test_simple_agent.py::test_agent_module_never_references_the_environment`.

## DEC-003 — Intersection inference with multiple hazards

Date: 2026-09-24
Status: PROPOSED
Affected phase(s): FASE 10 — Inference Engine

Context:
Section 37 requires a singleton intersection between two positive perception
neighborhoods to confirm a hazard. Sections 7 and 74 configure multiple pits,
Wumpus, and bats. With multiplicity greater than one, two positive signals can
be satisfied by different hazards outside their singleton intersection, so the
required confirmation is not logically valid in every permitted world.

Decision:
User decision required. The recommended multiplicity-aware interpretation is
to retain each positive perception as an existential candidate constraint and
confirm only when that individual constraint has one unresolved candidate.
The alternative is to implement section 37 literally, accepting possible false
confirmations in worlds with multiple hazards of the same type.

Reason:
The production logical agent must not assert knowledge that does not follow
from its observations. Neither instruction precedence nor existing accepted
decisions resolve the conflict between the literal intersection rule and the
configured hazard multiplicity.

Consequences:
FASE 10 remains `BLOCKED`. Absence, presence, elimination, safety, bounded
fixed-point processing, functional events, and fail-closed contradiction
handling can be implemented and tested, but intersection behavior and the
phase gate require an explicit requirement decision.

Evidence:
Sections 7, 34–38, 74, and 119 FASE 10; independent FASE 10 logic and
specification reviews; `tests/unit/test_inference.py`.

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
