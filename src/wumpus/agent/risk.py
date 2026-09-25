"""Least-risk cell scoring for when no proven-safe route remains.

Implements plan sections 42-43 (risk classification and score) as the basis
for `Strategy` priorities 6-7 (section 44): evaluating the least-risk
reachable cell, and recognizing when even that is too dangerous to attempt.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.domain import EntityType, Position


HAZARD_RISK_WEIGHTS = {
    EntityType.PIT: 3,
    EntityType.WUMPUS: 4,
    EntityType.BAT: 2,
}

CONFIRMED_DANGER = float("inf")

# The highest cell score still worth stepping into (priority 7's "expected
# risk excessive" threshold). Read directly off HAZARD_RISK_WEIGHTS instead
# of a separate magic number: any single-hazard candidate is tolerable, but
# never a cell that is a candidate for two or more hazard types at once.
# Sections 47-48's gold-conditioned risk tolerance (accept more before any
# gold, less after) belong to FASE 15's exit-policy scope -- see DEC-005 --
# and are not modeled here.
RISK_THRESHOLD = float(HAZARD_RISK_WEIGHTS[EntityType.WUMPUS])


@dataclass(frozen=True)
class RiskCandidate:
    """One scored, not-yet-safe cell the agent could step into."""

    position: Position
    score: float


def cell_risk(knowledge: KnowledgeBase, position: Position) -> float:
    """Score one cell per section 43's additive hazard-candidate model.

    Returns ``0.0`` for a proven-safe cell, `CONFIRMED_DANGER` for a
    confirmed live pit or Wumpus, and the sum of `HAZARD_RISK_WEIGHTS` for
    every hazard type the cell remains a candidate for otherwise (a
    confirmed bat counts the same as a possible one: known but non-lethal).
    Negative evidence and elimination already retract a hazard's ``possible``
    flag in `KnowledgeBase`/`InferenceEngine`, so no separate reduction step
    is needed here.
    """

    cell = knowledge.cell(position)
    if cell.confirmed_pit or cell.confirmed_wumpus:
        return CONFIRMED_DANGER
    if cell.safe:
        return 0.0

    score = 0.0
    if cell.possible_pit:
        score += HAZARD_RISK_WEIGHTS[EntityType.PIT]
    if cell.possible_wumpus:
        score += HAZARD_RISK_WEIGHTS[EntityType.WUMPUS]
    if cell.possible_bat or cell.confirmed_bat:
        score += HAZARD_RISK_WEIGHTS[EntityType.BAT]
    return score


def least_risk_candidate(
    knowledge: KnowledgeBase,
    position: Position,
) -> RiskCandidate | None:
    """Return the lowest-scoring reachable, uncertain cell, or ``None``.

    A candidate must be orthogonally adjacent to some cell the agent can
    already reach through proven-safe cells -- the agent can only ever step
    into a new cell from an already-reached, adjacent one -- and must carry
    at least one surviving hazard-candidate flag. A cell with no such flag
    is merely unclassified, not a risk decision: real inference always
    proves it safe once its explaining neighbor is visited (see
    `InferenceEngine._apply_negative_rules`), so this only guards against
    synthetic knowledge states that skip inference entirely.
    """

    candidates = [
        RiskCandidate(neighbor, score)
        for safe_cell in _reachable_safe(knowledge, position)
        for neighbor in safe_cell.neighbors()
        if neighbor in knowledge.all_cells and neighbor not in knowledge.safe
        for score in (cell_risk(knowledge, neighbor),)
        if 0.0 < score < CONFIRMED_DANGER
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda candidate: (candidate.score, candidate.position))
    return candidates[0]


def least_risk_candidate_toward(
    knowledge: KnowledgeBase,
    position: Position,
    target: Position,
) -> RiskCandidate | None:
    """Choose an equally acceptable risk deterministically toward ``target``.

    Risk remains the primary ordering.  The target is consulted only after
    confirmed dangers are excluded and candidates have the same risk score.
    """

    candidates = [
        RiskCandidate(neighbor, score)
        for safe_cell in _reachable_safe(knowledge, position)
        for neighbor in safe_cell.neighbors()
        if neighbor in knowledge.all_cells and neighbor not in knowledge.safe
        for score in (cell_risk(knowledge, neighbor),)
        if 0.0 < score < CONFIRMED_DANGER
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda candidate: (
            candidate.score,
            candidate.position.manhattan_distance(target),
            candidate.position,
        )
    )
    return candidates[0]


def _reachable_safe(knowledge: KnowledgeBase, position: Position) -> frozenset[Position]:
    """Return every safe cell connected to ``position`` through safe cells."""

    frontier: deque[Position] = deque([position])
    reached = {position}
    while frontier:
        current = frontier.popleft()
        for neighbor in current.neighbors():
            if neighbor in reached or neighbor not in knowledge.safe:
                continue
            reached.add(neighbor)
            frontier.append(neighbor)
    return frozenset(reached)
