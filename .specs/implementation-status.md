# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 14 — Risk engine (`VERIFIED`)

## Phase ledger

Populate this table from the phase headings in `.specs/plan.md`. Do not invent,
rename, merge, or reorder phases.

| Phase | Status | Verified evidence |
|---|---|---|
| FASE 1 — Scaffold | `VERIFIED` | `2 passed`; `compileall` passed; specification audit `COMPLIANT`. |
| FASE 2 — Domínio | `VERIFIED` | `13 passed` targeted; `15 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 3 — Gerador | `VERIFIED` | `28 passed` targeted; `43 passed` full; 100-seed audit passed; audit `COMPLIANT`. |
| FASE 4 — Ambiente | `VERIFIED` | `26 passed` targeted; `69 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 5 — Flecha | `VERIFIED` | `35 passed` targeted; `78 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 6 — Morcegos | `VERIFIED` | `42 passed` targeted; `85 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 7 — Engine | `VERIFIED` | `24 passed` targeted; `109 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 8 — Memory | `VERIFIED` | `7 passed` targeted; `31 passed` affected; `116 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 9 — Knowledge Base | `VERIFIED` | `14 passed` targeted; `45 passed` affected; `130 passed` full; `compileall` passed; independent audit `COMPLIANT`. |
| FASE 10 — Inference Engine | `VERIFIED` | `18 passed` targeted; `64 passed` affected; `149 passed` full; `compileall`, determinism, and anti-cheat checks passed; independent logic/specification audits `COMPLIANT`. |
| FASE 11 — Planner | `VERIFIED` | `10 passed` targeted; `18 passed` affected (`test_simple_agent.py`); `159 passed` full; `compileall` passed; specification and logic audits `COMPLIANT`. |
| FASE 12 — Strategy | `VERIFIED` | `11 passed` targeted; `44 passed` affected; `170 passed` full; `compileall` passed; 80-seed real-map stress run with no crash; independent specification and logic audits `COMPLIANT` after a confirmed reachability bug was fixed. |
| FASE 13 — Wumpus hunting | `VERIFIED` | `18 passed` (`test_strategy.py`); `19 passed` (`test_inference.py`); `9 passed` (`test_memory.py`); `179 passed` full; `compileall` passed; 2000-seed real-map stress run with 0 crashes and 0 unsound kill attributions; independent specification and logic audits `COMPLIANT` after fixing two confirmed defects (an inference false-confirmation regression and an unsound kill-attribution gap). |
| FASE 14 — Risk engine | `VERIFIED` | `13 passed` (`test_risk.py`); `24 passed` (`test_strategy.py`); `198 passed` full; `compileall` passed; 1000-seed real-map stress run with 0 crashes after the fallthrough fix (845 `ESCAPED`, 150 `DEAD`, 5 `TURN_LIMIT`); independent specification and logic audits `COMPLIANT` after fixing a confirmed HIGH-severity priority-cascade short-circuit and recording `DEC-005`. |
| FASE 15 — Política de saída | `NOT_STARTED` | — |
| FASE 16 — UI | `NOT_STARTED` | — |
| FASE 17 — Debug | `NOT_STARTED` | — |
| FASE 18 — CLI | `NOT_STARTED` | — |
| FASE 19 — Integration tests | `NOT_STARTED` | — |
| FASE 20 — E2E | `NOT_STARTED` | — |
| FASE 21 — README final | `NOT_STARTED` | — |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 14 — Risk engine.
- Completed acceptance criteria: Implemented priority 6 (least-risk cell
  evaluation) and priority 7 (forced return to `[1,1]` when the least-risk
  option is still excessive) in a new `src/wumpus/agent/risk.py` module,
  wired into `Strategy.decide` right after priority 5. `risk.cell_risk`
  scores a cell per section 43's additive hazard-candidate model
  (PIT=3, WUMPUS=4, BAT=2), `0.0` for a proven-safe cell, and
  `CONFIRMED_DANGER` (`inf`) for a confirmed live pit or Wumpus (a confirmed
  bat scores the same finite weight as a possible one, since bats are
  non-lethal). `risk.least_risk_candidate` restricts candidates to cells
  orthogonally adjacent to the agent's currently safe-reachable region, and
  `Strategy._approach` routes to a safe staging cell next to the target and
  takes the calculated final `MOVE_FORWARD` risk step itself (the planner's
  `find_path` only ever routes through already-safe cells, by design).
  Independent specification and logic review on 2026-09-25 found and this
  checkpoint fixed one CONFIRMED HIGH-severity, pre-existing control-flow
  bug (not new to this phase, but only now consequential): `Strategy.decide`
  returned `_pursue`'s result unconditionally from the priority-2 and
  priority-3/4 branches, so a chosen-but-unreachable route (e.g. an
  unclassified gap disconnecting the safe region) silently discarded every
  lower priority, including the new priorities 5-7. Fixed by only returning
  early when `_pursue` actually produces an action, otherwise falling
  through -- this also resolves a related specification-review finding
  (a gold-holding agent with a blocked route home previously had no chance
  at priorities 5-7 either). Recorded as `DEC-005`, which also settles that
  `risk.RISK_THRESHOLD` stays a single, non-gold-conditioned constant,
  deferring sections 47-48's gold-conditioned risk tolerance to FASE 15.
