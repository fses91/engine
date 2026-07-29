# ARCEngine game-authoring prompt

You are writing a complete, deterministic ARC-AGI-3 game with `arcengine`.
Prefer small symbolic grids, named sprites, short mechanics, and explicit state.
Keep rendering/protocol data numeric; symbols are the compact authoring and
inspection format.

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

- `.` = `-1`: transparent and passable.
- `X` = `-2`: invisible but solid in pixel-perfect collision.

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

Numeric 2D grids remain accepted, but use symbols in new game source.
`Sprite.pixels`, `Sprite.render()`, and raw camera frames are numeric `np.int8`
arrays. Regular `FrameData` and protocol frames are nested integer lists. Do
not assign a string directly into `Sprite.pixels`.

Inspection/conversion:

- `parse_grid_ascii(text_or_rows)` → numeric `np.int8` grid.
- `sprite.to_ascii()` → base pixels as text, preserving `.` and `X`;
  `sprite.to_ascii(rendered=True)` includes transforms.
- `format_sprite_ascii(grid)` → sprite text, preserving `.` and `X`.
- `format_grid_ascii(frame)` → visible color text for rendered 0..15 grids;
  values are clamped to 0..15, so it does not preserve negative sentinels.
- `sprite.color_remap("R", "b")` accepts color symbols; `.` erases and `X`
  creates invisible solid cells.
- `Camera(background="B", letter_box="G")` accepts symbols.

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
  letterboxing, then applies UI overlays. Final output is always 64×64 numeric.
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
- `ACTION6` is a click/place action with display coordinates
  `action.data["x"]`, `action.data["y"]` in `0..63`; use
  `camera.display_to_grid(x, y)` for world coordinates.
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
- `sys_every_pixel`: with `sys_click`, exposes every visible color cell
  (`0..15`); `.` and `X` do not generate click points.
- `sys_place`: marks a place/click target.

## Minimal working game

```python
from arcengine import (
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
- Rendered frames stay numeric; text formatters are only for compact reasoning
  or debugging.
- Tests cover movement, collision, reset, win/loss, and representative renders.
