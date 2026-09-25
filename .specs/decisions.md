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

## DEC-005 — Risk threshold stays a single constant; the priority cascade falls through on a failed route

Date: 2026-09-25
Status: ACCEPTED
Affected phase(s): FASE 14 — Risk engine

Context:
Section 44 priorities 6-7 give `Strategy` a least-risk fallback and a
forced-return trigger, scored per section 43. Sections 47-48, under the
separate "POLÍTICA DE SAÍDA" heading (sections 45-48), say the agent should
accept more risk before finding any gold and weigh score preservation more
heavily after. Independent specification and logic review on 2026-09-25
raised two related questions: (1) whether `risk.RISK_THRESHOLD` must be
gold-conditioned to satisfy sections 47-48, and (2) whether `Strategy.decide`
correctly reaches priorities 5-7 in every case they should apply, including
while holding gold.

Decision:
`risk.RISK_THRESHOLD` remains a single, non-gold-conditioned constant
(`HAZARD_RISK_WEIGHTS[WUMPUS]`); sections 47-48's differing risk tolerance
before/after gold is left to FASE 15 to implement as part of its exit-policy
work. Separately, `Strategy.decide`'s priority 2 (return-to-start-and-climb)
and priority 3/4 (route to the nearest unexplored cell) branches were fixed
to only return early when their own `_pursue` call actually produces an
action; when the chosen route has no safe path (e.g. an unclassified gap
disconnects the safe region, or the way home is blocked), `decide` now falls
through to priorities 5-7 instead of returning `None` outright -- including
while the agent holds gold, since section 45's fourth exit condition ("não
existem novas células alcançáveis com risco aceitável") and section 48 both
describe exactly that risk/reward tradeoff.

Reason:
Sections 47-48 sit under the "política de saída" heading (sections 45-48),
distinct from section 44's risk-engine priorities, and the FASE ledger
itself separates "FASE 14 — Risk engine" (menor risco) from "FASE 15 —
Política de saída" (retorno racional); gold-conditioning the threshold now
would be unreachable, untested code given `Strategy`'s own priority-2
precedent (already `VERIFIED` in FASE 12), which is exactly the code smell
`AGENTS.md`'s scope-control rules warn against. The fallthrough fix, in
contrast, is not a new priority-6/7 feature but a correction to already
existing FASE 12/13 control flow: returning `_pursue`'s result unconditionally
whenever some priority-2/3/4 target was merely *attempted* silently discarded
every lower priority the moment a chosen route turned out unreachable, which
independent logic review confirmed as a concrete, reachable defect (not
gold-specific) with a deterministic repro. Making every priority branch
consistently fall through only on a real `None` result closes that gap and,
as a direct consequence, also resolves the specification review's flagged
gold-plus-blocked-route-home gap without inventing new gold-conditioned
risk logic.

Consequences:
A gold-holding agent whose route home is blocked may still shoot a confirmed
Wumpus (priority 5) or accept a `RISK_THRESHOLD`-bounded risk (priority 6)
to clear the way, using the same threshold it would use without gold; it
does not yet weigh score preservation more heavily after finding gold, which
remains a known limitation until FASE 15. `test_strategy_declines_a_risk_above_the_threshold_and_returns_to_start`
and the existing priority-2/3/4 tests continue to pass unchanged, since none
of them previously depended on the unconditional-return behavior.

Evidence:
Sections 43-45, 47-48 FASE 14/15; `src/wumpus/agent/strategy.py::Strategy.decide`,
`Strategy._explore_at_risk`; `src/wumpus/agent/risk.py::RISK_THRESHOLD`;
independent specification and logic review on 2026-09-25 (specification
review: `PARTIALLY_COMPLIANT`, missing this record and flagging the gold
fallthrough gap; logic review: one CONFIRMED HIGH-severity control-flow bug
with a deterministic repro, fixed by the same change).

## DEC-006 — Exit utility uses score-derived costs and gold-conditioned tolerance

Date: 2026-09-25
Status: ACCEPTED
Affected phase(s): FASE 15 — Política de saída

Context:
Sections 45-48 require rational abandonment, permit a simple utility
heuristic, and require more risk tolerance before collecting gold than after,
but do not prescribe numeric thresholds or a probability model.

Decision:
Evaluate only the least-risk reachable candidate from FASE 14. Its incremental
utility is the canonical gold reward multiplied by the configured fraction of
gold still uncollected, minus the exact planned-action cost, an estimated
hazard cost obtained by scaling the canonical death penalty by
`candidate_risk / NO_GOLD_RISK_THRESHOLD`, and the canonical arrow cost when a
shot is required. Before gold, accept at most the existing single-Wumpus risk
threshold; after any gold, accept at most the bat-only weight. Once all
configured gold is collected, return immediately regardless of safe frontier.
If exploration is rejected, return to `[1,1]` and climb there, even with zero
gold; if no safe return route is known, rotate deterministically in place.

Reason:
The model is deterministic, auditable, uses only agent-owned knowledge, and
maps every term in section 46 to an existing centralized game value. The two
thresholds make sections 47-48 operational without claiming unsupported
probabilities, while climbing with zero gold is permitted by section 26 and
satisfies section 45's unconditional case where no acceptable cell remains.

Consequences:
When the already-prioritized safe return route is disconnected, one collected
gold still permits a positive-utility bat-only bridge, while two collected
gold make the same risk unattractive; a pit-only or Wumpus-only candidate is
always rejected after gold. Without gold, the agent remains willing to take a
pit-only hypothesis when utility is positive. The policy does not inspect the
real map or predict actual undiscovered gold locations.

Evidence:
Sections 26 and 45-48; `src/wumpus/agent/exit_policy.py`;
`tests/unit/test_exit_policy.py`; `tests/unit/test_strategy.py`.

