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
Status: ACCEPTED
Affected phase(s): FASE 10 — Inference Engine

Context:
Section 37 requires a singleton intersection between two positive perception
neighborhoods to confirm a hazard. Sections 7 and 74 configure multiple pits,
Wumpus, and bats. With multiplicity greater than one, two positive signals can
be satisfied by different hazards outside their singleton intersection, so the
required confirmation is not logically valid in every permitted world.

Decision:
Retain each positive perception as an independent existential candidate
constraint. Confirm only when one individual positive constraint has a single
unresolved candidate. A singleton intersection between separate constraints
remains possible knowledge and does not alone confirm a hazard.

Reason:
The production logical agent must not assert knowledge that does not follow
from its observations. The user explicitly authorized the recommended
multiplicity-aware interpretation on 2026-09-24.

Consequences:
Pairwise intersections cannot create false confirmations when distinct hazards
can satisfy the observations. Elimination and fixed-point propagation continue
to confirm hazards when an individual constraint is reduced to one candidate.

Evidence:
Sections 7, 34–38, 74, and 119 FASE 10; user authorization on 2026-09-24;
`tests/unit/test_inference.py`.

## DEC-004 — Priority 5 fires whenever exploration stalls, without a route-blocking proof

Date: 2026-09-24
Status: ACCEPTED
Affected phase(s): FASE 13 — Wumpus hunting

Context:
Section 44 priority 5 says to shoot a confirmed Wumpus "caso ele bloqueie
rota útil" (if it blocks a useful route), but the plan gives no algorithm
for proving that a specific confirmed Wumpus is the reason no safe route
remains, as opposed to an unrelated unconfirmed hazard or an unreachable
region being the real obstruction.

Decision:
`Strategy._hunt` (priority 5) fires whenever priorities 3-4 find no
reachable, unvisited safe cell (`unexplored` is empty), without separately
proving that the specific confirmed Wumpus it targets is what is blocking
progress.

Reason:
Priority 5 is only ever reached after priorities 3-4 have already searched
exhaustively for a safe route and found none; by that point, some obstacle
is preventing further safe progress, and a confirmed live Wumpus is one of
the few knowable obstacles the agent can act on without FASE 14's risk
engine. Building a precise "would killing this Wumpus specifically reopen a
route" proof would require frontier/connectivity reasoning that belongs to
FASE 14 and is not yet implemented; the alternative (never shooting without
that proof) would leave a confirmed, capturable Wumpus blocking exploration
indefinitely with no path to resolution.

Consequences:
The agent may occasionally spend an arrow (-10, section 21) on a confirmed
Wumpus that is not actually the sole obstruction (e.g., the true blocker is
an unconfirmed possible pit elsewhere). This trades a bounded, known cost
for guaranteed forward progress and is consistent with the project's
soundness-first posture elsewhere (DEC-003): the agent never asserts false
hazard knowledge, it just does not yet reason about which confirmed hazard
is "the" blocker. FASE 14 — Risk engine may tighten this once
frontier/connectivity reasoning exists.

Evidence:
Section 44 priority 5; `src/wumpus/agent/strategy.py::Strategy._hunt`;
`tests/unit/test_strategy.py` hunting tests; independent specification
review on 2026-09-24 (flagged as MEDIUM, accepted as a defensible
simplification pending FASE 14).

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
