# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 17 — Debug (`VERIFIED`)

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
| FASE 18 — CLI | `NOT_STARTED` | — |
| FASE 19 — Integration tests | `NOT_STARTED` | — |
| FASE 20 — E2E | `NOT_STARTED` | — |
| FASE 21 — README final | `NOT_STARTED` | — |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 17 — Debug.
- Completed acceptance criteria: Added an explicit professor/debug path for
  sections 69-71. `World.debug_snapshot()` returns an immutable current-state
  `DebugWorldSnapshot`; `wumpus.debug.DebugRenderer` is the only presentation
  path that accepts `World`, renders both `MAPA CONHECIDO PELO AGENTE` and
  `MAPA REAL`, and displays the current agent orientation plus live Wumpus,
  pits, uncollected gold, bats, and empty cells. The normal UI, game engine,
  and agent packages do not import the debug package or snapshot type.
- Remaining acceptance criteria: None for FASE 17. CLI wiring for `--debug`
  remains explicitly assigned to FASE 18 by the phase roadmap.
- Last verified commands: `.venv/bin/python -m pytest
  tests/unit/test_debug_renderer.py -q`; `.venv/bin/python -m pytest
  tests/unit/test_debug_renderer.py tests/unit/test_console.py
  tests/unit/test_world.py tests/unit/test_simple_agent.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`;
  100-seed deterministic debug-snapshot replay; `git diff --check`.
- Result: targeted `5 passed`; affected `48 passed`; full suite `233 passed`
  (up from 228); compilation, determinism, anti-cheat, and diff checks exited
  0. Ruff was not installed/configured. Specification compliance review was
  `COMPLIANT` with no open findings.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/environment/world.py`
- `src/wumpus/debug/__init__.py` (new)
- `src/wumpus/debug/renderer.py` (new)
- `src/wumpus/ui/symbols.py`
- `tests/unit/test_debug_renderer.py` (new)
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Sections 69 and 71: professor mode renders the known and real maps together;
  the real map uses current environment state and the centralized `W`, `P`,
  `G`, `B`, `.`, and oriented-agent symbols.
- Section 70: hidden state flows only from `World` to `DebugRenderer` through
  an immutable snapshot. Production agent, engine, and normal UI code neither
  imports nor receives the debug snapshot or renderer.

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
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/CLI work.
- The reasoning panel always shows the *previous* turn's `DecisionReason`
  alongside the newly rendered observation, never a same-turn preview of the
  upcoming action -- an inherent consequence of the already-`VERIFIED` FASE 7
  engine's `observe -> render -> decide` order, recorded as `DEC-007`.
- `ConsoleRenderer` and `DebugRenderer` are not yet wired into a runnable
  entry point; all CLI flags, including `--debug`, belong to FASE 18.

## Next action

Begin FASE 18 — CLI by adding the plan-defined flags (`--seed`, `--debug`,
`--step`, `--delay`, and `--no-delay`) and wiring the existing normal/debug
renderers without changing the agent/environment boundary.

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

2026-09-25 — FASE 17 — Debug verified: added an immutable current real-map
snapshot and an explicit `DebugRenderer` that shows agent knowledge beside the
real map while leaving the agent, engine, and normal UI isolated from hidden
state. Targeted `5 passed`, affected `48 passed`, full `233 passed`, compilation
and deterministic replay passed, and specification audit was `COMPLIANT`.
