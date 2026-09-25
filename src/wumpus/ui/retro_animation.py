"""Short, deterministic retro animations for things the game already reported.

What an animation is here
-------------------------
An `AnimationEvent` says *what happened*; expanding it produces a fixed list of
`AnimationFrame`s, and one Textual ticker consumes exactly one frame per tick.
A frame is pure decoration: a `MapOverlay`, an optional banner, an optional
border colour, and a phase number per animated sensor. Nothing in this module
can move the agent, change a score, kill a Wumpus, collect gold, teleport, or
touch the knowledge base -- it only reads an `ActionResult` the environment has
already produced.

Why every table is fixed
------------------------
No frame is ever chosen at random. Visual randomness would consume the game's
seeded RNG and break reproducibility, so particles, glitches, and sensor motifs
all come from the constant tuples below.

Why there is a single clock
---------------------------
One controller and one ticker drive every effect. Sensors animate concurrently
with the action that revealed them instead of queueing behind it, so a turn with
stench, breeze, and bat noise still resolves in well under a second.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from types import MappingProxyType

from wumpus.agent.planner import FORWARD_DELTA
from wumpus.domain import Action, ActionResult, Direction, Perception, Position
from wumpus.ui.retro_state import MapOverlay
from wumpus.ui.retro_tiles import (
    BUMP_SPRITE,
    DEATH_SPRITE,
    GLITCH_SPRITES,
    GOLD_BURST_SPRITES,
    PROJECTILE_SPRITES,
    TRAIL_SPRITE,
)
from wumpus.ui.symbols import (
    RETRO_AGENT_HOT_STYLE,
    RETRO_AGENT_STYLE,
    RETRO_BANNER_STYLE,
    RETRO_BAT_STYLE,
    RETRO_BEAM_STYLE,
    RETRO_BORDER_ALERT,
    RETRO_BORDER_BAT,
    RETRO_BORDER_ESCAPE,
    RETRO_BORDER_GOLD,
    RETRO_BORDER_IMPACT,
    RETRO_BORDER_WUMPUS,
    RETRO_DEAD_WUMPUS_STYLE,
    RETRO_DEATH_STYLE,
    RETRO_ESCAPE_STYLE,
    RETRO_GLITCH_STYLES,
    RETRO_GOLD_STYLE,
    RETRO_TRAIL_STYLE,
)


# A terminal pixel animation needs far fewer frames than a real game: 0.08s is
# about 12.5 FPS, which reads as motion without making a turn feel slow.
ANIMATION_FRAME_INTERVAL = 0.08


class AnimationKind(Enum):
    """The visual events the interface knows how to play."""

    INTRO = auto()
    MOVE = auto()
    TURN = auto()
    SHOOT = auto()
    WUMPUS_KILLED = auto()
    GRAB = auto()
    TELEPORT = auto()
    BUMP = auto()
    DEATH = auto()
    ESCAPE = auto()
    SENSORS = auto()


# Frame counts, and therefore durations, per event. Kept in one table so the
# timing budget of a turn can be read and tested in a single place.
FRAME_COUNTS = MappingProxyType(
    {
        AnimationKind.INTRO: 8,  # 640 ms
        AnimationKind.MOVE: 3,  # 240 ms
        AnimationKind.TURN: 3,  # 240 ms
        AnimationKind.SHOOT: 5,  # 400 ms, trimmed to the wall distance
        AnimationKind.WUMPUS_KILLED: 4,  # 320 ms
        AnimationKind.GRAB: 5,  # 400 ms
        AnimationKind.TELEPORT: 6,  # 480 ms
        AnimationKind.BUMP: 4,  # 320 ms
        AnimationKind.DEATH: 7,  # 560 ms
        AnimationKind.ESCAPE: 6,  # 480 ms
        AnimationKind.SENSORS: 6,  # 480 ms
    }
)

BANNER_WUMPUS_KILLED = "WUMPUS ELIMINADO"
BANNER_ESCAPED = "ESCAPOU DA CAVERNA"
BANNER_DEAD = "GAME OVER"
BANNER_TELEPORT = "MORCEGO!"
BANNER_BUMP = "PAREDE!"
BANNER_GOLD = "OURO!"
INTRO_BANNERS = ("READY", "READY", "3", "2", "1", "EXPLORE", "EXPLORE", "")


# ---------------------------------------------------------------------------
# Sensor motifs
#
# Each sensor gets its own small moving figure so a player can tell them apart
# without reading the label. Every motif is exactly `SENSOR_MOTIF_WIDTH` visual
# columns so the panel can never misalign, and none of them says *where* the
# hazard is -- only that it is near.
# ---------------------------------------------------------------------------

SENSOR_MOTIF_WIDTH = 4

SENSOR_MOTIFS = MappingProxyType(
    {
        # Stench thickening and thinning in place.
        "FEDOR": ("~~  ", "~~~ ", "~~~~", "~~~ ", "~~  ", " ~  "),
        # A gust of wind drifting past.
        "BRISA": ("~   ", " ~~ ", "  ~~", " ~~ ", "~~  ", "~   "),
        # Wings beating.
        "MORCEGO": ("\\  /", " \\/ ", " /\\ ", "/  \\", " \\/ ", " /\\ "),
        # Light glinting off gold in this very room.
        "BRILHO": (" *  ", " *+ ", "*+*·", " +* ", " *  ", "·*· "),
        # A single hard knock.
        "IMPACTO": ("><  ", "!!  ", "><  ", " ·  ", "><  ", "    "),
        # A scream rising.
        "GRITO": ("!   ", "!!  ", "!!! ", "!!!!", "!!! ", "!!  "),
    }
)

# Frames on which an animating sensor is drawn at full intensity, so the label
# visibly pulses instead of merely switching on.
SENSOR_PEAK_PHASES = frozenset({1, 2, 3})


def sensor_motif(label: str, phase: int | None, *, active: bool) -> str:
    """Return the motif cell for one sensor: animating, steady, or blank."""

    motif = SENSOR_MOTIFS[label]
    if not active:
        return " " * SENSOR_MOTIF_WIDTH
    if phase is None:
        return motif[0]
    return motif[phase % len(motif)]


def sensor_is_emphasised(phase: int | None) -> bool:
    """Whether this sensor is on a peak frame of its own animation."""

    return phase is not None and phase in SENSOR_PEAK_PHASES


# ---------------------------------------------------------------------------
# Events and frames
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AnimationEvent:
    """One thing worth showing, plus the already-observable data to show it with."""

    kind: AnimationKind
    position: Position | None = None
    origin: Position | None = None
    direction: Direction | None = None
    bounds: tuple[int, int] | None = None
    sensors: tuple[str, ...] = ()

    @property
    def frames(self) -> int:
        return FRAME_COUNTS[self.kind]


@dataclass(frozen=True)
class AnimationFrame:
    """One tick of decoration over an otherwise unchanged screen."""

    kinds: frozenset[AnimationKind] = field(default_factory=frozenset)
    overlay: MapOverlay = field(default_factory=MapOverlay)
    banner: str | None = None
    border_flash: str | None = None
    sensor_phases: tuple[tuple[str, int], ...] = ()

    @property
    def phases(self) -> Mapping[str, int]:
        return dict(self.sensor_phases)

    def has(self, kind: AnimationKind) -> bool:
        return kind in self.kinds


def _frame(kind: AnimationKind, **fields: object) -> AnimationFrame:
    return AnimationFrame(kinds=frozenset({kind}), **fields)  # type: ignore[arg-type]


def merge_frames(first: AnimationFrame, second: AnimationFrame) -> AnimationFrame:
    """Combine two concurrent frames into the one the screen actually draws."""

    a, b = first.overlay, second.overlay
    overlay = MapOverlay(
        agent_style=a.agent_style or b.agent_style,
        agent_sprite=a.agent_sprite or b.agent_sprite,
        agent_hidden=a.agent_hidden or b.agent_hidden,
        trail=a.trail + b.trail,
        trail_style=a.trail_style or b.trail_style,
        projectile=a.projectile or b.projectile,
        projectile_sprite=a.projectile_sprite or b.projectile_sprite,
        projectile_style=a.projectile_style or b.projectile_style,
        cell_flash=a.cell_flash + b.cell_flash,
        cell_flash_sprite=a.cell_flash_sprite or b.cell_flash_sprite,
    )
    return AnimationFrame(
        kinds=first.kinds | second.kinds,
        overlay=overlay,
        banner=first.banner or second.banner,
        border_flash=first.border_flash or second.border_flash,
        sensor_phases=first.sensor_phases + second.sensor_phases,
    )


# ---------------------------------------------------------------------------
# Expansion: one event becomes a fixed list of frames
# ---------------------------------------------------------------------------


def _intro_frames(event: AnimationEvent) -> list[AnimationFrame]:
    return [
        _frame(
            AnimationKind.INTRO,
            banner=INTRO_BANNERS[index] or None,
            border_flash=RETRO_BORDER_ESCAPE if index < 2 else None,
        )
        for index in range(event.frames)
    ]


def _move_frames(event: AnimationEvent) -> list[AnimationFrame]:
    """Emphasise the old room, streak between the rooms, then the new room."""

    origin = event.origin
    return [
        _frame(
            AnimationKind.MOVE,
            overlay=MapOverlay(
                agent_style=RETRO_AGENT_HOT_STYLE,
                trail=() if origin is None else (origin,),
                trail_style=RETRO_TRAIL_STYLE,
            ),
        ),
        _frame(
            AnimationKind.MOVE,
            overlay=MapOverlay(
                agent_style=RETRO_AGENT_HOT_STYLE,
                trail=() if origin is None else (origin,),
                trail_style=RETRO_TRAIL_STYLE,
            ),
        ),
        _frame(
            AnimationKind.MOVE,
            overlay=MapOverlay(agent_style=RETRO_AGENT_HOT_STYLE),
        ),
    ]


def _turn_frames(event: AnimationEvent) -> list[AnimationFrame]:
    """Pulse the agent in place; the logical direction already changed."""

    styles = (RETRO_AGENT_HOT_STYLE, RETRO_AGENT_STYLE, RETRO_AGENT_HOT_STYLE)
    return [
        _frame(AnimationKind.TURN, overlay=MapOverlay(agent_style=style))
        for style in styles[: event.frames]
    ]


def shot_path(
    origin: Position, direction: Direction, bounds: tuple[int, int]
) -> tuple[Position, ...]:
    """Every room the arrow visibly crosses, from the next one to the wall.

    The path always runs to the wall. It must never stop at the room a Wumpus
    secretly occupies, because that coordinate is not something the player is
    allowed to learn from an animation.
    """

    rows, cols = bounds
    delta_row, delta_col = FORWARD_DELTA[direction]
    path: list[Position] = []
    cursor = Position(origin.row + delta_row, origin.col + delta_col)
    while cursor.is_inside(rows, cols):
        path.append(cursor)
        cursor = Position(cursor.row + delta_row, cursor.col + delta_col)
    return tuple(path)


def _shoot_frames(event: AnimationEvent) -> list[AnimationFrame]:
    if event.position is None or event.direction is None or event.bounds is None:
        return []

    path = shot_path(event.position, event.direction, event.bounds)
    frames = [
        _frame(
            AnimationKind.SHOOT,
            overlay=MapOverlay(
                agent_style=RETRO_AGENT_HOT_STYLE,
                projectile=cell,
                projectile_sprite=PROJECTILE_SPRITES[index % len(PROJECTILE_SPRITES)],
                projectile_style=RETRO_BEAM_STYLE,
            ),
        )
        for index, cell in enumerate(path)
    ]
    if not frames:
        frames = [
            _frame(
                AnimationKind.SHOOT,
                overlay=MapOverlay(agent_style=RETRO_AGENT_HOT_STYLE),
            )
        ]
    return frames


def _wumpus_killed_frames(event: AnimationEvent) -> list[AnimationFrame]:
    """A cave-wide scream. No coordinate is revealed, because none is known."""

    borders = (
        RETRO_BORDER_WUMPUS,
        RETRO_BORDER_ALERT,
        RETRO_BORDER_WUMPUS,
        RETRO_BORDER_ALERT,
    )
    return [
        _frame(
            AnimationKind.WUMPUS_KILLED,
            banner=BANNER_WUMPUS_KILLED,
            border_flash=borders[index % len(borders)],
            overlay=MapOverlay(
                agent_style=RETRO_DEAD_WUMPUS_STYLE if index % 2 else None
            ),
        )
        for index in range(event.frames)
    ]


def _grab_frames(event: AnimationEvent) -> list[AnimationFrame]:
    position = event.position
    flash = () if position is None else ((position, RETRO_GOLD_STYLE),)
    sprites = (None, *GOLD_BURST_SPRITES, None)
    return [
        _frame(
            AnimationKind.GRAB,
            banner=BANNER_GOLD,
            border_flash=RETRO_BORDER_GOLD if index < 3 else None,
            overlay=MapOverlay(
                agent_style=RETRO_GOLD_STYLE,
                agent_sprite=sprites[index],
                cell_flash=flash,
            ),
        )
        for index in range(min(event.frames, len(sprites)))
    ]


def _teleport_frames(event: AnimationEvent) -> list[AnimationFrame]:
    """Bat, blackout, glitch, arrival -- and only the reported destination."""

    position = event.position
    frames: list[AnimationFrame] = []
    for index in range(event.frames):
        hidden = 1 <= index <= 3
        sprite = GLITCH_SPRITES[index % len(GLITCH_SPRITES)] if hidden else None
        style = RETRO_GLITCH_STYLES[index % len(RETRO_GLITCH_STYLES)]
        flash = (
            ((position, style),) if position is not None and not hidden else ()
        )
        frames.append(
            _frame(
                AnimationKind.TELEPORT,
                banner=BANNER_TELEPORT,
                border_flash=RETRO_BORDER_BAT,
                overlay=MapOverlay(
                    agent_style=RETRO_BAT_STYLE,
                    agent_hidden=hidden,
                    agent_sprite=sprite,
                    cell_flash=flash,
                ),
            )
        )
    return frames


def _bump_frames(event: AnimationEvent) -> list[AnimationFrame]:
    sprites = (BUMP_SPRITE, None, BUMP_SPRITE, None)
    borders = (RETRO_BORDER_IMPACT, RETRO_BORDER_ALERT, RETRO_BORDER_IMPACT, None)
    return [
        _frame(
            AnimationKind.BUMP,
            banner=BANNER_BUMP,
            border_flash=borders[index],
            overlay=MapOverlay(
                agent_style=RETRO_AGENT_HOT_STYLE,
                agent_sprite=sprites[index],
            ),
        )
        for index in range(min(event.frames, len(sprites)))
    ]


def _death_frames(event: AnimationEvent) -> list[AnimationFrame]:
    styles = (
        RETRO_AGENT_STYLE,
        RETRO_AGENT_HOT_STYLE,
        RETRO_DEATH_STYLE,
        RETRO_DEATH_STYLE,
        RETRO_DEATH_STYLE,
        RETRO_DEAD_WUMPUS_STYLE,
        RETRO_DEAD_WUMPUS_STYLE,
    )
    sprites = (None, None, DEATH_SPRITE, DEATH_SPRITE, DEATH_SPRITE, DEATH_SPRITE, DEATH_SPRITE)
    position = event.position
    return [
        _frame(
            AnimationKind.DEATH,
            banner=BANNER_DEAD if index >= 2 else None,
            border_flash=RETRO_BORDER_ALERT if index < 5 else None,
            overlay=MapOverlay(
                agent_style=styles[index],
                agent_sprite=sprites[index],
                cell_flash=(
                    ((position, RETRO_DEATH_STYLE),)
                    if position is not None and index in (2, 4)
                    else ()
                ),
            ),
        )
        for index in range(min(event.frames, len(styles)))
    ]


def _escape_frames(event: AnimationEvent) -> list[AnimationFrame]:
    position = event.position
    return [
        _frame(
            AnimationKind.ESCAPE,
            banner=BANNER_ESCAPED,
            border_flash=RETRO_BORDER_ESCAPE if index % 2 == 0 else None,
            overlay=MapOverlay(
                agent_style=(
                    RETRO_ESCAPE_STYLE if index % 2 == 0 else RETRO_AGENT_HOT_STYLE
                ),
                cell_flash=(
                    ((position, RETRO_ESCAPE_STYLE),)
                    if position is not None and index % 2 == 0
                    else ()
                ),
            ),
        )
        for index in range(event.frames)
    ]


def _sensor_frames(event: AnimationEvent) -> list[AnimationFrame]:
    """One frame list carrying every active sensor's phase, so they run together."""

    if not event.sensors:
        return []
    return [
        _frame(
            AnimationKind.SENSORS,
            sensor_phases=tuple((label, index) for label in event.sensors),
        )
        for index in range(event.frames)
    ]


