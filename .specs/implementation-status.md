# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 18 — CLI (`VERIFIED`)

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
| FASE 19 — Integration tests | `NOT_STARTED` | — |
| FASE 20 — E2E | `NOT_STARTED` | — |
| FASE 21 — README final | `NOT_STARTED` | — |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 18 — CLI.
- Completed acceptance criteria: Added `main.py` as the composition root that
  builds one `random.Random(seed)`, a `MapGenerator`-produced `World`, and a
  `SimpleAgent`, then drives them through the unchanged `GameEngine` loop.
  Wired all five plan-defined flags: `--seed` (reproducible generation),
  `--debug` (routes turn rendering through `DebugRenderer`, which is the only
  place the real `World` is forwarded, matching the already-VERIFIED FASE 17
  boundary), `--step` (blocks on `input()` once per turn), `--delay` (default
  0.5s `time.sleep` between automatic turns), and `--no-delay` (forces zero
  delay). Final outcome always renders via `ConsoleRenderer.render_final` and
  prints `ESCAPOU DA CAVERNA` / `AGENTE MORREU` per section 142. Inserted the
  repository's `src/` onto `sys.path` at the top of `main.py` so
  `python main.py ...` runs without a separate install step, matching section
  142's `pip install -r requirements.txt` + `python main.py` expectation.
- Remaining acceptance criteria: None for FASE 18.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_cli.py
  -q`; `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src
  main.py`; `python main.py --seed 42 --no-delay` run twice compared byte-for-
  byte for the final summary; `python main.py --seed 5 --no-delay --debug`
  (confirmed `MAPA REAL` panels render); `yes "" | python main.py --seed 5
  --step` (confirmed one prompt per turn); `git diff --check`.
- Result: targeted `7 passed`; full suite `240 passed` (up from 233);
  compilation exited 0; two same-seed runs produced identical final score/
  turns/status; `--debug` and `--step` manual smoke checks behaved as
  specified. Ruff was not installed/configured. Specification compliance
  review was `COMPLIANT` with no BLOCKER/HIGH/MEDIUM findings (one LOW
  informational note about `SimpleAgent`'s unused `rng` constructor parameter,
  pre-existing from earlier phases and not a FASE 18 defect).
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `main.py` (new)
- `tests/unit/test_cli.py` (new)
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 8: map generation uses an injected `random.Random(seed)`, never the
  global `random` module, so `--seed` reproduces a map deterministically.
- Sections 69, 72: `--debug` shows `MAPA CONHECIDO PELO AGENTE` and `MAPA
  REAL` together for every turn; the default mode shows only the known map.
- Section 70: the real `World` is forwarded only to the FASE 17
  `DebugRenderer`, never to `SimpleAgent`, `GameEngine`, or the normal
  `ConsoleRenderer`.
- Sections 72-73: `--delay`/`--no-delay` control the pause between automatic
  turns; `--step` blocks on `ENTER` after each turn's render instead.
- Section 142: the program is runnable as `python main.py --seed 42 --step`
  and prints `ESCAPOU DA CAVERNA` or `AGENTE MORREU` on the corresponding
  terminal outcome.

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

## Next action

Begin FASE 19 — Integration tests: run the real, unmodified `SimpleAgent`
against known/generated maps through `GameEngine` to validate end-to-end
behavior beyond the existing unit-level stress sweeps.

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

2026-09-25 — FASE 18 — CLI verified: added `main.py` wiring `--seed`,
`--debug`, `--step`, `--delay`, and `--no-delay` over the unchanged
`GameEngine`/`SimpleAgent`/`World` components, preserving the agent/
environment boundary (the real `World` reaches only `DebugRenderer`).
Targeted `7 passed`, full `240 passed`, compilation and deterministic-seed
smoke checks passed, and specification audit was `COMPLIANT`.