## DEC-007 — The reasoning panel shows the previous turn's decision, not a live preview

Date: 2026-09-25
Status: ACCEPTED
Affected phase(s): FASE 16 — UI

Context:
Section 60's engine loop order is `observe -> render -> decide -> execute`,
already implemented and `VERIFIED` by the unchanged FASE 7 `GameEngine.step`
(`src/wumpus/game/engine.py`) and pinned by its own
`tests/unit/test_engine.py` event-order test. Section 67's example panel
("Próxima ação: MOVER PARA FRENTE") could be read as previewing the action
about to be taken for the state currently on screen.

Decision:
`Strategy.decide` records a `DecisionReason` (section 68) at the moment it
chooses an action, and `ConsoleRenderer.render` displays whatever
`DecisionReason` is available when called. Given the fixed engine order, that
value is always the *previous* turn's decision alongside the *new* observation
it produced -- never a same-turn preview. This is not changed by choosing a
different render call site.

Reason:
Reordering the loop to render after `decide()` would require modifying the
already-`VERIFIED` FASE 7 `GameEngine`/`TurnRenderer` contract for a UI-only
concern, which `AGENTS.md`'s scope-control rules discourage without a strict
dependency. The one-turn lag is an inherent consequence of the plan's own
documented loop order, not a shortcut invented in this phase, and the panel
remains informative (it explains why the agent is now where it is).

Consequences:
The reasoning panel is empty on turn one (`Strategy.last_reason is None`
before any `decide` call) and always describes the action that produced the
currently rendered observation, not the one about to be taken. FASE 18's CLI
wiring must not present the panel as a live preview of the next action.

Evidence:
Section 60 pseudocode; section 67-68; `src/wumpus/game/engine.py::GameEngine.step`;
`src/wumpus/agent/strategy.py::Strategy.decide`;
`src/wumpus/ui/console.py::render_reasoning`; independent specification
review on 2026-09-25.

## DEC-008 — The exit moves to the far corner and the match objective is selectable

Date: 2026-09-25
Status: ACCEPTED
Affected phase(s): post-plan maintenance `GAME-GOAL-EXIT-CORNER-003`
(supersedes plan consequences for FASE 15 and DEC-006)

Context:
After the plan was fully implemented, the user explicitly authorized a
gameplay rule change. The plan's historical rule made `[1,1]` both the spawn
and the escape room, reached by `Action.CLIMB`, with a single implicit goal.
The user requires the match to become a traversal of the cave with an
explicitly chosen objective. This record exists because `.specs/plan.md` must
not be rewritten to match later code.

Decision:
The spawn stays `START_POSITION = Position(1, 1)` facing `NORTH`. The exit
becomes the opposite corner, derived once by
`exit_position_for(rows, cols)` -> `Position(rows, cols)` and exposed as
`GameConfig.exit_position`; the canonical 6x6 map therefore exits at `[6,6]`.
Map generation protects that room, so the protected set becomes the three safe
initial cells plus the exit, computed by `protected_cells(rows, cols)`; the
rooms adjacent to the exit stay randomly generated. Escape is automatic: the
`World` checks the objective the moment the agent occupies the exit room,
however it arrived, including a bat teleport. `Action.CLIMB` stays in the enum
for compatibility but can no longer end a game anywhere, including `[1,1]`.
A new `GameObjective` enum in the game layer offers `ESCAPE_FAST` (the exit
alone ends the match) and `COLLECT_ALL_GOLD` (`collected_gold >=
required_gold`, derived by the `World` from the generated map, must hold
first). The objective is chosen explicitly in the setup screen alongside the
mode and is carried by `SessionSettings` into both the `World` and
`SimpleAgent`.

Reason:
Making the exit a far corner turns the match into an actual traversal, which
is the user's stated goal, and deriving it from the map dimensions keeps
smaller test maps valid instead of hardcoding `[6,6]`. Automatic escape
removes a turn that carried no decision. Keeping the objective in the game
layer rather than the UI preserves the single source of truth for terminal
rules: the manual and autonomous modes share one `World` condition.

Consequences:
This supersedes, for all later work, the plan consequences that made
`START_POSITION` the escape room, that made returning to `[1,1]` a rational
exit target, and that made `CLIMB` a victory. DEC-006's utility heuristic
survives as a risk policy but no longer decides a physical destination, and
its "return to `[1,1]` and climb there" clause is void. The canonical 6x6
entity capacity drops from 33 to 32 rooms. `Strategy` now branches on the
objective: `ESCAPE_FAST` orders the safe frontier by real planned action cost
plus the Manhattan lower bound to the exit and deliberately skips glitter,
while `COLLECT_ALL_GOLD` still grabs gold and may not escape before the last
one is collected, so `TURN_LIMIT` and `DEAD` remain legitimate outcomes.
Safety filtering still runs before any distance heuristic. Map solvability is
deliberately not guaranteed: no rejection sampling was added. The historical
FASE 1-21 statuses are unchanged; only FASE 21's README content was revalidated.

Evidence:
User authorization of maintenance `GAME-GOAL-EXIT-CORNER-003` on 2026-09-25;
`src/wumpus/game/objective.py`; `src/wumpus/game/config.py::exit_position_for`,
`protected_cells`, `available_entity_cells`;
`src/wumpus/environment/world.py::World._exit_requirement_satisfied`;
`src/wumpus/agent/strategy.py`; `tests/unit/test_game_goal_exit.py`;
`tests/unit/test_strategy.py`; `tests/unit/test_retro_setup.py`;
`tests/unit/test_retro_tiles.py`; `tests/e2e/test_seeded_games.py`;
`tests/test_readme.py`.

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
