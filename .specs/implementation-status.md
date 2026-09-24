# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 4 — Ambiente (`NOT_STARTED`)

## Phase ledger

Populate this table from the phase headings in `.specs/plan.md`. Do not invent,
rename, merge, or reorder phases.

| Phase | Status | Verified evidence |
|---|---|---|
| FASE 1 — Scaffold | `VERIFIED` | `2 passed`; `compileall` passed; specification audit `COMPLIANT`. |
| FASE 2 — Domínio | `VERIFIED` | `13 passed` targeted; `15 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 3 — Gerador | `VERIFIED` | `28 passed` targeted; `43 passed` full; 100-seed audit passed; audit `COMPLIANT`. |
| FASE 4 — Ambiente | `NOT_STARTED` | — |
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
- Last completed phase: FASE 3 — Gerador.
- Completed acceptance criteria: Implemented and tested canonical and
  configurable map dimensions, exact entity counts, unique placements, empty
  initial safe zone, injected seeded RNG, and post-generation validation.
- Remaining acceptance criteria: None for FASE 3.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_generator.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`;
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c <100-seed invariant audit>`.
- Result: Targeted tests `28 passed`; full suite `43 passed`; compilation exit
  0; 100-seed audit exit 0; verification `PASS`; specification compliance
  `COMPLIANT`. The first auxiliary audit invocation exited 1 because direct
  Python lacked pytest's configured `src` path; rerunning with `PYTHONPATH=src`
  passed without a code change.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: The harness and canonical specification files were
  pre-existing ignored files. Only the two required state files are included
  from that ignored set; no unrelated harness files are checkpointed.

## Files changed in current phase

- `src/wumpus/environment/__init__.py`
- `src/wumpus/environment/generator.py`
- `tests/unit/test_generator.py`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Sections 4 and 74: canonical generation produces a 6x6 map.
- Sections 6–7: the initial safe cells are empty and exactly 11 entities occupy
  distinct cells with canonical type counts.
- Sections 8, 125, and 126: generation uses only an injected `random.Random`
  and fixed seeds reproduce identical maps.
- Sections 75–76: every generated map is validated once without solvability
  filtering or regeneration loops.
- Sections 80 and 119, FASE 3: all required generator invariants have passing
  automated coverage.

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- Solvability is intentionally not guaranteed, as required by section 76.
- `World`, mechanics, sensors, scoring, and AI behavior remain outside FASE 3.

## Next action

Begin FASE 4 — Ambiente by extracting its exact contract and implementing only
`World`, perceptions, movement, rotations, gold, death, walls, exit, and
centralized scoring with tests.

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

2026-09-24 — FASE 3 — Gerador verified after focused tests, full regression,
source compilation, 100-seed invariant audit, architecture verification, and
specification compliance.
