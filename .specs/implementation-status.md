# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 16 — UI (`VERIFIED`)

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
- Last completed phase: FASE 16 — UI.
- Completed acceptance criteria: Implemented the Rich console presentation
  required by sections 62-68. `src/wumpus/ui/console.py::ConsoleRenderer`
  renders a known-map panel (section 62) built exclusively from
  `KnowledgeBase` classifications and the agent's own position/direction,
  a perceptions panel (section 65), an agent status panel (section 66), and
  a reasoning panel (sections 67-68). Colors and symbols (sections 63-64)
  are centralized in `src/wumpus/ui/symbols.py`. `Strategy` gained a new
  `DecisionReason` (`src/wumpus/agent/reasoning.py`) recorded at every
  existing decision return point as a purely additive change (confirmed via
  `git diff HEAD -- src/wumpus/agent/strategy.py`: only new lines plus two
  `return X` -> `action = X; return action` restructurings, no condition or
  branch order changed) -- so the agent produces structured "why" data and
  the renderer translates it to text, never the reverse.
- Remaining acceptance criteria: None for FASE 16. The renderer is not yet
  wired into a runnable entry point; that wiring belongs to FASE 18 (CLI).
- Last verified commands: `.venv/bin/python -m pytest
  tests/unit/test_reasoning.py tests/unit/test_console.py
  tests/unit/test_strategy.py tests/unit/test_simple_agent.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`;
  `git diff --check`.
- Result: targeted `61 passed`; full suite `228 passed` (up from 215);
  compilation and diff checks exited 0. Independent specification review
  found the implementation `PARTIALLY_COMPLIANT` on first pass (no anti-cheat
  violation, but missing a boundary test for the new `wumpus.ui` package, an
  unconfirmed additive-diff claim, an unrecorded render-timing design
  decision, and two low-severity presentation gaps); all four were
  addressed: added
  `tests/unit/test_console.py::test_ui_package_never_imports_the_environment_or_hidden_map_types`
  (which also caught and fixed a false-positive `Table.grid(...)` call,
  replaced with `Table(box=None, show_header=False, ...)`), confirmed the
  additive-only `strategy.py` diff, recorded `DEC-007`, and reconciled the
  symbol set (removed the unused `GOLD_SYMBOL` since `KnowledgeBase` has no
  per-cell gold classification; wired `GLITTER_COLOR` into the perceptions
  panel; localized the direction label via a new `DIRECTION_LABELS` map).
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/reasoning.py` (new)
- `src/wumpus/agent/strategy.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/agent/__init__.py`
- `src/wumpus/ui/__init__.py` (new)
- `src/wumpus/ui/symbols.py` (new)
- `src/wumpus/ui/console.py` (new)
- `tests/unit/test_reasoning.py` (new)
- `tests/unit/test_console.py` (new)
- `tests/unit/test_strategy.py`
- `.specs/decisions.md`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 62: `render_known_map` renders every cell's classification
  (confirmed hazard, possible hazard, visited, safe, unknown) using only
  `KnowledgeBase`, plus the agent's own position/direction glyph.
- Sections 63-64: `src/wumpus/ui/symbols.py` centralizes every color and
  symbol as the single source of truth for the console layer.
- Section 65: `render_perceptions` shows all six perceived signals with the
  plan's SIM/NÃO convention.
- Section 66: `render_agent_status` shows position, direction, gold, score,
  and an optional step count.
- Sections 67-68: `Strategy.last_reason` exposes a structured
  `DecisionReason` per decision; `render_reasoning` translates it to text
  without the agent composing display strings itself.
- Sections 57-59: the UI package reads only `AgentObservation`, agent-owned
  `KnowledgeBase`, `DecisionReason`, and `GameOutcome` -- never
  `wumpus.environment` or hidden map/world state, now covered by a
  dedicated AST boundary test mirroring the agent package's own.

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
- `ConsoleRenderer` is not yet wired into a runnable entry point; the debug
  dual-map mode and the CLI remain unimplemented until FASE 17 and FASE 18.

## Next action

Begin FASE 17 — Debug by adding the real-map debug view (section 69) through
an explicit debug-only path that never lets production agent code touch the
real map, per AGENTS.md's debug-rendering invariant.

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

2026-09-25 — FASE 16 — UI verified: `rich`-based `ConsoleRenderer` for the
known map, perceptions, agent status, and reasoning panels (sections 62-68),
backed by a new `DecisionReason` the agent records additively at every
existing decision point. Independent specification review found the first
pass `PARTIALLY_COMPLIANT` (missing a `wumpus.ui` boundary test, an
unconfirmed additive-diff claim, an unrecorded render-timing decision, two
presentation gaps); all four addressed, including recording `DEC-007` for
the reasoning panel's inherent one-turn lag under the unchanged FASE 7 engine
order. Targeted/full tests, compilation, and diff validation passed.
