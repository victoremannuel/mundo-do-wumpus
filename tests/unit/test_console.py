import ast
import io
from pathlib import Path

from rich.console import Console

from wumpus.agent import DecisionReason, KnowledgeBase
from wumpus.domain import Action, AgentObservation, Direction, EntityType, Perception, Position
from wumpus.game.engine import GameOutcome, GameStatus
from wumpus.ui import ConsoleRenderer


def make_observation(
    *,
    position: Position = Position(1, 1),
    direction: Direction = Direction.NORTH,
    perception: Perception | None = None,
    score: int = 0,
    collected_gold: int = 0,
) -> AgentObservation:
    return AgentObservation(
        position=position,
        direction=direction,
        perception=perception
        or Perception(
            stench=False, breeze=False, bat_noise=False, glitter=False, bump=False, scream=False
        ),
        score=score,
        collected_gold=collected_gold,
        active=True,
    )


def render_to_text(renderer_call) -> str:
    buffer = io.StringIO()
    console = Console(file=buffer, width=100, color_system=None)
    renderer_call(console)
    return buffer.getvalue()


def test_render_known_map_shows_the_agent_glyph_at_its_position() -> None:
    knowledge = KnowledgeBase(2, 2)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(make_observation(), knowledge)
    )

    assert "A↑" in output
    assert "MAPA CONHECIDO PELO AGENTE" in output


def test_render_marks_confirmed_hazards_with_their_symbols() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_confirmed(Position(3, 3), EntityType.WUMPUS)
    knowledge.mark_confirmed(Position(2, 2), EntityType.PIT)
    knowledge.mark_possible(Position(1, 2), EntityType.BAT)

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(make_observation(), knowledge)
    )

    assert "W" in output
    assert "P" in output
    assert "!" in output


def test_render_perceptions_panel_shows_every_sensed_value() -> None:
    observation = make_observation(
        perception=Perception(
            stench=True, breeze=False, bat_noise=True, glitter=False, bump=False, scream=False
        )
    )
    knowledge = KnowledgeBase(2, 2)

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(observation, knowledge)
    )

    assert "Fedor" in output and "SIM" in output
    assert "Morcego" in output


def test_render_agent_panel_shows_position_gold_score_and_steps() -> None:
    observation = make_observation(position=Position(3, 2), score=934, collected_gold=1)
    knowledge = KnowledgeBase(3, 3)

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(observation, knowledge, steps=57)
    )

    assert "[3,2]" in output
    assert "934" in output
    assert "57" in output


def test_render_reasoning_panel_shows_the_decision_and_its_target() -> None:
    observation = make_observation()
    knowledge = KnowledgeBase(3, 3)
    reason = DecisionReason(Action.MOVE_FORWARD, "Safe unexplored frontier", Position(4, 2))

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(observation, knowledge, reason)
    )

    assert "Safe unexplored frontier" in output
    assert "[4,2]" in output
    assert "MOVE_FORWARD" in output


def test_render_reasoning_panel_handles_no_recorded_decision() -> None:
    observation = make_observation()
    knowledge = KnowledgeBase(3, 3)

    output = render_to_text(
        lambda console: ConsoleRenderer(console).render(observation, knowledge, None)
    )

    assert "Nenhuma decisão registrada ainda." in output


def test_ui_package_never_imports_the_environment_or_hidden_map_types() -> None:
    ui_package = Path(__file__).parents[2] / "src" / "wumpus" / "ui"
    forbidden_names = {"World", "GeneratedMap", "grid", "entities"}

    for module_path in ui_package.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    not alias.name.startswith("wumpus.environment") for alias in node.names
                )
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("wumpus.environment")
                assert not (
                    node.module == "wumpus"
                    and any(alias.name == "environment" for alias in node.names)
                )
            if isinstance(node, ast.Name):
                assert node.id not in forbidden_names
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names


def test_render_final_shows_the_outcome_summary() -> None:
    outcome = GameOutcome(
        status=GameStatus.ESCAPED,
        score=934,
        collected_gold=2,
        killed_wumpus=1,
        turns=57,
        visited_cells=10,
    )

    output = render_to_text(lambda console: ConsoleRenderer(console).render_final(outcome))

    assert "ESCAPED" in output
    assert "934" in output
    assert "RESULTADO FINAL" in output
