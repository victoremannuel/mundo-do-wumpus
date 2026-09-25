# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 20 — E2E (`VERIFIED`)

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
| FASE 20 — E2E | `VERIFIED` | `10 passed` targeted; `14 passed` affected; `252 passed` full; 100-seed stress completed without exceptions; independent specification/test audits `COMPLIANT`/`PASS`. |
| FASE 21 — README final | `NOT_STARTED` | — |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 20 — E2E.
- Completed acceptance criteria: Added a fixed-seed E2E matrix using the plan's
  ten example seeds (`1`, `2`, `3`, `10`, `20`, `42`, `100`, `123`, `999`,
  `2026`). Every case constructs the production procedural map, real `World`,
  unmodified `SimpleAgent`, and `GameEngine`; runs to a bounded terminal
  `GameStatus`; then replays from the same seed and compares the complete
  `GameOutcome` for determinism.
- Remaining acceptance criteria: None for FASE 20.
- Last verified commands: `.venv/bin/python -m pytest
  tests/e2e/test_seeded_games.py -q`; `.venv/bin/python -m pytest
  tests/e2e/test_seeded_games.py tests/integration/test_known_maps.py
  tests/unit/test_simple_agent.py::test_agent_package_never_imports_the_environment_or_hidden_map_types
  tests/unit/test_engine.py::test_seeded_games_with_the_simple_agent_are_reproducible
  -q`; 100-seed generated-map stress script; `.venv/bin/python -m pytest -q`;
  `.venv/bin/python -m compileall -q src main.py`; `git diff --check`.
- Result: targeted `10 passed`; E2E/integration/determinism/antitrapaça
  `14 passed`; full suite `252 passed` (up from 242); compilation exited 0.
  The 100-seed stress run completed without exceptions or invalid-state
  assertions: 84 `ESCAPED`, 12 `DEAD`, 4 `TURN_LIMIT`, maximum 2000 turns.
  Ruff remains unconfigured/not installed. Independent specification review
  was `COMPLIANT`, and independent test review was `PASS`; neither found a
  blocker to verification.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `tests/e2e/test_seeded_games.py` (new)
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Sections 104 and 119, FASE 20: all ten fixed seeds execute the production
  autonomous stack to a bounded terminal status without exceptions.
- Sections 8, 105, and 126: every seed is replayed with injected RNG state;
  complete outcomes match and every run ends in at most `MAX_TURNS` (2000).
- Sections 124 and 137: the E2E matrix detects uncaught errors or unbounded
  execution, while the complete pytest suite remains green with zero failures.
- Section 138: a separate 100-seed stress run completed without crashes or
  invalid-state assertions; victory in every map was intentionally not
  required.

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
- The 100-seed stress run reached `TURN_LIMIT` on 4 maps. This is a bounded,
  plan-defined terminal status rather than a crash; explicit cycle detection,
  `knowledge_revision`, and objective blacklisting from sections 106-108 remain
  unimplemented technical debt already documented above.

## Next action

Begin FASE 21 — README final: document the plan-required architecture,
behavior, PEAS model, execution modes, tests, examples, and limitations. Do
not alter production behavior unless the documentation audit exposes a real
defect.

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

2026-09-25 — FASE 20 — E2E verified: added ten deterministic fixed-seed
runs over the complete production game, each replayed to prove identical final
outcomes. Targeted `10 passed`, affected `14 passed`, full `252 passed`,
compilation passed, and a separate 100-seed stress run completed without
exceptions. Independent specification/test audits were `COMPLIANT`/`PASS`.
