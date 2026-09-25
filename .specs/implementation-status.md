# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 21 — README final (`VERIFIED`)

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
| FASE 21 — README final | `VERIFIED` | `2 passed` README contract tests; full regression `291 passed` (run in three bounded groups); `compileall` passed; specification audit `COMPLIANT`. |

## Current checkpoint

- Checkpoint type: `VERIFIED`.
- Checkpoint commit: Not recorded. When committed, resolve the authoritative
  hash with `git log -1 --format=%H` rather than attempting to store a commit's
  own hash inside itself.
- Last completed phase: FASE 21 — README final.
- Completed acceptance criteria: README documents the academic objective, game
  rules, architecture and anti-cheat boundary, inference/strategy, map
  generation, PEAS, execution and debug modes, tests, reproducible examples,
  limitations, and source layout. It reflects the current persistent Textual
  interface and retains the legacy console invocation.
- Remaining acceptance criteria: None.
- Last verified commands: `.venv/bin/python -m pytest tests/test_readme.py -q`;
  regression split into 220 non-TUI unit tests, 50 scaffold/console/debug/CLI/
  integration/E2E tests, and 21 TUI tests; `.venv/bin/python -m compileall -q
  src main.py`; `git diff --check`.
- Result: targeted `2 passed`; complete regression `291 passed` with zero
  failures (220 + 50 + 21); compilation exited 0; diff check clean. Ruff
  remains unconfigured/not installed. Documentation/specification audit was
  `COMPLIANT` for FASE 21, with no unresolved documentation finding.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: `__pycache__` directories remain untracked and are never
  staged. The canonical specification files stay in the ignored `.specs`
  directory; only required state files are checkpointed from it.

## Files changed in current phase

- `README.md`
- `tests/test_readme.py` (new)
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Sections 110–118 and 119 FASE 21: final documentation covers every listed
  README topic and accurately classifies the agent/environment.
- Sections 72–73 and 114: documented execution modes, debug isolation, and
  fixed-seed reproducibility match `main.py` and the current TUI.
- Sections 120–121: README contract tests, full regression, compilation, and
  diff check passed.

## Current blockers

- Final-project audit is `BLOCKERS`: plan sections 106–108 still lack explicit
  cycle detection, a knowledge-revision-driven replanning trigger, and
  temporary objective blacklisting; section 109's exploration-rate metric and
  section 78's complete final summary are also absent. All numbered phases,
  including FASE 21, are verified, but the project Definition of Done cannot
  be claimed until these plan requirements have executable evidence.

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

Resolve the final-audit blockers for sections 78 and 106–109 with explicit
scope authorization (they are not a numbered phase), then add traceability and
repeat the final audit. Do not declare the repository release-ready yet.

## Post-FASE-20 maintenance

### UI-RETRO-TUI-001 — Persistent retro pixel-art interface

Status: `VERIFIED`. This is presentation-layer maintenance, not a plan phase. It
does not start, advance, or complete FASE 21, and it changes no phase status.

Base commit: `bdff853ac7a9b417e0efda1f536ff82424423fd5` (FASE 20 — E2E
`VERIFIED`).

Summary: replaced the scrolling turn-by-turn console experience with a
persistent Textual interface. The widget tree mounts once and every turn only
calls `widget.update(...)`, so the terminal shows one fixed screen instead of a
new frame printed under the previous one. The map is drawn as 5x-scale
pixel-art tiles (`TILE_HEIGHT = 5`, `TILE_WIDTH = 10`, one 70x38 board for a
6x6 world) with the agent's facing direction visible as a distinct sprite per
`Direction`. Interactive controls cover pause, single step, debug, speed, and
quit. The game itself is untouched: no file under `src/wumpus/agent`,
`src/wumpus/environment`, `src/wumpus/domain`, or `src/wumpus/game` was
modified.

Architecture:

- `src/wumpus/ui/retro_tiles.py`: tile geometry, sprites, and tile styles.
- `src/wumpus/ui/retro_state.py`: `MapView`, `TurnSnapshot`, knowledge-to-tile
  classification, and the speed-interval table.
- `src/wumpus/ui/retro_map.py`: board rendering with coordinates and borders.
- `src/wumpus/ui/retro_panels.py`: header, HUD, sensors, decision, legend,
  footer, summary, failure, and minimum-size renderables.
- `src/wumpus/ui/retro_app.py`: `RetroGameApp`, its widgets, CSS, timer, and
  controls. It calls `GameEngine.step()` and never reimplements the loop.
- `src/wumpus/debug/retro_renderer.py`: the only place that converts a
  `DebugWorldSnapshot` into an inert `MapView`.
- `main.py`: composition root. `run()` is unchanged and still headless;
  `run_tui()` launches the interface; `main()` dispatches on
  `--legacy-console`.

