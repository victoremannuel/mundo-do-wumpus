"""Command-line entry point for the Wumpus World logical agent (FASE 18).

Assembles the real environment (`MapGenerator`, `World`) and the isolated
`SimpleAgent`, then drives them through the existing `GameEngine` loop.
Only this module is allowed to hold both the real `World` and the agent at
once: it passes the world to the debug renderer for display, but the agent
itself only ever receives `AgentObservation` through the engine's
observe -> decide -> act -> learn cycle (sections 69-70).

Two front ends share that assembly. `main()` launches the persistent retro
Textual interface by default; `run()` keeps the original headless, scrolling
console flow so tests, stress runs, and `--legacy-console` never need an
interactive terminal.
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

from wumpus.agent import HumanAgent, SimpleAgent
from wumpus.debug.renderer import DebugRenderer
from wumpus.domain import AgentObservation
from wumpus.environment import MapGenerator, World, layout_signature
from wumpus.game import (
    GameConfig,
    GameEngine,
    GameObjective,
    GameOutcome,
    GameStatus,
    resolve_effective_seed,
    seed_for_restart,
)
from wumpus.ui.console import ConsoleRenderer
from wumpus.ui.retro_state import (
    DEFAULT_INTERVAL,
    MAX_SPEED_INDEX,
    SPEED_INTERVALS,
)


DEFAULT_DELAY = DEFAULT_INTERVAL


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
    parser.add_argument(
        "--legacy-console",
        action="store_true",
        help="Usa o renderer de console original em vez da interface retro",
    )
    return parser.parse_args(argv)


def build_game(
    seed: int | None,
    config: GameConfig | None = None,
    objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
) -> tuple[World, SimpleAgent]:
    """Assemble one real world and one isolated agent from a single seed."""

    effective_seed = resolve_effective_seed(seed)
    rng = random.Random(effective_seed)
    game_config = config if config is not None else GameConfig()
    generated_map = MapGenerator(rng, game_config, objective=objective).generate()
    world = World(generated_map, rng=rng, objective=objective)
    agent = SimpleAgent(rng, game_config, objective=objective)
    return world, agent


def build_session(settings: object) -> object:
    """Assemble a TUI session without exposing the real world to `wumpus.ui`."""

    from wumpus.debug.retro_renderer import build_real_map_view
    from wumpus.ui.retro_session import GameMode, GameSession, SessionSettings

    if not isinstance(settings, SessionSettings):
        raise TypeError("settings must be SessionSettings")
    effective_settings = settings
    config = effective_settings.config
    game_seed = seed_for_restart(
        effective_settings.seed, effective_settings.restart_index
    )
    rng = random.Random(game_seed)
    generated_map = MapGenerator(
        rng,
        config,
        objective=effective_settings.objective,
        previous_layout=effective_settings.previous_layout,
    ).generate()
    world = World(generated_map, rng=rng, objective=effective_settings.objective)

    if effective_settings.mode is GameMode.MANUAL:
        agent = HumanAgent(config)
        submitter = agent.queue_action
        clearer = agent.clear_pending_action
    else:
        agent = SimpleAgent(rng, config, objective=effective_settings.objective)
        submitter = None
        clearer = None

    return GameSession(
        engine=GameEngine(world, agent),
        presentation_source=agent,
        initial_observation=world.observation(),
        mode=effective_settings.mode,
        settings=effective_settings,
        next_settings=SessionSettings(
            mode=effective_settings.mode,
            seed=effective_settings.seed,
            game_config=effective_settings.game_config,
            objective=effective_settings.objective,
            restart_index=effective_settings.restart_index + 1,
            previous_layout=layout_signature(generated_map),
        ),
        debug_map_source=lambda: build_real_map_view(world.debug_snapshot()),
        manual_action_submitter=submitter,
        manual_action_clearer=clearer,
    )


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
        elif outcome.status is GameStatus.ABANDONED:
            print("AGENTE INTERROMPEU A EXPLORAÇÃO SEM ROTA RACIONAL")

    engine = GameEngine(
        world,
        agent,
        on_render=on_render,
        on_render_final=on_render_final,
    )
    return engine.run()


def speed_index_for(delay: float, *, no_delay: bool) -> int:
    """Map a requested delay onto the interface's discrete speed steps.

    A Textual timer must never be given a zero interval: that starves the event
    loop and the keyboard stops responding. `--no-delay` therefore selects the
    fastest safe interval instead of no interval at all.
    """

    if no_delay:
        return MAX_SPEED_INDEX
    return min(
        range(len(SPEED_INTERVALS)),
        key=lambda index: abs(SPEED_INTERVALS[index] - delay),
    )


def run_tui(args: argparse.Namespace) -> GameOutcome | None:
    """Run one game inside the persistent retro interface.

    The world is assembled here, in the composition root, and only ever exposed
    to the interface as agent-legal data: the first `AgentObservation` and, for
    professor mode, an inert real-map view produced by the authorized debug
    adapter. Reading that first observation before the engine exists is safe
    because the transient bump/scream signals it consumes are still unset, so
    the agent's own first observation is unchanged and the seed stays
    reproducible.
    """

    from wumpus.ui.retro_app import RetroGameApp

    app = RetroGameApp(
        session_factory=build_session,
        seed=args.seed,
        speed_index=speed_index_for(args.delay, no_delay=args.no_delay),
        start_paused=args.step,
        debug_enabled=args.debug,
    )
    return app.run()


def main(argv: list[str] | None = None) -> GameOutcome | None:
    """Dispatch between the retro interface and the legacy console flow."""

    args = parse_args(argv)
    if args.legacy_console:
        return run(argv)
    return run_tui(args)


if __name__ == "__main__":
    main()
