# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 13 — Wumpus hunting (`VERIFIED`)

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
| FASE 14 — Risk engine | `NOT_STARTED` | — |
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
- Last completed phase: FASE 13 — Wumpus hunting.
- Completed acceptance criteria: Implemented priority 5 (shoot a confirmed
  Wumpus once priorities 1-4 find nothing) with alignment-seeking when not
  already sharing a row/column, and `Strategy.confirm_kill` to reconcile
  knowledge after a `SHOOT` result per section 56. Fixed two real defects
  found via stress-testing against generated maps (not visible from static
  reasoning alone): (1) a FASE 10 `InferenceEngine` false-confirmation bug,
  where a historical stench reading whose explaining Wumpus later died could
  get wrongly reassigned by elimination to an unrelated neighbor; (2) an
  unsound `confirm_kill` attribution gap, where a cell the agent had simply
  never gathered evidence about (neither confirmed, possible, nor proven
  Wumpus-free) was wrongly treated as proof of absence, risking a live
  Wumpus being marked dead and safe.
- Remaining acceptance criteria: None for FASE 13. Priorities 6-7
  (least-risk fallback, forced return under excessive risk) still require
  FASE 14's Risk engine; `Strategy.decide` returns `None` when no priority
  through 5 applies, and `SimpleAgent` keeps its bounded random fallback.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_strategy.py
  tests/unit/test_inference.py tests/unit/test_memory.py
  tests/unit/test_knowledge.py -q`; `.venv/bin/python -m pytest -q`;
  `.venv/bin/python -m compileall -q src`; a 2000-seed stress sweep over the
  real `MapGenerator`/`World`/`GameEngine` loop, checking both for exceptions
  and for `agent.memory.knowledge.dead_wumpus` never containing a cell the
  real `World` still counts alive (soundness, not just crash-freedom).
- Result: `test_strategy.py` 18 passed; `test_inference.py` 19 passed;
  `test_memory.py` 9 passed; full suite `179 passed`; compilation exit 0;
  2000-seed stress run: 0 crashes, 0 unsound kill attributions (1534
  `ESCAPED`, 465 `DEAD`, 1 `TURN_LIMIT` — deaths and turn limits are expected
  since risk avoidance, FASE 14, is still deferred). Independent logic review
  found one CRITICAL bug (the `confirm_kill` attribution gap above) and
  independent specification review found one MEDIUM item (priority 5 does
  not prove the targeted Wumpus is the actual route blocker, recorded as
  `DEC-004`) and one LOW item (a duplicated direction-delta table, now
  consolidated into `planner.FORWARD_DELTA`). Both the CRITICAL and LOW
  items were fixed; specification review confirmed `COMPLIANT` after this
  checkpoint records the phase in the state files.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/strategy.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/agent/inference.py`
- `src/wumpus/agent/planner.py`
- `src/wumpus/agent/__init__.py`
- `tests/unit/test_strategy.py`
- `tests/unit/test_inference.py`
- `tests/unit/test_memory.py`
- `.specs/decisions.md`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 54: `Strategy._hunt` reads only `knowledge.confirmed_wumpus`, never
  `possible_wumpus`; a merely-suspected Wumpus never triggers a shot
  (`test_strategy_does_not_shoot_a_merely_possible_wumpus`).
- Section 55: firing requires `position.row == wumpus.row or position.col ==
  wumpus.col`; when unaligned, the agent routes to the nearest reachable
  `knowledge.safe` cell sharing that row/column before firing
  (`test_strategy_routes_to_an_alignment_cell_before_shooting`).
- Section 56: `Strategy.confirm_kill` registers the death
  (`knowledge.mark_wumpus_dead`), recomputes potential stench going forward
  (via the `InferenceEngine` fix, so old stench explained by the now-dead
  Wumpus is never reassigned), and updates the safety of the newly-dead cell
  (which becomes `safe` once every hazard type is ruled out there, per the
  pre-existing `mark_wumpus_dead` transition) -- but only when the shot's
  outcome is actually *determinable*: every cell strictly closer along the
  line of fire must already be proven `not_wumpus`, otherwise the kill is
  left unattributed rather than guessed
  (`test_strategy_confirm_kill_does_not_attribute_through_an_unclassified_cell`).
- Section 44 priority 5: fires only after priorities 1-4 find no reachable
  unexplored safe cell, per `DEC-004`'s documented interpretation of
  "bloqueie rota útil".
- Section 21 (arrow cost/no limit): unaffected, already `VERIFIED` in FASE 5;
  `Strategy` only ever issues `Action.SHOOT`, cost/scoring remain centralized
  in `wumpus/environment/scoring.py`.
- Sections 57–59: `strategy.py` still imports only `wumpus.agent.knowledge`,
  `wumpus.agent.planner`, `wumpus.domain`, and `wumpus.game.config`; the line
  of fire is walked using `knowledge.all_cells` and the `ActionResult` DTO
  only, never `wumpus.environment` or hidden map/World state, verified by
  the existing AST boundary test.

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- Priority 5 does not prove the targeted confirmed Wumpus is the actual
  obstruction blocking further safe exploration (accepted trade-off,
  `DEC-004`); a future FASE 14 frontier/connectivity check could tighten
  this once risk-based reasoning exists.
- `confirm_kill`'s soundness-first attribution rule means many kills go
  unattributed in practice on larger, less-explored maps (a cell strictly
  closer on the line of fire is often still unclassified) -- the agent then
  keeps treating that Wumpus as confirmed-alive and simply stops trying to
  shoot it again until new information arrives; this is intentional
  (sound-but-incomplete) rather than a defect.
- Priorities 6-7 (least-risk fallback, forced return under excessive risk)
  are not implemented; they require FASE 14's Risk engine. Until then,
  `SimpleAgent` falls back to bounded random movement whenever `Strategy`
  finds no known-safe target and no confirmed, shootable Wumpus, which can
  lead to death on generated maps with hazards -- expected and out of this
  phase's scope.
- Section 45/46's fuller utility-based exit policy (probabilistic cost model,
  risk tolerance before/after gold) remains deferred to FASE 15.
- `AgentMemory` records only the final position observable after a bat chain;
  hidden intermediate teleport destinations are correctly unavailable to it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/UI/CLI work.
- Console rendering, debug map, and the CLI remain unimplemented until FASE 16
  to FASE 18; the engine exposes `on_render` and `on_render_final` hooks for them.

## Next action

Begin FASE 14 — Risk engine by implementing least-risk cell evaluation
(priority 6) for when no safe exploration or shootable confirmed Wumpus
remains, and a forced-return trigger (priority 7) when expected risk is
excessive, replacing `SimpleAgent`'s bounded random fallback.

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

2026-09-25 — FASE 13 — Wumpus hunting verified: priority 5 (confirmation,
alignment, firing) added to `Strategy`, a real FASE 10 inference
false-confirmation bug and an unsound kill-attribution gap fixed after
independent review, targeted/full tests, compilation, and a 2000-seed
real-map stress run with 0 crashes and 0 unsound attributions.