Boundary: `wumpus.ui` imports neither `wumpus.environment` nor `wumpus.debug`.
The real map reaches the screen only as a pre-classified `MapView` injected by
`main.py` from the authorized debug adapter, so debug mode is observation only
and cannot influence a decision. The existing anti-cheat and debug-boundary
tests were not weakened and still pass.

Determinism: no module under `wumpus.ui` touches a random source, asserted by
`tests/unit/test_retro_app.py::test_the_interface_module_never_touches_a_random_source`.
Playing a seed through the interface produces exactly the outcome a bare
`GameEngine` produces, with debug on or off, and pausing or changing speed does
not alter it.

Tests: `tests/unit/test_retro_tiles.py` (13) and
`tests/unit/test_retro_app.py` (21, driven through `App.run_test` and `Pilot`
without an async pytest plugin); `tests/unit/test_cli.py` extended with three
cases for `--legacy-console`, the default front end, and speed-index safety.

Commands and results:

- `.venv/bin/python -m pytest tests/unit/test_retro_tiles.py
  tests/unit/test_retro_app.py tests/unit/test_cli.py tests/unit/test_console.py
  tests/unit/test_debug_renderer.py -q` — 57 passed.
- `.venv/bin/python -m pytest tests/e2e/test_seeded_games.py -q` — 10 passed.
- `.venv/bin/python -m pytest -q` — 289 passed (252 pre-existing plus 37 new).
- `.venv/bin/python -m compileall -q src main.py` — exit 0.
- `git diff --check` — clean.
- Manual smoke over a real pty at 140x46 for `--seed 42`, `--seed 42 --step`,
  `--seed 42 --debug`, `--seed 42 --no-delay`, and at 95x31: the alternate
  screen buffer is used in every run, the title is repainted 3 times across a
  whole 64-turn game instead of once per turn, no traceback appears, `--step`
  opens paused, `--debug` reaches the real map, `--no-delay` completes the game
  and shows the summary, and 95x31 shows the minimum-size notice.
- `.venv/bin/python main.py --seed 42 --legacy-console --no-delay` — unchanged
  legacy output, `ESCAPED`, score 936, 64 turns.

Documented deviations from the maintenance brief:

- Side-by-side boards start at `DUAL_MAP_MIN_WIDTH = 176` as requested, but the
  HUD can only be preserved alongside them from
  `DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH = 190` (two 72-column panels plus a
  46-column sidebar). Between 176 and 189 columns both boards are shown at full
  tile scale and the sidebar is hidden rather than squashing the tiles; the HUD
  is always restored once the game ends.
- The final summary is a fixed `RESULTADO` panel in the sidebar rather than a
  floating centered box. A full-screen Textual overlay layer occludes the layer
  beneath it even when transparent, which would have hidden the final board;
  the panel keeps both the board and the summary visible.
- Arrow glyphs (`▲ ▶ ▼ ◀`) are not used inside tiles. They have ambiguous East
  Asian width and would misalign the board, so the agent sprites are built from
  block characters, as the brief's own fallback clause allows.

Not addressed on purpose (pre-existing, unrelated technical debt): cycle
detection, objective blacklisting, knowledge-revision redesign, shooting
statistics, and the final summary statistics of plan sections 78 and 105-109.

Next canonical action: FASE 21 — README final.

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

2026-09-25 — FASE 21 — README final verified: replaced the scaffold README
with plan-required academic, rules, architecture, algorithm, knowledge,
inference, strategy, generation, PEAS, execution, debug, test, example, and
limitation documentation. Added two contract tests. Targeted `2 passed`; full
regression `291 passed` (220 + 50 + 21 in bounded groups); compilation and
`git diff --check` passed; specification audit `COMPLIANT`.

2026-09-25 — Final-project audit: `BLOCKERS`. Full suite `291 passed`,
compilation, deterministic legacy release/debug seed-42 smoke runs, and the
prior 100-seed stress evidence passed; however, sections 78 and 106–109 are
still unimplemented and have no traceability evidence. This does not reopen
FASE 21, but prevents an overall Definition-of-Done claim.

2026-09-25 — UI-RETRO-TUI-001 (post-FASE-20 maintenance): added the persistent
retro Textual interface as the default front end while keeping `run()` headless
and `--legacy-console` available. Full suite `289 passed` (252 pre-existing plus
37 new), compilation passed, E2E `10 passed`, `git diff --check` clean, and five
real-pty smoke runs confirmed a single fixed screen. No phase status changed;
FASE 20 stays `VERIFIED` and FASE 21 stays `NOT_STARTED`.

2026-09-25 — FASE 20 — E2E verified: added ten deterministic fixed-seed
runs over the complete production game, each replayed to prove identical final
outcomes. Targeted `10 passed`, affected `14 passed`, full `252 passed`,
compilation passed, and a separate 100-seed stress run completed without
exceptions. Independent specification/test audits were `COMPLIANT`/`PASS`.
