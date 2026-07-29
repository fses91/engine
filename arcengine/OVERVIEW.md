# ARCEngine overview

ARCEngine is a turn-based, sprite-oriented game engine for ARC-AGI-3. It keeps
game source spatial and compact for human or agent authors while preserving the
numeric grids expected by NumPy, rendering, and the ARC protocol.

## Design goals

The engine supplies the common structure:

- a 64×64, 16-color output frame;
- a small discrete action vocabulary;
- turn-based updates—time advances only while resolving an input;
- one or more rendered frames per input;
- sprites, levels, collision detection, camera composition, and UI overlays.

Games supply their own mechanics in `ARCBaseGame.step()`.

## Symbolic authoring, numeric runtime

Authored sprite grids use one character per cell:

```text
WwgGcBMPRbSYOrNp  16 visible ARC colors, indices 0..15
.                 transparent and passable, value -1
X                 invisible and solid, value -2
```

The symbol case is significant. A grid such as:

```python
Sprite(
    [
        "BBBBB",
        "B...B",
        "B.X.B",
        "BBBBB",
    ]
)
```

is decoded to an `np.int8` array at construction. The rest of the engine stays
numeric:

```text
symbolic source
    → parse_grid_ascii
    → Sprite.pixels (np.int8)
    → rotate / mirror / scale / compose
    → Camera.render() (64×64 np.int8)
    → FrameData / ARC protocol (numeric)
```

This boundary is intentional: strings reduce source and prompt size, while
numeric arrays keep rendering, collision, and wire behavior unchanged. Legacy
numeric sprite grids remain accepted.

Use `Sprite.to_ascii()` or `format_sprite_ascii()` when inspecting base sprite
data because both preserve `.` and `X`. Use `format_grid_ascii()` for rendered
0..15 grids; it clamps values to the visible palette. `parse_grid_ascii()` is
the inverse authoring helper.

## Sprites and collision

A sprite owns base pixels plus a world position, layer, transform, blocking
mode, interaction mode, name, and tags.

Rendering applies rotation, mirroring, and scaling to the numeric base grid.
Lower layers render first, so higher layers appear on top. Both `.` and `X` are
invisible.

Pixel-perfect collision has deliberately different sentinel behavior:

- `.` is a true hole: invisible and non-colliding.
- `X` is an invisible solid cell.
- every visible color cell is solid.

`BlockingMode.BOUNDING_BOX` ignores per-cell holes.
`BlockingMode.NOT_BLOCKED` disables collision. `InteractionMode` independently
controls whether a whole sprite is visible and/or collidable:

- `TANGIBLE`: visible and collidable;
- `INTANGIBLE`: visible and non-collidable;
- `INVISIBLE`: hidden and collidable;
- `REMOVED`: hidden and non-collidable.

`ARCBaseGame.try_move()` and `try_move_sprite()` apply a tentative move and
restore the original position when any collision is found.

## Main game loop

`ARCBaseGame.perform_action()` owns the loop and must not be overridden:

```text
handle RESET if requested
set current action
while action is incomplete:
    apply a pending level transition, or call step()
    render and append one frame
return all frames and game state
```

Every `step()` implementation must eventually call `complete_action()`.
Changing state across several calls before completion creates a multi-frame
animation. An action is limited to 1000 frames.

`next_level()` increments the completed-level score. If another level exists,
the transition occurs on the following loop iteration; otherwise the game
enters `WIN`. `lose()` enters `GAME_OVER`.

RESET normally performs a full reset before play has begun and a current-level
reset after actions have been taken. The `ONLY_RESET_LEVELS=true` environment
setting forces level-only resets except after a win.

Levels and sprites are cloned when a game is created or reset. A game that
keeps sprite references should rebind them in `on_set_level(level)` by name or
tag.

## Render loop

1. `Camera._raw_render()` creates a camera-sized numeric background and draws
   visible sprites from low to high layer.
2. `Camera.render()` uniformly upscales the view with nearest-neighbor repeats,
   centers it in a 64×64 letter-boxed frame, and applies UI interfaces.
3. `perform_action(raw=False)` serializes the numeric array as nested integer
   lists. `raw=True` keeps NumPy arrays in `FrameDataRaw`.

Camera background and letter-box colors accept symbols such as `"B"` or legacy
indices. Camera dimensions determine integer scaling:

- 32×32 scales 2× and fills the frame;
- 30×30 scales 2× with a 2-pixel border;
- 30×15 scales 2× with horizontal and vertical letterboxing;
- 15×15 scales 4× with a 2-pixel border.

UI implementations receive the final numeric 64×64 frame. They can use
`RenderableUserDisplay.draw_sprite()` to compose symbolic-authored sprites
without converting the frame to text.

## Actions

- `RESET` (`0`) resets the game or level.
- `ACTION1`–`ACTION5` and `ACTION7` contain no coordinates.
- `ACTION6` contains display coordinates `x` and `y` in `0..63`.

Common controls map ACTION1–4 to up, down, left, and right; ACTION5 to a primary
button; ACTION6 to click/place; and ACTION7 to undo. A game declares the action
IDs it exposes with `available_actions`.

## Example games

- [Simple Maze](../examples/simple_maze.py): pixel-perfect movement and walls.
- [Merge](../examples/merge.py): collision and sprite merging.
- [Complex Maze](../examples/complex_maze.py): additional mechanics and a
  `ToggleableUserDisplay`.
- [Merge/Detach](../examples/merge_detach.py): custom UI and detachable merged
  sprites.

For an agent-sized operational reference and minimal game skeleton, use
[docs/AGENT_PROMPT.md](../docs/AGENT_PROMPT.md).
