# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 5 — Flecha (`NOT_STARTED`)

## Phase ledger

Populate this table from the phase headings in `.specs/plan.md`. Do not invent,
rename, merge, or reorder phases.

| Phase | Status | Verified evidence |
|---|---|---|
| FASE 1 — Scaffold | `VERIFIED` | `2 passed`; `compileall` passed; specification audit `COMPLIANT`. |
| FASE 2 — Domínio | `VERIFIED` | `13 passed` targeted; `15 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 3 — Gerador | `VERIFIED` | `28 passed` targeted; `43 passed` full; 100-seed audit passed; audit `COMPLIANT`. |
| FASE 4 — Ambiente | `VERIFIED` | `26 passed` targeted; `69 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 5 — Flecha | `NOT_STARTED` | — |
| FASE 6 — Morcegos | `NOT_STARTED` | — |
| FASE 7 — Engine | `NOT_STARTED` | — |
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
- Last completed phase: FASE 4 — Ambiente.
- Completed acceptance criteria: Implemented and tested private `World` state,
  sensors, movement, rotations, walls, gold collection, lethal hazards, exit,
  invalid-exit event, action results, and centralized scoring.
- Remaining acceptance criteria: None for FASE 4.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_world.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`.
- Result: Targeted tests `26 passed`; full suite `69 passed`; compilation exit
  0; verification `PASS`; specification compliance `COMPLIANT`. The first
  compliance review found missing invalid-`CLIMB` event recording; it was
  implemented and all affected gates were rerun successfully.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: The harness and canonical specification files were
  pre-existing ignored files. Only the two required state files are included
  from that ignored set; no unrelated harness files are checkpointed.

## Files changed in current phase

- `src/wumpus/environment/__init__.py`
- `src/wumpus/environment/actions.py`
- `src/wumpus/environment/scoring.py`
- `src/wumpus/environment/sensors.py`
- `src/wumpus/environment/world.py`
- `tests/unit/test_world.py`
- `.specs/decisions.md`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Sections 5 and 30: `World` starts at `[1,1]`, facing North, while keeping map
  collections private.
- Sections 13–18 and 81–86: sensors, movement, rotations, walls, and transient
  bump behavior have passing directional and diagonal coverage.
- Sections 11–12 and 89–91: scoring has one source of truth; gold collection
  and lethal hazards update state and score correctly.
- Sections 26–27 and 102: climbing exits only at `[1,1]` and invalid attempts
  are charged and recorded.
- Sections 61 and 119, FASE 4: supported actions return consistent
  `ActionResult` values and all environment tests pass.

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- `SHOOT` deliberately raises `NotImplementedError` until FASE 5.
- Bat cells are sensed and enterable but do not teleport until FASE 6.
- DEC-001 resolves the death scoring ambiguity as `-1` movement plus `-1000`
  death penalty (`-1001` total action delta).

## Next action

Begin FASE 5 — Flecha by extracting its exact contract and implementing only
straight-line shooting, first-live-Wumpus hits, unlimited arrows, scream
transience, stench updates, and exact `-10` scoring with tests.

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

2026-09-24 — FASE 4 — Ambiente verified after focused tests, full regression,
source compilation, architecture verification, resolved compliance finding,
and final specification compliance.