_EXPANDERS = {
    AnimationKind.INTRO: _intro_frames,
    AnimationKind.MOVE: _move_frames,
    AnimationKind.TURN: _turn_frames,
    AnimationKind.SHOOT: _shoot_frames,
    AnimationKind.WUMPUS_KILLED: _wumpus_killed_frames,
    AnimationKind.GRAB: _grab_frames,
    AnimationKind.TELEPORT: _teleport_frames,
    AnimationKind.BUMP: _bump_frames,
    AnimationKind.DEATH: _death_frames,
    AnimationKind.ESCAPE: _escape_frames,
    AnimationKind.SENSORS: _sensor_frames,
}


def expand_event(event: AnimationEvent) -> tuple[AnimationFrame, ...]:
    """Turn one event into its fixed frame sequence."""

    return tuple(_EXPANDERS[event.kind](event))


def expand_events(events: Iterable[AnimationEvent]) -> tuple[AnimationFrame, ...]:
    """Lay out a turn: action effects in order, sensor feedback alongside them.

    Sensors deliberately do *not* queue behind the action. A room with stench,
    breeze, and bat noise would otherwise cost three separate animations and make
    every turn crawl; running them concurrently keeps a normal turn short while
    still giving each sensor its own visible motif.
    """

    action_frames: list[AnimationFrame] = []
    sensor_frames: list[AnimationFrame] = []
    for event in events:
        if event.kind is AnimationKind.SENSORS:
            sensor_frames.extend(expand_event(event))
        else:
            action_frames.extend(expand_event(event))

    if not sensor_frames:
        return tuple(action_frames)
    if not action_frames:
        return tuple(sensor_frames)

    length = max(len(action_frames), len(sensor_frames))
    merged: list[AnimationFrame] = []
    for index in range(length):
        action = (
            action_frames[index]
            if index < len(action_frames)
            else replace(action_frames[-1], overlay=MapOverlay(), banner=None)
        )
        sensor = (
            sensor_frames[index]
            if index < len(sensor_frames)
            else replace(sensor_frames[-1], sensor_phases=())
        )
        merged.append(merge_frames(action, sensor))
    return tuple(merged)


