"""Command-line entry point for the Wumpus World logical agent (FASE 18).

Assembles the real environment (`MapGenerator`, `World`) and the isolated
`SimpleAgent`, then drives them through the existing `GameEngine` loop.
Only this module is allowed to hold both the real `World` and the agent at
once: it passes the world to the debug renderer for display, but the agent
itself only ever receives `AgentObservation` through the engine's
observe -> decide -> act -> learn cycle (sections 69-70).
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from wumpus.agent import SimpleAgent
from wumpus.debug.renderer import DebugRenderer
from wumpus.domain import AgentObservation
from wumpus.environment import MapGenerator, World
from wumpus.game import GameConfig, GameEngine, GameOutcome, GameStatus
from wumpus.ui.console import ConsoleRenderer


DEFAULT_DELAY = 0.5


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mundo do Wumpus - agente logico autonomo"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Seed reprodutivel para o mapa"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Exibe o mapa real ao lado do mapa conhecido pelo agente",
    )
    parser.add_argument(
        "--step",
        action="store_true",
        help="Pausa apos cada acao, aguardando ENTER",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="Segundos de espera entre turnos em execucao automatica",
    )
    parser.add_argument(
        "--no-delay",
        action="store_true",
        help="Executa sem atraso entre turnos",
    )
    return parser.parse_args(argv)


def build_game(seed: int | None) -> tuple[World, SimpleAgent]:
    """Assemble one real world and one isolated agent from a single seed."""

    rng = random.Random(seed)
    config = GameConfig()
    generated_map = MapGenerator(rng, config).generate()
    world = World(generated_map, rng=rng)
    agent = SimpleAgent(rng, config)
    return world, agent


def run(argv: list[str] | None = None) -> GameOutcome:
    args = parse_args(argv)
    world, agent = build_game(args.seed)
    delay = 0.0 if args.no_delay else max(0.0, args.delay)

    turn_renderer = DebugRenderer() if args.debug else ConsoleRenderer()
    final_renderer = ConsoleRenderer()

    def on_render(observation: AgentObservation) -> None:
        reason = agent.last_reason
        steps = agent.actions_taken
        if args.debug:
            turn_renderer.render(
                world, observation, agent.memory.knowledge, reason, steps
            )
        else:
            turn_renderer.render(
                observation, agent.memory.knowledge, reason, steps
            )
        if args.step:
            input("Pressione ENTER para continuar...")
        elif delay > 0:
            time.sleep(delay)

    def on_render_final(outcome: GameOutcome) -> None:
        final_renderer.render_final(outcome)
        if outcome.status is GameStatus.ESCAPED:
            print("ESCAPOU DA CAVERNA")
        elif outcome.status is GameStatus.DEAD:
            print("AGENTE MORREU")

    engine = GameEngine(
        world,
        agent,
        on_render=on_render,
        on_render_final=on_render_final,
    )
    return engine.run()


if __name__ == "__main__":
    run()
