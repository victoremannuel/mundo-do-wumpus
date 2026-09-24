"""Private real-world state and deterministic environment mechanics."""

from wumpus.domain import (
    Action,
    ActionResult,
    Direction,
    EntityType,
    Perception,
    Position,
)
from wumpus.environment.actions import forward_position, rotated
from wumpus.environment.generator import GeneratedMap
from wumpus.environment.scoring import DEATH_PENALTY, GOLD_REWARD, action_cost
from wumpus.environment.sensors import sense


START_POSITION = Position(1, 1)
START_DIRECTION = Direction.NORTH
INVALID_CLIMB_EVENT = "Tentativa inválida de saída."


class World:
    """Own the hidden map and apply environment rules to agent actions."""

    def __init__(self, generated_map: GeneratedMap) -> None:
        if not START_POSITION.is_inside(generated_map.rows, generated_map.cols):
            raise ValueError("Generated map does not contain the start position")

        self._rows = generated_map.rows
        self._cols = generated_map.cols
        self._alive_wumpus = self._positions_for(
            generated_map, EntityType.WUMPUS
        )
        self._pits = self._positions_for(generated_map, EntityType.PIT)
        self._bats = self._positions_for(generated_map, EntityType.BAT)
        self._gold = self._positions_for(generated_map, EntityType.GOLD)

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
        if action is Action.SHOOT:
            raise NotImplementedError("SHOOT is implemented in FASE 5")

        score_before = self._score
        gold_collected = False
        self._last_event = None
        self._score += action_cost(action)

        if action is Action.MOVE_FORWARD:
            self._move_forward()
        elif action in (Action.TURN_RIGHT, Action.TURN_LEFT):
            self._agent_direction = rotated(self._agent_direction, action)
        elif action is Action.GRAB:
            gold_collected = self._grab_gold()
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
            died=self._dead,
            escaped=self._escaped,
        )

    def _move_forward(self) -> None:
        destination = forward_position(
            self._agent_position, self._agent_direction
        )
        if not destination.is_inside(self._rows, self._cols):
            self._last_bump = True
            return

        self._agent_position = destination
        if destination in self._pits or destination in self._alive_wumpus:
            self._score += DEATH_PENALTY
            self._dead = True
            self._game_over = True

    def _grab_gold(self) -> bool:
        if self._agent_position not in self._gold:
            return False

        self._gold.remove(self._agent_position)
        self._collected_gold += 1
        self._score += GOLD_REWARD
        return True

    def _climb(self) -> None:
        if self._agent_position == START_POSITION:
            self._escaped = True
            self._game_over = True
            return

        self._last_event = INVALID_CLIMB_EVENT
