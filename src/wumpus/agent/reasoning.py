"""Structured decision events the agent emits for external rendering (section 68).

The agent records *why* it chose an action as data, never as natural language
composed for display -- a renderer is responsible for translating this into
human-readable text.
"""

from __future__ import annotations

from dataclasses import dataclass

from wumpus.domain import Action, Position


@dataclass(frozen=True)
class DecisionReason:
    """One structured explanation for the action returned by `Strategy.decide`."""

    action: Action | None
    reason: str
    target: Position | None = None
