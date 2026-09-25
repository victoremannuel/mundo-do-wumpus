# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 12 — Strategy (`VERIFIED`)

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
| FASE 13 — Wumpus hunting | `NOT_STARTED` | — |
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
- Last completed phase: FASE 12 — Strategy.
- Completed acceptance criteria: Implemented the priority-1-to-4 decision
  hierarchy (grab gold, climb/return once no safe frontier remains while
  carrying gold, otherwise route to the nearest reachable unvisited safe
  cell), wired `find_path`/`plan_actions` into `SimpleAgent` through a
  persisted `deque[Action]` plan cache that survives across turns and is
  invalidated only by a position/expected-path mismatch (covers bumps and
  bat teleports without special-casing either), and a reachability-aware
  target search that tries unexplored candidates nearest-first instead of
  giving up on the first (possibly disconnected) pick.
- Remaining acceptance criteria: None for FASE 12. Priority 5 (shooting a
  confirmed Wumpus) requires FASE 13's alignment/firing mechanics; priorities
  6-7 (least-risk fallback, forced return under excessive risk) require
  FASE 14's Risk engine. `Strategy.decide` returns `None` when no priority in
  this phase applies, and `SimpleAgent` keeps its pre-existing bounded random
  fallback for that case, documented below.
- Last verified commands: `.venv/bin/python -m pytest
  tests/unit/test_strategy.py -q`; `.venv/bin/python -m pytest
  tests/unit/test_strategy.py tests/unit/test_simple_agent.py
  tests/unit/test_planner.py tests/unit/test_engine.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`;
  an 80-seed stress sweep over the real `MapGenerator`/`World`/`GameEngine`
  loop checking for exceptions or hangs.
- Result: Targeted tests `11 passed`; affected tests `44 passed`; full suite
  `170 passed`; compilation exit 0; 80-seed stress run completed every game
  (53 `ESCAPED`, 27 `DEAD` — deaths are expected since risk avoidance and
  Wumpus hunting are still deferred) with no crash or hang. Independent logic
  review found one CONFIRMED bug (nearest-by-raw-distance target selection
  had no reachability check, so an unreachable-but-nearer safe cell — e.g.
  across a bat-teleport gap — could permanently starve exploration); fixed by
  trying candidates nearest-first with a `find_path` reachability check per
  candidate, with a regression test added. Independent specification review
  confirmed `COMPLIANT` after this checkpoint records the phase in the state
  files.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/strategy.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/agent/__init__.py`
- `tests/unit/test_strategy.py`
- `tests/unit/test_simple_agent.py`
- `tests/unit/test_memory.py`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 44 priorities 1-4: `Strategy.decide` checks glitter (GRAB), then
  the literal section 45 exit condition (gold and no safe frontier: CLIMB at
  start, otherwise route toward it), then routes to the nearest reachable
  unvisited safe cell.
- Section 45 (minimal literal exit condition only): `collected_gold > 0 and
  not unexplored`, without inventing the fuller multi-factor utility policy
  section 45/46 describe as optional and out of this phase's scope.
- Sections 51-52: the FASE 11 `deque[Action]` plan is cached across
  `decide()` calls and consumed one action per cycle; it is discarded and
  recomputed when the observed position no longer matches the plan's
  expected current cell (covers unexpected bumps and bat teleports) or when
  the pursued target is no longer a valid candidate.
- Section 99/49 corollary: candidate targets are only ever cells in
  `knowledge.safe`, and unreachable candidates (safe but not yet connected
  through other safe cells) are skipped in favor of the next-nearest
  reachable one rather than stalling the agent.
- Section 100: `test_strategy_grabs_gold_regardless_of_the_safe_frontier`
  confirms GRAB fires independently of frontier state.
- Section 101: `test_strategy_heads_toward_the_start_with_gold_and_no_safe_frontier`
  and `SimpleAgent`'s existing exit-position test confirm the agent routes
  toward `[1,1]` when carrying gold with no safe frontier left, elsewhere.
- Sections 57–59: `strategy.py` imports only `wumpus.agent.knowledge`,
  `wumpus.agent.planner`, `wumpus.domain`, and `wumpus.game.config`; it never
  imports `wumpus.environment` or references hidden map/World state,
  verified by the existing AST boundary test (now covering `strategy.py`
  automatically).

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- Priority 5 (shoot a confirmed Wumpus blocking a useful route) is not
  implemented; it requires FASE 13's alignment and firing mechanics.
- Priorities 6-7 (least-risk fallback, forced return under excessive risk)
  are not implemented; they require FASE 14's Risk engine. Until then,
  `SimpleAgent` falls back to bounded random movement whenever `Strategy`
  finds no known-safe target, which can lead to death on generated maps with
  hazards — expected and out of this phase's scope.
- Section 45/46's fuller utility-based exit policy (probabilistic cost model,
  risk tolerance before/after gold) is deferred to FASE 15 — Política de
  saída; FASE 12 implements only the literal minimal exit condition the plan
  gives as a FASE-12 test case (section 101).
- `AgentMemory` records only the final position observable after a bat chain;
  hidden intermediate teleport destinations are correctly unavailable to it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/UI/CLI work. FASE 7 exposes only the terminal engine data it can
  already prove and does not claim those sections as verified.
- Console rendering, debug map, and the CLI remain unimplemented until FASE 16
  to FASE 18; the engine exposes `on_render` and `on_render_final` hooks for them.
- When FASE 13 adds shooting, it must reconcile historical stench constraints
  and call the existing dead-Wumpus knowledge transition after a scream/kill.

## Next action

Begin FASE 13 — Wumpus hunting by implementing confirmation-driven alignment,
firing, and replanning: when a confirmed Wumpus blocks the only useful route,
align toward it, SHOOT, and reconcile historical stench constraints plus the
existing dead-Wumpus knowledge transition after a scream/kill, feeding the
result back into `Strategy`'s priority 5.

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

2026-09-24 — FASE 12 — Strategy verified: priority 1-4 decision hierarchy
wired into `SimpleAgent` via the FASE 11 planner, targeted/affected/full
tests, compilation, an 80-seed real-map stress run, and independent logic/
specification reviews after fixing a confirmed reachability bug in target
selection.