# ---------------------------------------------------------------------------
# Deriving events from what the environment actually reported
# ---------------------------------------------------------------------------

PERSISTENT_SENSORS: tuple[tuple[str, str], ...] = (
    ("FEDOR", "stench"),
    ("BRISA", "breeze"),
    ("MORCEGO", "bat_noise"),
    ("BRILHO", "glitter"),
)
TRANSIENT_SENSORS: tuple[tuple[str, str], ...] = (
    ("IMPACTO", "bump"),
    ("GRITO", "scream"),
)


def sensors_to_animate(
    perception: Perception,
    *,
    previous: Perception | None,
    entered_new_room: bool,
) -> tuple[str, ...]:
    """Pick which sensors deserve a full animation this turn.

    A persistent sensor animates when it switches on, or when the agent walks
    into a new room where it is already on. Merely turning in place keeps the
    sensor lit without replaying the whole dramatic sequence. Bump and scream are
    single events, so they always animate.
    """

    labels: list[str] = []
    for label, attribute in PERSISTENT_SENSORS:
        if not getattr(perception, attribute):
            continue
        was_on = previous is not None and getattr(previous, attribute)
        if entered_new_room or not was_on:
            labels.append(label)
    for label, attribute in TRANSIENT_SENSORS:
        if getattr(perception, attribute):
            labels.append(label)
    return tuple(labels)