- Remaining acceptance criteria: None for FASE 14. Sections 45-48's full
  exit-policy reasoning (utility model, gold-conditioned risk tolerance,
  rational abandonment) remains FASE 15's scope; `Strategy.decide` still
  returns `None` only in the residual case of being at the start cell with
  nothing left to explore or risk, and `SimpleAgent` keeps its bounded
  random fallback for exactly that gap.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_risk.py
  tests/unit/test_strategy.py tests/unit/test_simple_agent.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`;
  two 1000-seed stress sweeps (before and after the fallthrough fix) over
  the real `MapGenerator`/`World`/`GameEngine` loop, checking for exceptions.
- Result: `test_risk.py` 13 passed; `test_strategy.py` 24 passed; full suite
  `198 passed`; compilation exit 0. Stress sweep before the fix: 0 crashes,
  814 `ESCAPED`, 181 `DEAD`, 5 `TURN_LIMIT`. Stress sweep after the fix:
  0 crashes, 845 `ESCAPED`, 150 `DEAD`, 5 `TURN_LIMIT` (the escape-rate
  increase reflects agents that previously gave up early on a disconnected
  safe region now falling through to a resolving risk step). Independent
  logic review found one CONFIRMED HIGH bug (the priority-cascade
  short-circuit above, with a deterministic repro) and confirmed as sound:
  `cell_risk`'s handling of every reachable `KnownCell` state,
  `least_risk_candidate`'s reachability/termination, `_approach`'s
  direction/plan bookkeeping, the `collected_gold` priority interaction,
  determinism, death/teleport handling, and the agent/environment boundary.
  Independent specification review classified `PARTIALLY_COMPLIANT` pending
  two items: a citation to a not-yet-written `DEC-005` (now written) and the
  same gold-plus-blocked-route gap (now resolved by the same fix) --
  otherwise confirmed the risk-scoring model, priority ordering, absence of
  duplicated magic values against `wumpus/environment/scoring.py`, and that
  test assertions prove the requirements rather than merely execute code.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/risk.py` (new)
- `src/wumpus/agent/strategy.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/agent/__init__.py`
- `tests/unit/test_risk.py` (new)
- `tests/unit/test_strategy.py`
- `.specs/decisions.md`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 42-43: `risk.cell_risk` classifies every cell (`0.0` safe,
  `CONFIRMED_DANGER` for a confirmed live pit/Wumpus, additive
  `HAZARD_RISK_WEIGHTS` sum otherwise), with negative evidence and
  elimination reductions inherited for free from `KnowledgeBase`/
  `InferenceEngine` rather than duplicated
  (`test_cell_risk_ignores_a_hazard_type_already_ruled_out`).
- Section 44 priority 6: `Strategy._explore_at_risk` steps into the
  reachable, not-yet-safe cell with the lowest `cell_risk` score once
  priorities 1-5 find nothing, provided it is within `RISK_THRESHOLD`
  (`test_strategy_prioritizes_the_lowest_scoring_risk_candidate`,
  `test_strategy_steps_into_the_chosen_risk_candidate_after_turning`).
