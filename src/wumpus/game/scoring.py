"""Single source of truth for game scoring values."""

from types import MappingProxyType

from wumpus.domain import Action


ACTION_COSTS = MappingProxyType(
    {
        Action.MOVE_FORWARD: -1,
        Action.TURN_RIGHT: -1,
        Action.GRAB: -1,
        Action.SHOOT: -10,
        Action.CLIMB: -1,
    }
)

GOLD_REWARD = 1000
DEATH_PENALTY = -1000


def action_cost(action: Action) -> int:
    """Return the complete base cost for one action."""

    return ACTION_COSTS[action]
