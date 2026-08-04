# Engine game-authoring prompt

You are writing a complete, deterministic ARC-AGI-3 game with `engine`.
Prefer small symbolic grids, named sprites, short mechanics, and explicit state.
Use symbols for every color and sprite cell. Treat the engine's storage,
rendering, and protocol conversion as opaque implementation details.

## Palette and grids

Use this exact palette:

```python
ARC_COLOR_CHARS = "WwgGcBMPRbSYOrNp"
ARC_COLOR_LEGEND = (
    "W=white, w=light gray, g=gray, G=dark gray, c=charcoal, B=black, "
    "M=magenta, P=pink, R=red, b=blue, S=sky blue, Y=yellow, O=orange, "
    "r=dark red, N=light green, p=purple"
)
```

Special cells:

- `.`: empty, invisible, and passable.
- `X`: invisible but solid in pixel-perfect collision.

Case matters: `B/b`, `P/p`, `R/r`, `W/w`, and `G/g` are different colors.
Write rectangular grids as quoted row strings:

```python
wall = Sprite(
    [
        "BBBBBBB",
        "B.....B",
        "B.XXX.B",
        "B.....B",
        "BBBBBBB",
    ],
    name="wall",
)
```

`["WWWggW"]` is valid; `[WWWggW]` is invalid Python. A dedented multiline
string is also canonical:

```python
player = Sprite(
    """
        .RR.
        RRRR
        .RR.
    """,
    name="player",
)
```

Never use integer color codes in game source. Author and inspect grids only
through the symbolic forms below.

Symbolic inspection:

- `sprite.pixels` → immutable source rows such as `("W.R", "BBB")`.
- `sprite.symbols` → immutable source rows such as `("W.R", "BBB")`.
- `sprite.render()` → immutable transformed rows using the same symbols.
- `sprite.set_pixel(x, y, "R")` and `sprite.set_pixels(["R.", ".R"])` mutate
  source cells without introducing color numbers.
- `sprite.crop(right=1)` shrinks an untransformed sprite from an edge;
  `sprite.pad(left=1, fill="R")` grows it while preserving existing cells at
  their world coordinates.
- `sprite.contains_point(x, y)` performs a transform-aware, pixel-perfect
  world-coordinate hit test.
- `level.get_sprites_at(x, y)` returns matching sprites from highest to lowest
  layer; `level.get_sprite_at(x, y)` returns only the top match.
- `sprite.to_ascii()` → source grid as text, preserving `.` and `X`;
  `sprite.to_ascii(rendered=True)` includes transforms.
- `format_grid_ascii(frame)` → a rendered frame as symbolic text.
- `sprite.color_remap("R", "b")` accepts color symbols; `.` erases and `X`
  creates invisible solid cells.
- `Camera(background="B", letter_box="G")` accepts symbols.

Numeric palette indices are an output-protocol detail. They may appear in the
frame sequence returned by `perform_action()`, but sprite construction,
inspection, transforms, color operations, and camera-region inspection remain
symbolic.

## Core model

- Coordinates are `(x, y)`, origin top-left; +x is right and +y is down.
- A `Sprite` has pixels, position, layer, transforms, blocking, interaction,
  name, and tags.
- Lower layers render first; higher layers appear on top.
- Rotation is `0`, `90`, `180`, or `270`.
- Positive scale repeats cells. Negative scale downsamples: `-1` divides by 2,
  `-2` by 3, etc. Scale `0` is invalid.
- `Level` groups sprites and may set `grid_size=(width, height)`.
- The camera renders its viewport, integer-upscales it, centers it with
  letterboxing, then applies UI overlays. Final output is always 64×64.
- Game construction and resets clone levels/sprites. Rebind stored sprite
  references in `on_set_level(level)` by name or tag.

Collision:

- `BlockingMode.PIXEL_PERFECT`: only overlapping solid cells collide; `.` is a
  hole, `X` and visible colors are solid.
