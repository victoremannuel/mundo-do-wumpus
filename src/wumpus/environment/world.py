"""Private real-world state and deterministic environment mechanics."""

import random
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    EntityType,
    Perception,
    Position,
)
from wumpus.environment.actions import forward_position, rotated
from wumpus.environment.arrows import line_of_fire
from wumpus.environment.bats import (
    BAT_CHAIN_LIMIT_EVENT,
    MAX_BAT_TELEPORT_CHAIN,
    choose_teleport_destination,
)
from wumpus.environment.generator import GeneratedMap
from wumpus.environment.sensors import sense
from wumpus.game.config import START_DIRECTION, START_POSITION, exit_position_for
from wumpus.game.objective import GameObjective
from wumpus.game.scoring import DEATH_PENALTY, GOLD_REWARD, action_cost


INVALID_CLIMB_EVENT = "A saída é automática somente na célula final."
EXIT_BLOCKED_EVENT = "SAÍDA BLOQUEADA"


@dataclass(frozen=True)
class DebugWorldSnapshot:
    """Immutable hidden-state snapshot intended only for debug rendering."""

    rows: int
    cols: int
    agent_position: Position
    agent_direction: Direction
    entities: Mapping[Position, EntityType]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", MappingProxyType(dict(self.entities)))

    def entity_at(self, position: Position) -> EntityType:
        """Return the current real entity at an in-bounds position."""

        if not position.is_inside(self.rows, self.cols):
            raise ValueError(f"Position outside debug snapshot: {position}")
        return self.entities.get(position, EntityType.EMPTY)


