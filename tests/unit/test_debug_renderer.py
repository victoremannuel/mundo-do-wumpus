import ast
import io
import random
from pathlib import Path

import pytest
from rich.console import Console

from wumpus.agent import KnowledgeBase
from wumpus.debug import DebugRenderer, render_real_map
from wumpus.domain import Action, EntityType, Position
from wumpus.environment.generator import GeneratedMap
from wumpus.environment.world import World


def make_world(entities: dict[Position, EntityType] | None = None) -> World:
    return World(
        GeneratedMap(rows=3, cols=3, entities=entities or {}),
        rng=random.Random(7),
    )


def render_to_text(renderable) -> str:
    buffer = io.StringIO()
    Console(file=buffer, width=100, color_system=None).print(renderable)
    return buffer.getvalue()


def test_real_map_renders_every_current_entity_and_agent_orientation() -> None:
    world = make_world(
        {
            Position(3, 1): EntityType.WUMPUS,
            Position(3, 2): EntityType.PIT,
            Position(2, 2): EntityType.GOLD,
            Position(2, 3): EntityType.BAT,
        }
    )

    output = render_to_text(render_real_map(world.debug_snapshot()))

    assert "MAPA REAL" in output
    assert "W" in output
    assert "P" in output
    assert "G" in output
    assert "B" in output
    assert "A↑" in output
    assert "." in output


def test_debug_renderer_shows_known_and_real_maps_in_the_same_turn() -> None:
    world = make_world({Position(3, 3): EntityType.WUMPUS})
    observation = world.observation()
    knowledge = KnowledgeBase(3, 3)
    buffer = io.StringIO()
    console = Console(file=buffer, width=100, color_system=None)

    DebugRenderer(console).render(world, observation, knowledge)

    output = buffer.getvalue()
    assert "MAPA CONHECIDO PELO AGENTE" in output
    assert "MAPA REAL" in output


def test_debug_snapshot_tracks_world_changes_without_mutable_aliases() -> None:
    gold_position = Position(1, 1)
    world = make_world({gold_position: EntityType.GOLD})
    before = world.debug_snapshot()

    result = world.execute(Action.GRAB)
    after = world.debug_snapshot()

    assert result.gold_collected
    assert before.entity_at(gold_position) is EntityType.GOLD
    assert after.entity_at(gold_position) is EntityType.EMPTY
    with pytest.raises(TypeError):
        before.entities[Position(2, 2)] = EntityType.PIT  # type: ignore[index]


def test_hidden_state_import_is_confined_to_the_explicit_debug_package() -> None:
    source_root = Path(__file__).parents[2] / "src" / "wumpus"

    for package_name in ("agent", "game", "ui"):
        for module_path in (source_root / package_name).glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported_names = {alias.name for alias in node.names}
                    assert "DebugWorldSnapshot" not in imported_names
                    assert "DebugRenderer" not in imported_names
                    assert not (node.module or "").startswith("wumpus.debug")
                if isinstance(node, ast.Import):
                    assert all(
                        not alias.name.startswith("wumpus.debug")
                        for alias in node.names
                    )


def test_debug_snapshot_rejects_out_of_bounds_queries() -> None:
    snapshot = make_world().debug_snapshot()

    with pytest.raises(ValueError, match="outside debug snapshot"):
        snapshot.entity_at(Position(4, 1))
