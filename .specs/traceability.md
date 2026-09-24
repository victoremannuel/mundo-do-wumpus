# Requirement Traceability

This file maps requirements to implementation, tests, and executable evidence.
Build it progressively as phases are implemented. Requirement wording and
identifiers must come from `.specs/plan.md`.

## Status vocabulary

- `NOT_STARTED`: no implementation or evidence yet.
- `IN_PROGRESS`: implementation or tests are incomplete.
- `BLOCKED`: progress requires an unresolved decision or external input.
- `IMPLEMENTED`: implementation exists but the complete gate has not passed.
- `VERIFIED`: implementation and required tests have passed.

## Traceability matrix

| Plan reference | Acceptance criterion | Implementation | Automated test | Evidence | Status |
|---|---|---|---|---|---|
| Section 119 — FASE 1 — Scaffold | Create `pyproject.toml`, `requirements.txt`, initial `README`, `src`, and `tests` | `pyproject.toml`; `requirements.txt`; `README.md`; `src/wumpus/__init__.py`; `tests/test_scaffold.py` | `tests/test_scaffold.py::test_required_scaffold_exists` | `.venv/bin/python -m pytest tests/test_scaffold.py -q` — 2 passed | `VERIFIED` |
| Section 119 — FASE 1 — Scaffold | `pytest` must execute | Pytest configuration in `pyproject.toml` and dependency in `requirements.txt` | `tests/test_scaffold.py::test_package_is_importable` | `.venv/bin/python -m pytest -q` — 2 passed | `VERIFIED` |
| Sections 120–121 — Checkpoint and quality | Tests must pass after the phase and `src` must compile | Importable package scaffold in `src/wumpus/__init__.py` | Full scaffold suite | `.venv/bin/python -m pytest -q` — 2 passed; `.venv/bin/python -m compileall -q src` — exit 0 | `VERIFIED` |

## Maintenance rules

- Add or update rows in the same phase that implements the requirement.
- Reference concrete file paths and test names when they exist.
- Use exact commands and outcomes in the Evidence column.
- A row cannot be `VERIFIED` when its required test is missing, skipped, or
  failing.
- Do not weaken a requirement to match the current code.
- Keep one row per independently verifiable acceptance criterion when a plan
  section contains multiple behaviors.
