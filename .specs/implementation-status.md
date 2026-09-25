# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 8 — Memory (`NOT_STARTED`)

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
| FASE 8 — Memory | `NOT_STARTED` | — |
| FASE 9 — Knowledge Base | `NOT_STARTED` | — |
| FASE 10 — Inference Engine | `NOT_STARTED` | — |
| FASE 11 — Planner | `NOT_STARTED` | — |
| FASE 12 — Strategy | `NOT_STARTED` | — |
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
- Last completed phase: FASE 7 — Engine.
- Completed acceptance criteria: Implemented the functional game loop
  (`observe → render hook → decide → execute → process_result → final render`),
  the reduced `AgentObservation` surface, terminal statuses `ESCAPED`, `DEAD`, and
  `TURN_LIMIT` with `MAX_TURNS = 2000`, the end-of-game outcome report, and the
  temporary `SimpleAgent` deciding only from observations with an injected RNG.
- Remaining acceptance criteria: None for FASE 7.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_engine.py
  tests/unit/test_simple_agent.py -q`; `.venv/bin/python -m pytest -q`;
  `.venv/bin/python -m compileall -q src`; seeded loop smoke run for seeds 1,
  42, and 2026.
- Result: Targeted tests `24 passed`; full suite `109 passed`; compilation exit
  0; seeded runs reproducible; verification `PASS`; specification compliance
  `COMPLIANT`. Independent critical-phase reviews found and drove corrections
  for render ordering, final rendering, premature outcome status, anti-cheat
  coverage, and overclaimed final-statistics traceability.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only the three required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/__init__.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/domain/__init__.py`
- `src/wumpus/domain/observation.py`
- `src/wumpus/environment/generator.py`
- `src/wumpus/environment/world.py`
- `src/wumpus/game/__init__.py`
- `src/wumpus/game/config.py`
- `src/wumpus/game/engine.py`
- `tests/unit/test_engine.py`
- `tests/unit/test_simple_agent.py`
- `.specs/implementation-status.md`
- `.specs/decisions.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 60: `GameEngine.step` runs the exact plan loop and exposes an
  optional pre-decision render hook; `GameEngine.run` invokes the final render
  hook after the terminal outcome, keeping rendering outside engine rules.
- Sections 57 and 58: `AgentObservation` carries only position, direction,
  perception, score, collected gold, and active state; the agent layer has no
  reference to `World` or the real map.
- Section 26: the loop stops on escape from `[1,1]` and on death.
- Sections 105 and 124: the loop is bounded by `MAX_TURNS = 2000` and finishes
  with `TURN_LIMIT` instead of running forever.
- Sections 119 FASE 7, 125, and 126: the temporary `SimpleAgent` makes the game
  work mechanically and stays deterministic under an injected `random.Random`.

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- `SimpleAgent` is intentionally non-intelligent and has no memory, inference,
  planning, or risk evaluation; FASE 8 onwards replaces it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/UI/CLI work. FASE 7 exposes only the terminal engine data it can
  already prove and does not claim those sections as verified.
- Console rendering, debug map, and the CLI remain unimplemented until FASE 16
  to FASE 18; the engine exposes `on_render` and `on_render_final` hooks for them.

## Next action

Begin FASE 8 — Memory by implementing the agent memory of visited rooms and
perception history, without advanced inference.

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

2026-09-24 — FASE 7 — Engine verified after focused tests, full regression,
source compilation, seeded loop reproduction, architecture verification, and
specification compliance.
