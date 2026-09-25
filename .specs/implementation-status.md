# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 19 — Integration tests (`VERIFIED`)

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
| FASE 15 — Política de saída | `VERIFIED` | `49 passed` targeted; `215 passed` full; `compileall` passed; final 100-seed stress run with 0 crashes and 50 deterministic replays; independent specification and logic audits `COMPLIANT` after fixing exhausted-gold and disconnected-fallback defects. |
| FASE 16 — UI | `VERIFIED` | `61 passed` targeted (`test_reasoning.py`, `test_console.py`, `test_strategy.py`, `test_simple_agent.py`); `228 passed` full; `compileall` passed; independent specification review `COMPLIANT` after addressing a boundary-test gap, an additive-diff confirmation, a recorded decision, and two presentation cleanups. |
| FASE 17 — Debug | `VERIFIED` | `5 passed` targeted; `48 passed` affected; `233 passed` full; `compileall`, deterministic snapshots, and anti-cheat checks passed; specification audit `COMPLIANT`. |
| FASE 18 — CLI | `VERIFIED` | `7 passed` targeted; `240 passed` full; `compileall` passed; deterministic seed replay, `--debug`/`--step`/`--no-delay` manual smoke checks passed; specification audit `COMPLIANT`. |
| FASE 19 — Integration tests | `VERIFIED` | `2 passed` targeted; `4 passed` integration/determinism/antitrapaça; `242 passed` full; `compileall` passed; independent specification and test audits `COMPLIANT`/`PASS`. |
| FASE 20 — E2E | `NOT_STARTED` | — |
| FASE 21 — README final | `NOT_STARTED` | — |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 19 — Integration tests.
- Completed acceptance criteria: Added a dedicated integration suite that runs
  the production `GeneratedMap -> World -> SimpleAgent -> GameEngine` stack,
  without doubles, against two deterministic known maps. The first proves
  autonomous exploration, gold collection, score propagation, return to
  `[1,1]`, and `CLIMB`. The mixed map proves perception-driven inference,
  confirmed-pit avoidance, confirmed-Wumpus hunting/death reconciliation,
  gold collection, score propagation, safe return, and escape. Tests construct
  hidden maps as fixtures but never pass them to the agent; the engine keeps
  `AgentObservation`/`ActionResult` as the only runtime information surfaces.
- Remaining acceptance criteria: None for FASE 19.
- Last verified commands: `.venv/bin/python -m pytest
  tests/integration/test_known_maps.py -q`; `.venv/bin/python -m pytest
  tests/integration/test_known_maps.py
  tests/unit/test_simple_agent.py::test_agent_package_never_imports_the_environment_or_hidden_map_types
  tests/unit/test_engine.py::test_seeded_games_with_the_simple_agent_are_reproducible
  -q`; `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src
  main.py`; `git diff --check`.
- Result: targeted `2 passed`; integration/determinism/antitrapaça `4 passed`;
  full suite `242 passed` (up from 240); compilation exited 0. Ruff was not
  installed/configured. Independent specification and architecture review was
  `COMPLIANT` after state persistence, and independent test review was `PASS`;
  its score-propagation recommendation was incorporated before final evidence.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `tests/integration/test_known_maps.py` (new)
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 119, FASE 19: the unmodified real logical agent runs through the real
  engine and environment against multiple known maps, with assertions on
  terminal behavior and agent-owned knowledge rather than smoke-only execution.
- Sections 57-60: integration preserves the antitrapaça boundary; known hidden
  state exists only in the test fixture and environment, while `SimpleAgent`
  receives reduced observations/results through `GameEngine`.
- Sections 134-135: integrated scenarios prove autonomy, perception/inference,
  safe planning, confirmed-danger avoidance, rational shooting, gold
  collection, synchronized scoring, return to the exit, and successful climb.
- Section 137: the complete pytest suite remains green with zero failures.

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
- A safely disconnected agent with no acceptable risk step rotates in place
  until knowledge changes or `MAX_TURNS` ends the game. This is deterministic
  and fail-closed since FASE 15; explicit cycle detection and loop recovery
  remain later plan work (sections 105-108).
- `AgentMemory` records only the final position observable after a bat chain;
  hidden intermediate teleport destinations are correctly unavailable to it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are not printed in the
  final panel; deferred to later statistics work (not a FASE 18 acceptance
  criterion, which lists only the five flags).
- The reasoning panel always shows the *previous* turn's `DecisionReason`
  alongside the newly rendered observation, never a same-turn preview of the
  upcoming action -- an inherent consequence of the already-`VERIFIED` FASE 7
  engine's `observe -> render -> decide` order, recorded as `DEC-007`.
- `SimpleAgent`'s constructor accepts an `rng: random.Random` parameter that
  is stored but never used internally (pre-existing since earlier phases);
  `main.py` passes the same RNG instance used for map generation/world
  mechanics. Since the parameter is unused, no entropy-sharing side effect
  exists today; noted by the FASE 18 specification review as a LOW,
  non-blocking observation for future attention if that parameter ever
  becomes load-bearing.
- FASE 19 intentionally uses two deterministic known maps and does not add a
  multi-seed generated-map matrix, which belongs to FASE 20. Bat teleport and
  lethal-map integration remain covered at unit/component level rather than by
  this phase's known-map scenarios.

## Next action

Begin FASE 20 — E2E: execute the production game over at least 10 fixed seeds,
prove bounded termination without exceptions, and keep deterministic evidence.

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

2026-09-25 — FASE 19 — Integration tests verified: added two known-map tests
running the unmodified `SimpleAgent`, `World`, and `GameEngine` together. They
prove gold collection/return plus mixed-map inference, confirmed-pit avoidance,
Wumpus hunting, synchronized scoring, and escape without hidden-state leakage.
Targeted `2 passed`, full `242 passed`, compilation passed, and independent
specification/test audits were `COMPLIANT`/`PASS`.