- `BlockingMode.BOUNDING_BOX`: rectangular collision.
- `BlockingMode.NOT_BLOCKED`: no collision.
- `InteractionMode.TANGIBLE`: visible + collidable.
- `InteractionMode.INTANGIBLE`: visible + non-collidable.
- `InteractionMode.INVISIBLE`: hidden + collidable.
- `InteractionMode.REMOVED`: hidden + non-collidable.
- `try_move_sprite(sprite, dx, dy)` tentatively moves, then restores the old
  position and returns collisions if blocked.

## Actions and lifecycle

- `RESET=0`.
- `ACTION1=up`, `ACTION2=down`, `ACTION3=left`, `ACTION4=right` by common
  convention.
- `ACTION5` is the primary/space action.
- `ACTION6` is a click/place action with display coordinates in `0..63`. Use
  `x, y = action.require_position()` and then
  `camera.display_to_grid(x, y)` for world coordinates. Optional accessors
  `action.x`, `action.y`, and `action.position` return `None` for actions with
  no position; the raw mapping remains available as `action.data`.
- `ACTION7` is commonly undo.
- Declare enabled IDs with `available_actions`; the default is 1..6.

Put mechanics in `step()`. `perform_action()` repeatedly calls `step()` and
renders after each call until `complete_action()` is called. Always complete
every action path. To animate, change state over several calls and complete
only on the final frame. Use `next_level()` after a solved level, `win()` for an
immediate win, and `lose()` for game over.

Useful system tags:

- `sys_static`: eligible pixel-perfect sprites are merged per layer when a
  level is built.
- `sys_click`: exposes an ACTION6 location for a sprite.
- `sys_every_pixel`: with `sys_click`, exposes every visible color cell; `.`
  and `X` do not generate click points.
- `sys_place`: marks a place/click target.

## Minimal working game

```python
from engine import (
    ARCBaseGame,
    ActionInput,
    BlockingMode,
    Camera,
    GameAction,
    InteractionMode,
    Level,
    Sprite,
)

MOVE = {
    GameAction.ACTION1: (0, -1),
    GameAction.ACTION2: (0, 1),
    GameAction.ACTION3: (-1, 0),
    GameAction.ACTION4: (1, 0),
}

walls = Sprite(
    [
        "BBBBBBB",
        "B.....B",
        "B.BBB.B",
        "B.....B",
        "BBBBBBB",
    ],
    name="walls",
    layer=0,
    blocking=BlockingMode.PIXEL_PERFECT,
    tags=["sys_static"],
)
goal = Sprite(
    ["N"],
    name="goal",
    x=5,
    y=3,
    layer=1,
    interaction=InteractionMode.INTANGIBLE,
)
player = Sprite(["R"], name="player", x=1, y=1, layer=2)
level = Level(
    [walls, goal, player],
    grid_size=(7, 5),
    name="maze",
)


class TinyMaze(ARCBaseGame):
    def on_set_level(self, level: Level) -> None:
        self.player = level.get_sprites_by_name("player")[0]

    def step(self) -> None:
        delta = MOVE.get(self.action.id)
        if delta is not None:
            self.try_move_sprite(self.player, *delta)
            if (self.player.x, self.player.y) == (5, 3):
                self.next_level()  # One level, so this wins.
        self.complete_action()


game = TinyMaze(
    game_id="tiny_maze",
    levels=[level],
    camera=Camera(background="W", letter_box="B"),
    available_actions=[1, 2, 3, 4],
)

frame_data = game.perform_action(ActionInput(id=GameAction.RESET))
```

## Completion checklist

- All sprite rows are quoted, rectangular, and use only the palette plus
  `.`/`X`.
- Camera colors and `color_remap` calls use symbols.
- Important sprites have stable names/tags; references are rebound in
  `on_set_level`.
- Decorative sprites are non-collidable; walls and holes use the intended
  blocking semantics.
- Every `step()` path eventually calls `complete_action()`.
- Enabled actions match implemented mechanics; ACTION6 coordinates are
  converted through the camera.
- Win, loss, level transition, RESET, and replay behavior are deterministic.
- Use `format_grid_ascii` when a frame must be included in reasoning or debug
  output.
- Tests cover movement, collision, reset, win/loss, and representative renders.
