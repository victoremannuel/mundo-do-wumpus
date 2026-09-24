"""Information exposed by the environment to the logical agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Perception:
    stench: bool
    breeze: bool
    bat_noise: bool
    glitter: bool
    bump: bool
    scream: bool