- Section 44 priority 7: when the least-risk reachable cell exceeds
  `RISK_THRESHOLD`, or none exists, the agent routes back toward
  `START_POSITION` instead of taking the risk
  (`test_strategy_declines_a_risk_above_the_threshold_and_returns_to_start`).
- A confirmed-danger cell (live pit or Wumpus) is never selected as a risk
  candidate (`test_strategy_never_treats_a_confirmed_danger_cell_as_a_risk_candidate`,
  `test_least_risk_candidate_never_returns_a_confirmed_danger_cell`).
- Regression: priorities 5-7 are reachable even when priority 3/4's chosen
  unexplored cell, or priority 2's route home, turns out unreachable --
  including while holding gold --
  (`test_strategy_falls_through_to_risk_when_every_unexplored_cell_is_unreachable`,
  `test_strategy_falls_through_to_risk_when_the_way_home_is_blocked_with_gold`).
- Sections 57–59: `risk.py` imports only `wumpus.agent.knowledge` and
  `wumpus.domain`; `strategy.py`'s additions import only `wumpus.agent.risk`
  alongside its existing agent-owned imports -- never `wumpus.environment`
  or hidden map/World state, verified by the existing AST boundary test
  (`test_agent_package_never_imports_the_environment_or_hidden_map_types`,
  which globs every file in `src/wumpus/agent/`, including the new module).

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- Priority 5 does not prove the targeted confirmed Wumpus is the actual
  obstruction blocking further safe exploration (accepted trade-off,
  `DEC-004`).
- `confirm_kill`'s soundness-first attribution rule means many kills go
  unattributed in practice on larger, less-explored maps -- intentional
  (sound-but-incomplete), not a defect.
- `risk.RISK_THRESHOLD` is a single constant, not conditioned on whether the
  agent already holds gold; sections 47-48's differing risk tolerance
  before/after gold is deferred to FASE 15 (`DEC-005`).
- Section 45/46's fuller utility-based exit policy (probabilistic cost model,
  rational abandonment conditions) remains deferred to FASE 15. Reaching the
  start cell with nothing left to explore or risk still falls to
  `SimpleAgent`'s bounded random fallback rather than a deliberate CLIMB
  decision, since that decision belongs to FASE 15.
- `AgentMemory` records only the final position observable after a bat chain;
  hidden intermediate teleport destinations are correctly unavailable to it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/UI/CLI work.
- Console rendering, debug map, and the CLI remain unimplemented until FASE 16
  to FASE 18; the engine exposes `on_render` and `on_render_final` hooks for them.

## Next action

Begin FASE 15 — Política de saída by implementing the rational-abandonment
exit policy (section 45), a utility heuristic (section 46), and
gold-conditioned risk tolerance (sections 47-48, `DEC-005`'s deferred item),
replacing `SimpleAgent`'s residual random fallback with a deliberate CLIMB
decision once the agent is at the start cell with nothing left to explore or
risk.

## Checkpoint update contract

After each phase attempt, update:

- exact phase number and title;
- phase and overall status;
- files changed;
- requirements satisfied;
- commands executed and their results;
- blockers, limitations, and technical debt;
- next action;
- checkpoint type and expected post-checkpoint worktree state;
- last update date.

Mark a phase `VERIFIED` only after targeted validation, the full regression
suite, and specification compliance all pass. Commit the state file in the same
checkpoint as the implementation it describes.

## Last update

2026-09-25 — FASE 14 — Risk engine verified: priorities 6-7 (least-risk cell
evaluation, forced return under excessive risk) added via a new `risk.py`
module and `Strategy._explore_at_risk`/`_approach`. Independent review found
and this checkpoint fixed a confirmed HIGH-severity priority-cascade
short-circuit predating this phase (an unreachable chosen route silently
discarded every lower priority), recorded as `DEC-005` alongside the
decision to keep `RISK_THRESHOLD` non-gold-conditioned. Targeted/full tests,
compilation, and two 1000-seed real-map stress runs (before/after the fix)
with 0 crashes both times.
