# Implementation Status

This file records execution state only. Requirements remain in
`.specs/plan.md`.

## Overall status

`IN_PROGRESS`

Allowed values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IMPLEMENTED`,
`VERIFIED`.

## Current phase

FASE 3 — Gerador (`NOT_STARTED`)

## Phase ledger

Populate this table from the phase headings in `.specs/plan.md`. Do not invent,
rename, merge, or reorder phases.

| Phase | Status | Verified evidence |
|---|---|---|
| FASE 1 — Scaffold | `VERIFIED` | `2 passed`; `compileall` passed; specification audit `COMPLIANT`. |
| FASE 2 — Domínio | `VERIFIED` | `13 passed` targeted; `15 passed` full; `compileall` passed; audit `COMPLIANT`. |
| FASE 3 — Gerador | `NOT_STARTED` | — |
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
- Last completed phase: FASE 2 — Domínio.
- Completed acceptance criteria: Implemented and tested `Position`,
  `Direction`, `Action`, `EntityType`, `Perception`, `ActionResult`, and
  `GameConfig`, without AI behavior.
- Remaining acceptance criteria: None for FASE 2.
- Last verified commands: `.venv/bin/python -m pytest tests/unit/test_domain.py -q`;
  `.venv/bin/python -m pytest -q`; `.venv/bin/python -m compileall -q src`.
- Result: Targeted tests `13 passed`; full suite `15 passed`; compilation exit
  0; verification `PASS`; specification compliance `COMPLIANT`.
- Expected post-checkpoint worktree: Clean for task-owned files.
- Working tree notes: The harness and canonical specification files were
  pre-existing ignored files. Only the two required state files are included
  from that ignored set; no unrelated harness files are checkpointed.

## Files changed in current phase

- `src/wumpus/domain/__init__.py`
- `src/wumpus/domain/coordinate.py`
- `src/wumpus/domain/enums.py`
- `src/wumpus/domain/models.py`
- `src/wumpus/domain/perception.py`
- `src/wumpus/game/__init__.py`
- `src/wumpus/game/config.py`
- `tests/unit/test_domain.py`
- `.specs/implementation-status.md`
- `.specs/traceability.md`

## Requirements satisfied in current phase

- Section 9: `Direction`, `Action`, and `EntityType` contain the exact required
  members.
- Section 13: `Perception` is immutable and contains all six signals.
- Section 29: `Position` is immutable, ordered, one-based, and supplies the
  coordinate helpers described by the plan.
- Section 61: `ActionResult` contains the required state and false event
  defaults.
- Section 74: `GameConfig` centralizes the canonical dimensions and counts.
- Section 119, FASE 2: all seven types exist without AI logic and tests pass.

## Current blockers

- None.

## Known limitations and technical debt

- Ruff is not configured or installed, and its use is optional in section 121.
- `CellRisk` is an optional suggestion in section 9 and is not one of the seven
  required FASE 2 types; introduce it only if the Risk engine needs it.
- Configuration/map invariant validation belongs to FASE 3; environment,
  scoring, and AI behavior remain intentionally absent.

## Next action

Begin FASE 3 — Gerador by extracting its exact contract and implementing only
the 6x6 seeded map generation, entity counts, safe-zone/no-overlap constraints,
and invariant tests.

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

2026-09-24 — FASE 2 — Domínio verified after targeted tests, full regression,
source compilation, architecture verification, and specification compliance.