def build_intro_events() -> tuple[AnimationEvent, ...]:
    """The short title-in animation played once when a match starts."""

    return (AnimationEvent(kind=AnimationKind.INTRO),)


def build_initial_sensor_events(perception: Perception) -> tuple[AnimationEvent, ...]:
    """Animate sensors already active in the entrance after the intro."""

    labels = sensors_to_animate(
        perception,
        previous=None,
        entered_new_room=False,
    )
    if not labels:
        return ()
    return (AnimationEvent(kind=AnimationKind.SENSORS, sensors=labels),)


def build_turn_events(
    result: ActionResult,
    *,
    previous_position: Position,
    previous_perception: Perception | None,
    bounds: tuple[int, int],
) -> tuple[AnimationEvent, ...]:
    """Derive this turn's visual events from the environment's own report.

    Everything read here -- action, position, direction, the gold/kill/teleport/
    death/escape flags, and the perception -- is data the agent is already given.
    No hidden state is consulted, so an animation can never leak a coordinate the
    player was not told.
    """

    events: list[AnimationEvent] = []
    position = result.position
    perception = result.perception

    if result.died:
        if result.teleported:
            events.append(
                AnimationEvent(kind=AnimationKind.TELEPORT, position=position)
            )
        events.append(AnimationEvent(kind=AnimationKind.DEATH, position=position))
    elif result.escaped:
        events.append(AnimationEvent(kind=AnimationKind.ESCAPE, position=position))
    else:
        if result.action is Action.SHOOT:
            events.append(
                AnimationEvent(
                    kind=AnimationKind.SHOOT,
                    position=position,
                    direction=result.direction,
                    bounds=bounds,
                )
            )
        if result.wumpus_killed:
            events.append(AnimationEvent(kind=AnimationKind.WUMPUS_KILLED))
        if result.teleported:
            events.append(
                AnimationEvent(kind=AnimationKind.TELEPORT, position=position)
            )
        elif result.action is Action.MOVE_FORWARD and position != previous_position:
            events.append(
                AnimationEvent(
                    kind=AnimationKind.MOVE,
                    position=position,
                    origin=previous_position,
                )
            )
        if perception.bump:
            events.append(AnimationEvent(kind=AnimationKind.BUMP, position=position))
        if result.action in (Action.TURN_LEFT, Action.TURN_RIGHT):
            events.append(
                AnimationEvent(
                    kind=AnimationKind.TURN,
                    position=position,
                    direction=result.direction,
                )
            )
        if result.gold_collected:
            events.append(AnimationEvent(kind=AnimationKind.GRAB, position=position))

    labels = sensors_to_animate(
        perception,
        previous=previous_perception,
        entered_new_room=position != previous_position,
    )
    if labels and not result.died:
        events.append(AnimationEvent(kind=AnimationKind.SENSORS, sensors=labels))

    return tuple(events)


