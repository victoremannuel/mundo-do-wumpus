"""Public match objectives shared by the environment and agent strategy."""

from enum import Enum, auto


class GameObjective(Enum):
    """The rule a match must satisfy before its automatic exit succeeds."""

    ESCAPE_FAST = auto()
    COLLECT_ALL_GOLD = auto()


OBJECTIVE_LABELS = {
    GameObjective.ESCAPE_FAST: "ESCAPAR O MAIS RÁPIDO POSSÍVEL",
    GameObjective.COLLECT_ALL_GOLD: "COLETAR TODOS OS OUROS ANTES DE ESCAPAR",
}