class World:
    """Own the hidden map and apply environment rules to agent actions."""

    def __init__(
        self,
        generated_map: GeneratedMap,
        *,
        rng: random.Random,
        objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
    ) -> None:
        if not START_POSITION.is_inside(generated_map.rows, generated_map.cols):
            raise ValueError("Generated map does not contain the start position")

        self._rows = generated_map.rows
        self._cols = generated_map.cols
        self._exit_position = exit_position_for(self._rows, self._cols)
        self._objective = objective
        self._rng = rng
        self._alive_wumpus = self._positions_for(
            generated_map, EntityType.WUMPUS
        )
        self._dead_wumpus: set[Position] = set()
        self._pits = self._positions_for(generated_map, EntityType.PIT)
        self._bats = self._positions_for(generated_map, EntityType.BAT)
        self._gold = self._positions_for(generated_map, EntityType.GOLD)
        self._required_gold = len(self._gold)

        self._agent_position = START_POSITION
        self._agent_direction = START_DIRECTION
        self._score = 0
        self._collected_gold = 0
        self._game_over = False
        self._escaped = False
        self._dead = False
        self._last_bump = False
        self._last_scream = False
        self._last_event: str | None = None

    @staticmethod
    def _positions_for(
        generated_map: GeneratedMap, entity_type: EntityType
    ) -> set[Position]:
        return {
            position
            for position, placed_type in generated_map.entities.items()
            if placed_type is entity_type
        }

    @property
    def agent_position(self) -> Position:
        return self._agent_position

    @property
    def agent_direction(self) -> Direction:
        return self._agent_direction

    @property
    def score(self) -> int:
        return self._score

    @property
    def collected_gold(self) -> int:
        return self._collected_gold

    @property
    def required_gold(self) -> int:
        return self._required_gold

    @property
    def objective(self) -> GameObjective:
        return self._objective

    @property
    def exit_position(self) -> Position:
        return self._exit_position

    @property
    def killed_wumpus(self) -> int:
        return len(self._dead_wumpus)

    @property
    def game_over(self) -> bool:
        return self._game_over

    @property
    def escaped(self) -> bool:
        return self._escaped

    @property
    def dead(self) -> bool:
        return self._dead

    @property
    def last_event(self) -> str | None:
        return self._last_event

    def debug_snapshot(self) -> DebugWorldSnapshot:
        """Return hidden state for the explicit professor/debug path only."""

        entities = {
            **dict.fromkeys(self._alive_wumpus, EntityType.WUMPUS),
            **dict.fromkeys(self._pits, EntityType.PIT),
            **dict.fromkeys(self._gold, EntityType.GOLD),
            **dict.fromkeys(self._bats, EntityType.BAT),
        }
        return DebugWorldSnapshot(
            rows=self._rows,
            cols=self._cols,
            agent_position=self._agent_position,
            agent_direction=self._agent_direction,
            entities=entities,
        )

    def observation(self) -> AgentObservation:
        """Return the only information surface exposed to the agent."""

        return AgentObservation(
            position=self._agent_position,
            direction=self._agent_direction,
            perception=self.observe(),
            score=self._score,
            collected_gold=self._collected_gold,
            active=not self._game_over,
        )

    def observe(self) -> Perception:
        """Return current perceptions and consume transient event signals."""

        perception = sense(
            self._agent_position,
            alive_wumpus=self._alive_wumpus,
            pits=self._pits,
            bats=self._bats,
            gold=self._gold,
            bump=self._last_bump,
            scream=self._last_scream,
        )
        self._last_bump = False
        self._last_scream = False
        return perception

    def execute(self, action: Action) -> ActionResult:
        """Apply one supported action and return its observable result."""

        if self._game_over:
            raise RuntimeError("Cannot execute actions after the game ends")
        score_before = self._score
        gold_collected = False
        wumpus_killed = False
        teleported = False
        exit_blocked = False
        self._last_event = None
        self._score += action_cost(action)

        if action is Action.MOVE_FORWARD:
            teleported, exit_blocked = self._move_forward()
        elif action in (Action.TURN_RIGHT, Action.TURN_LEFT):
            self._agent_direction = rotated(self._agent_direction, action)
        elif action is Action.GRAB:
            gold_collected = self._grab_gold()
        elif action is Action.SHOOT:
            wumpus_killed = self._shoot()
        elif action is Action.CLIMB:
            self._climb()
        else:
            raise ValueError(f"Unsupported action: {action}")

        return ActionResult(
            action=action,
            position=self._agent_position,
            direction=self._agent_direction,
            score_delta=self._score - score_before,
            total_score=self._score,
            perception=self.observe(),
            gold_collected=gold_collected,
            wumpus_killed=wumpus_killed,
            teleported=teleported,
            died=self._dead,
            escaped=self._escaped,
            exit_blocked=exit_blocked,
        )

    def _move_forward(self) -> tuple[bool, bool]:
        destination = forward_position(
            self._agent_position, self._agent_direction
        )
        if not destination.is_inside(self._rows, self._cols):
            self._last_bump = True
            return False, False

        self._agent_position = destination
        if destination in self._bats:
            return self._teleport_from_bat()

        return False, self._resolve_current_position()

    def _teleport_from_bat(self) -> tuple[bool, bool]:
        for _ in range(MAX_BAT_TELEPORT_CHAIN):
            self._agent_position = choose_teleport_destination(
                self._rng,
                rows=self._rows,
                cols=self._cols,
            )
            if self._agent_position not in self._bats:
                return True, self._resolve_current_position()

        self._last_event = BAT_CHAIN_LIMIT_EVENT
        self._agent_position = choose_teleport_destination(
            self._rng,
            rows=self._rows,
            cols=self._cols,
            excluded=self._bats,
        )
        return True, self._resolve_current_position()

    def _resolve_current_position(self) -> bool:
        if (
            self._agent_position in self._pits
            or self._agent_position in self._alive_wumpus
        ):
            self._score += DEATH_PENALTY
            self._dead = True
            self._game_over = True
            return False

        if self._agent_position == self._exit_position:
            if self._exit_requirement_satisfied():
                self._escaped = True
                self._game_over = True
            else:
                self._last_event = EXIT_BLOCKED_EVENT
                return True
        return False

    def _exit_requirement_satisfied(self) -> bool:
        if self._objective is GameObjective.ESCAPE_FAST:
            return True
        if self._objective is GameObjective.COLLECT_ALL_GOLD:
            return self._collected_gold >= self._required_gold
        raise AssertionError(f"Unsupported game objective: {self._objective!r}")

    def _grab_gold(self) -> bool:
        if self._agent_position not in self._gold:
            return False

        self._gold.remove(self._agent_position)
        self._collected_gold += 1
        self._score += GOLD_REWARD
        return True

    def _shoot(self) -> bool:
        for position in line_of_fire(
            self._agent_position,
            self._agent_direction,
            rows=self._rows,
            cols=self._cols,
        ):
            if position not in self._alive_wumpus:
                continue

            self._alive_wumpus.remove(position)
            self._dead_wumpus.add(position)
            self._last_scream = True
            return True

        return False

    def _climb(self) -> None:
        self._last_event = INVALID_CLIMB_EVENT
