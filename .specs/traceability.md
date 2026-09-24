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
| Section 9 — Enums do domínio | `Direction`, `Action`, and `EntityType` expose the plan-defined members | `src/wumpus/domain/enums.py` | `tests/unit/test_domain.py::test_domain_enums_have_the_plan_defined_members` | `.venv/bin/python -m pytest tests/unit/test_domain.py -q` — 13 passed | `VERIFIED` |
| Section 13 — Percepções do agente | `Perception` is immutable and carries the six plan-defined signals | `src/wumpus/domain/perception.py` | `tests/unit/test_domain.py::test_perception_has_exactly_six_immutable_signals` | `.venv/bin/python -m pytest tests/unit/test_domain.py -q` — 13 passed | `VERIFIED` |
| Section 29 — Modelagem de coordenadas | `Position` is immutable, ordered, one-based, and supports neighbors, bounds, and Manhattan distance | `src/wumpus/domain/coordinate.py` | `tests/unit/test_domain.py::test_position_is_an_immutable_ordered_value_object`; `test_position_exposes_orthogonal_neighbors`; `test_position_uses_one_based_world_bounds`; `test_position_calculates_manhattan_distance` | `.venv/bin/python -m pytest tests/unit/test_domain.py -q` — 13 passed | `VERIFIED` |
| Section 61 — Action Result | `ActionResult` records action state and defaults all event flags to false | `src/wumpus/domain/models.py` | `tests/unit/test_domain.py::test_action_result_records_outcome_with_false_event_defaults` | `.venv/bin/python -m pytest tests/unit/test_domain.py -q` — 13 passed | `VERIFIED` |
| Section 74 — Configuração central | `GameConfig` provides the canonical 6x6 and entity-count defaults | `src/wumpus/game/config.py` | `tests/unit/test_domain.py::test_game_config_uses_canonical_defaults_and_remains_configurable` | `.venv/bin/python -m pytest tests/unit/test_domain.py -q` — 13 passed | `VERIFIED` |
| Section 119 — FASE 2 — Domínio | Implement the seven domain types without AI logic and keep the phase test suite green | `src/wumpus/domain/`; `src/wumpus/game/config.py` | `tests/unit/test_domain.py` | `.venv/bin/python -m pytest -q` — 15 passed; `.venv/bin/python -m compileall -q src` — exit 0 | `VERIFIED` |

## Maintenance rules

- Add or update rows in the same phase that implements the requirement.
- Reference concrete file paths and test names when they exist.
- Use exact commands and outcomes in the Evidence column.
- A row cannot be `VERIFIED` when its required test is missing, skipped, or
  failing.
- Do not weaken a requirement to match the current code.
- Keep one row per independently verifiable acceptance criterion when a plan
  section contains multiple behaviors.