# ---------------------------------------------------------------------------
# The single clock
# ---------------------------------------------------------------------------


class AnimationController:
    """One queue, one current frame, one ticker. Never a timer per effect."""

    def __init__(self) -> None:
        self._frames: deque[AnimationFrame] = deque()
        self._frame: AnimationFrame | None = None

    @property
    def busy(self) -> bool:
        """Whether a frame is on screen or still waiting to be drawn."""

        return self._frame is not None or bool(self._frames)

    @property
    def frame(self) -> AnimationFrame | None:
        """The frame the screen should currently decorate itself with."""

        return self._frame

    @property
    def pending(self) -> int:
        return len(self._frames)

    def enqueue(self, events: Iterable[AnimationEvent]) -> int:
        """Queue every frame of these events; return how many were added."""

        frames = expand_events(events)
        self._frames.extend(frames)
        return len(frames)

    def enqueue_frames(self, frames: Sequence[AnimationFrame]) -> None:
        self._frames.extend(frames)

    def advance(self) -> bool:
        """Show the next queued frame. Returns whether anything is still playing."""

        if self._frames:
            self._frame = self._frames.popleft()
            return True
        self._frame = None
        return False

    def cancel(self) -> None:
        """Drop every frame at once, so a restart leaves nothing mid-flight."""

        self._frames.clear()
        self._frame = None
