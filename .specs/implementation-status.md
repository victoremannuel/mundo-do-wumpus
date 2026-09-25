# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 15 — Política de saída (`VERIFIED`)

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
- Last completed phase: FASE 15 — Política de saída.
- Completed acceptance criteria: Implemented sections 45-48 in
  `src/wumpus/agent/exit_policy.py` and integrated them into `Strategy`.
  The agent abandons exploration when the least-risk reachable alternative
  exceeds its gold-conditioned tolerance or has non-positive utility, returns
  safely to `[1,1]`, and deliberately executes `CLIMB` there even with no
  gold. Utility uses the configured fraction of gold remaining, the exact
  BFS-derived action count including turns/final step, score-derived hazard
  cost, and canonical arrow cost. Collecting the configured total gold
  preempts further exploration and forces return. When no safe return or
  acceptable risk step exists away from the exit, Strategy returns a
  deterministic `TURN_RIGHT`, never a knowledge-blind forward fallback.
  Scoring constants moved to `wumpus.game.scoring` so both environment and
  agent policy share one source without breaching the anti-cheat boundary.
- Remaining acceptance criteria: None for FASE 15.
- Last verified commands: `.venv/bin/python -m pytest
  tests/unit/test_exit_policy.py tests/unit/test_strategy.py
  tests/unit/test_simple_agent.py -q`; `.venv/bin/python -m pytest -q`;
  `.venv/bin/python -m compileall -q src`; `git diff --check`; real-world
  stress sweep for 100 seeds plus deterministic replay of the first 50.
- Result: targeted `49 passed`; full suite `215 passed`; compilation and
  diff checks exited 0. Final stress: 84 `ESCAPED`, 12 `DEAD`, 4
  `TURN_LIMIT`, 0 crashes; all 50 replayed outcomes were identical. Earlier
  300-seed validation of the corrected exit semantics also completed with
  255 `ESCAPED`, 28 `DEAD`, 17 `TURN_LIMIT`, 0 crashes. Independent logic
  and specification reviews both classified the final semantics
  `COMPLIANT`; their initial reviews found and the phase fixed two HIGH
  defects (continued search after all configured gold and random movement
  into rejected/confirmed danger) plus exact-route/arrow-cost evidence gaps.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `src/wumpus/agent/exit_policy.py` (new)
- `src/wumpus/agent/strategy.py`
- `src/wumpus/agent/simple_agent.py`
- `src/wumpus/agent/__init__.py`
- `src/wumpus/game/scoring.py` (new canonical scoring source)
- `src/wumpus/environment/scoring.py` (compatibility re-export)
- `src/wumpus/environment/world.py`
- `tests/unit/test_exit_policy.py` (new)
- `tests/unit/test_strategy.py`
- `tests/unit/test_simple_agent.py`
- `.specs/decisions.md`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 45: rational abandonment returns toward `[1,1]`, climbs there when
  no acceptable exploration remains, and fails closed deterministically when
  a disconnected safe route cannot yet be proven.
- Section 46: `UtilityEstimate` exposes expected remaining-gold value,
  exact planned-action cost, score-derived hazard cost, canonical arrow cost,
  and their total; `Strategy` uses the model for risk and hunting decisions.
- Sections 47-48: tolerance drops from the FASE 14 threshold before gold to
  bat-only risk after gold; increasing collected gold also reduces expected
  future value, and exhausting configured gold forces immediate return.
- Sections 57-59: the new policy consumes only configuration, canonical game
  scoring, `KnowledgeBase`, and observation-derived state. The existing AST
  boundary test covers every agent module and passes.

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
  and fail-closed for FASE 15; explicit cycle detection and loop recovery
  remain later plan work (sections 105-108).
- `AgentMemory` records only the final position observable after a bat chain;
  hidden intermediate teleport destinations are correctly unavailable to it.
- The final summary remains incomplete for sections 78 and 109: reason,
  shooting count, exploration percentage, and seed are deferred to the later
  statistics/UI/CLI work.
- Console rendering, debug map, and the CLI remain unimplemented until FASE 16
  to FASE 18; the engine exposes `on_render` and `on_render_final` hooks for them.

## Next action

Begin FASE 16 — UI by implementing the Rich console presentation required by
sections 62-68, without moving domain decisions into rendering code.

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

2026-09-25 — FASE 15 — Política de saída verified: deterministic rational
abandonment, configured remaining-gold utility, exact route/action cost,
canonical hazard/arrow costs, gold-conditioned risk tolerance, exhausted-gold
return, and fail-closed disconnected handling added under `DEC-006`.
Independent reviews initially found two HIGH semantic defects and later
classified the corrected result `COMPLIANT`. Targeted/full tests, compilation,
diff validation, and final deterministic real-map stress evidence passed.
