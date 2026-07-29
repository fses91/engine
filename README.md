# Engine

A compact, sprite-based Python engine for ARC-AGI-3 games. Game source uses
one-character color symbols that are easy for humans and small-context agents to
read and write. The engine handles rendering and ARC protocol conversion behind
the symbolic API.

For a short, copy-paste-ready game-authoring context, see
[the Engine agent prompt](docs/AGENT_PROMPT.md).

## Installation from GitHub

This project is not intended to be published on PyPI. Install this repository
directly with its Git URL:

```bash
pip install "engine @ git+https://github.com/arcprize/ARCEngine.git@main"
```

If you host the repository under another account or name, replace that GitHub
URL with your repository URL.

For a private repository or SSH-based access:

```bash
pip install "engine @ git+ssh://git@github.com/arcprize/ARCEngine.git@main"
```

To use it from another project's `pyproject.toml`, add a PEP 508 direct
reference:

```toml
[project]
dependencies = [
    "engine @ git+https://github.com/arcprize/ARCEngine.git@main",
]
```

Then run `pip install .` or `uv sync` in that project. For reproducible builds,
replace `main` with a release tag or commit SHA. With uv, the equivalent
command is:

```bash
uv add "engine @ git+https://github.com/arcprize/ARCEngine.git@main"
```

After installation, import the library as `engine`:

```python
from engine import ARCBaseGame, Camera, Level, Sprite
```

## Compact symbolic grids

Use one character per cell. The 16 ARC colors use this exact ordering and
legend:

```python
ARC_COLOR_CHARS = "WwgGcBMPRbSYOrNp"
ARC_COLOR_LEGEND = (
    "W=white, w=light gray, g=gray, G=dark gray, c=charcoal, B=black, "
    "M=magenta, P=pink, R=red, b=blue, S=sky blue, Y=yellow, O=orange, "
    "r=dark red, N=light green, p=purple"
)
```

Two additional sprite symbols control geometry:

| Symbol | Meaning | Visible | Pixel-perfect collision |
| --- | --- | --- | --- |
| `.` | Empty cell | No | Passable |
| `X` | Invisible wall | No | Solid |

Symbols are case-sensitive: `B` is black while `b` is blue, `P` is pink while
`p` is purple, and `R` is red while `r` is dark red.

The canonical form is a list of row strings:

```python
from engine import Sprite

maze = Sprite(
    pixels=[
        "BBBBBBB",
        "B.....B",
        "B.XXX.B",
        "B.....B",
        "BBBBBBB",
    ],
    name="maze",
)
```

A dedented multiline string is equally valid and is convenient for larger
sprites:

```python
player = Sprite(
    pixels="""
        .RR.
        RRRR
        .RR.
    """,
    name="player",
)
```

Rows must be quoted Python strings—`["WWWggW"]` is valid, while `[WWWggW]`
would refer to an undefined Python variable. Every row must have the same
width. Use symbols—not color numbers—in game source.

Treat storage and protocol conversion as engine internals. The public
game-authoring model is symbolic:

- `Camera(background="B", letter_box="G")` uses color symbols.
- `sprite.color_remap("R", "b")` accepts symbols, including `.` and `X`.
- `sprite.symbols` returns immutable symbolic rows.
- `sprite.to_ascii()` returns the sprite's source grid using color symbols and
  preserves `.`/`X`; `sprite.to_ascii(rendered=True)` includes its current
  transforms.
- `format_grid_ascii(frame)` converts an engine frame to the same compact
  symbolic representation for reasoning or debugging.

## Quick Start

`ARCBaseGame` is the base class for Engine games. Create a game by subclassing it and overriding `step()`:

```python
from engine import ARCBaseGame, ActionInput, Camera, GameAction, Level, Sprite

class MyGame(ARCBaseGame):
    def step(self) -> None:
        # Your game logic here.
        # Call complete_action() when you are done handling the input.
        self.complete_action()

level = Level([Sprite(["R"], name="player")])

# Camera is optional (defaults to 64x64).
game = MyGame(
    game_id="my_game",
    levels=[level],
    camera=Camera(background="B", letter_box="B"),
)

# Multiple frames are returned if the action plays an animation.
frames = game.perform_action(ActionInput(id=GameAction.ACTION1))
```

## API Documentation

### `ARCBaseGame`
Base class for games. Subclass this and implement `step()`.

#### Properties

- `current_level` (Level): The current active level
- `camera` (Camera): The game's camera
- `game_id` (str): The game's identifier (should be set by subclasses)
- `action` (ActionInput): The current action being performed
- `level_index: int` - current level index

#### Methods

##### `__init__(game_id, levels, camera=None, debug=False, win_score=1, available_actions=[1,2,3,4,5,6], seed=0)`
Initialize a new game.

- `game_id`: Game identifier
- `levels`: List of levels to initialize the game with (each level is cloned)
- `camera`: Optional camera to use. If not provided, a default 64x64 camera is created
- `debug`: Enable debug logging
- `available_actions`: List of numeric action IDs
- `seed`: Optional seed value for game logic

Raises `ValueError` if `levels` is empty.

##### `debug(message)`
Print a debug message if debug mode is enabled.

- `message`: Message to print

##### `set_level(index)`
Set the current level by index.

- `index`: The index of the level to set as current
- Raises `IndexError` if index is out of range

##### `set_level_by_name(name)`
Set the current level by name.

- `name`: The level name to match
- Raises `ValueError` if no level matches

##### `perform_action(action_input, raw=False)`
Perform an action and return the resulting frame data.

This method runs `step()` in a loop until `complete_action()` is called, rendering each frame. It should not be overridden; implement game logic in `step()`.

- `action_input`: The action to perform
- `raw`: If True, returns `FrameDataRaw` with numpy frames
- Returns: `FrameData` or `FrameDataRaw`
- Raises `ValueError` if an action exceeds 1000 frames

##### `complete_action()`
Mark the current action as complete. Call this when the provided action is fully resolved.

##### `is_action_complete()`
Check if the current action is complete.

- Returns: True if the action is complete, False otherwise

##### `win()`
Call this when the player has beaten the game.

##### `lose()`
Call this when the player has lost the game.

##### `handle_reset()`
Handle RESET actions, choosing between `level_reset()` and `full_reset()` based on action count and `ONLY_RESET_LEVELS`.

##### `full_reset()`
Reset the entire game back to its initial state.

##### `level_reset()`
Reset only the current level back to its initial state.

##### `step()`
Step the game. This is where your game logic should be implemented.

REQUIRED: Call `complete_action()` when the action is complete. It does not need to be called every step, but once the action is complete. The engine will keep calling `step()` and rendering frames until the action is complete.

##### `try_move(sprite_name, dx, dy)`
Try to move a sprite and return a list of sprites it collides with.

This method attempts to move the sprite by the given deltas and checks for collisions. If any collisions are detected, the sprite is not moved and the method returns a list of collided sprites.

- `sprite_name`: The name of the sprite to move
- `dx`: The change in x position (positive = right, negative = left)
- `dy`: The change in y position (positive = down, negative = up)
- Returns: A list of sprites collided with. If no collisions occur, the sprite is moved and an empty list is returned
- Raises `ValueError` if no sprite with the given name is found

Example (`try_move`):

```python
# Try to move a sprite right by 1 pixel
collisions = game.try_move("player", 1, 0)
if not collisions:
    print("Move successful!")
else:
    print(f"Collided with: {[sprite.name for sprite in collisions]}")
```

##### `try_move_sprite(sprite, dx, dy)`
Try to move a specific sprite and return a list of sprites it collides with.

- `sprite`: The sprite to move
- `dx`: The change in x position (positive = right, negative = left)
- `dy`: The change in y position (positive = down, negative = up)
- Returns: A list of sprites collided with. If no collisions occur, the sprite is moved and an empty list is returned

##### `next_level()`
Advance to the next level or mark the game as won if the last level is complete.

##### `on_set_level(level)`
Hook called when the level is set. Override to apply level-specific setup.

- `level`: The level being set

##### `get_pixels_at_sprite(sprite)`
Get the camera pixels at a sprite's location.

- `sprite`: The sprite to sample
- Returns: A numpy array of pixels covering the sprite's area

##### `get_pixels(x, y, width, height)`
Get the camera pixels at a given position.

- `x`, `y`: Top-left position in camera space
- `width`, `height`: Dimensions of the sample area
- Returns: A numpy array of pixels for the given region

#### Notes

- `perform_action` runs `step()` in a loop until `complete_action()` is called. It raises
  `ValueError` if an action exceeds 1000 frames.


## API

The public API is exported from `engine.__init__`:

Import necessary components from engine:

```python
from engine import (
    ARC_COLOR_CHARS,
    ARC_COLOR_LEGEND,
    ARCBaseGame,
    Camera,
    Level,
    Sprite,
    format_grid_ascii,
)
```

#### `GameAction`
Enum of available actions with attached data model types.

- `RESET` (id 0) uses `SimpleAction`.
- `ACTION1`-`ACTION5` and `ACTION7` use `SimpleAction`.
- `ACTION6` uses `ComplexAction` to encode screen coordinates `x` and `y` (0,0 is the top left pixel). Used for click inputs

Common client/UI conventions:
- `ACTION1`: Up or W or 1
- `ACTION2`: Down or S or 2
- `ACTION3`: Left or A or 3
- `ACTION4`: Right or D or 4
- `ACTION5`: Spacebar
- `ACTION7`: Z - Used for Undo

### Grid encoding helpers

#### `format_grid_ascii(grid)`

Convert a rendered engine frame to newline-delimited color symbols. An empty
grid is rendered as `(empty grid)`.

### `Sprite`
A 2D sprite with position, rotation, scale, and collision behavior.

```python
from engine import Sprite, BlockingMode, InteractionMode

# Create a simple 2x2 sprite
sprite_simple = Sprite([
    "wg",
    "Gc",
])

# Create a sprite with custom properties
sprite_custom = Sprite(
    pixels=[
        ".RR.",
        "RRRR",
        ".RR.",
    ],
    name="player",
    x=10,
    y=20,
    layer=1,
    scale=2,
    rotation=90,
    mirror_ud=False,
    mirror_lr=False,
    blocking=BlockingMode.PIXEL_PERFECT,
    interaction=InteractionMode.TANGIBLE,
    # If interaction is None, visible/collidable determine the mode.
    # visible=True, collidable=True are the defaults.
    tags=["player"],
)
```

#### Notes

- Sprite grids use symbolic row strings. `.` is empty and passable; `X` is
  invisible and solid. Neither is drawn, but only `.` is a hole for
  pixel-perfect collision.

- Rotation is limited to `0`, `90`, `180`, `270` degrees.
- `scale`:
  - Positive values upscale (2 = double size, 3 = triple size).
  - Negative values downscale by a divisor: `-1` => divide by 2, `-2` => divide by 3, etc.
  - `0` is invalid and raises `ValueError`.
- If `interaction` is `None`, `visible` and `collidable` determine the interaction mode.

#### Properties

- `name: str`
- `x: int`, `y: int`
- `layer: int`
- `scale: int`
- `rotation: int`
- `blocking: BlockingMode`
- `symbols: tuple[str, ...]`
- `interaction: InteractionMode`
- `tags: list[str]`
- `mirror_ud: bool`, `mirror_lr: bool`
- `is_visible: bool`
- `is_collidable: bool`
- `width: int`, `height: int` (based on rendered size)

#### Methods

##### `__init__(pixels, name=None, x=0, y=0, layer=0, scale=1, rotation=0, mirror_ud=False, mirror_lr=False, blocking=BlockingMode.PIXEL_PERFECT, interaction=None, visible=True, collidable=True, tags=[])`
Initialize a new Sprite.

- `pixels`: Symbolic `list[str]` or a dedented multiline grid string
- `name`: Optional sprite name (default: generates UUID)
- `x`: X coordinate in pixels (default: 0)
- `y`: Y coordinate in pixels (default: 0)
- `layer`: Z-order layer for rendering (default: 0, higher values render on top)
- `scale`: Scale factor (default: 1)
- `rotation`: Rotation in degrees (default: 0)
- `mirror_ud`, `mirror_lr`: Optional vertical/horizontal mirroring
- `blocking`: Collision detection method (default: PIXEL_PERFECT)
- `interaction`: Optional interaction mode override. If `None`, `visible`/`collidable` determine the mode
- `visible`, `collidable`: Used only when `interaction` is `None`
- `tags`: Optional list of string tags

Raises `ValueError` if scale is 0, pixels is not a 2D list/array, rotation is invalid,
or if downscaling factor doesn't evenly divide sprite dimensions.

##### `clone(new_name=None)`
Create an independent copy of this sprite.

- `new_name`: Optional name for the cloned sprite (default: reuses current name)
- Returns: A new Sprite instance with the same properties but independent state

##### `set_position(x, y)`
Set the sprite's position.

- `x`: New X coordinate in pixels
- `y`: New Y coordinate in pixels

##### `move(dx, dy)`
Move the sprite by the given deltas.

- `dx`: Change in x position (positive = right, negative = left)
- `dy`: Change in y position (positive = down, negative = up)

##### `set_scale(scale)`
Set the sprite's scale factor.

- `scale`: The new scale factor:
  * Positive values scale up (2 = double size, 3 = triple size)
  * Negative values scale down (-1 = half size, -2 = one-third size, -3 = one-fourth size)
  * Zero is invalid
- Raises `ValueError` if scale is 0 or if downscaling factor doesn't evenly divide sprite dimensions

For example:
```python
sprite = Sprite(["wg", "Gc"])

# Upscaling examples
sprite.set_scale(2)  # Doubles size in both dimensions
sprite.set_scale(3)  # Triples size in both dimensions

# Downscaling examples
sprite.set_scale(-1)  # Half size (divide dimensions by 2)
sprite.set_scale(-2)  # One-third size (divide dimensions by 3)
sprite.set_scale(-3)  # One-fourth size (divide dimensions by 4)
```

##### `adjust_scale(delta)`
Adjust the sprite's scale by a delta value, moving one step at a time.

The method will adjust the scale by incrementing or decrementing by 1 repeatedly until reaching the target scale. This ensures smooth transitions and validates each step.

Negative scales indicate downscaling factors:
- scale = -1: half size (divide by 2)
- scale = -2: one-third size (divide by 3)
- scale = -3: one-fourth size (divide by 4)

Examples:
- Current scale 1, delta +2 -> Steps through: 1 -> 2 -> 3
- Current scale 1, delta -2 -> Steps through: 1 -> 0 -> -1 (half size)
- Current scale -2, delta +3 -> Steps through: -2 -> -1 -> 0 -> 1

Raises `ValueError` if any intermediate scale would be 0 or if a downscaling factor doesn't evenly divide sprite dimensions.

##### `set_rotation(rotation)`
Set the sprite's rotation to a specific value.

- `rotation`: The new rotation in degrees (must be 0, 90, 180, or 270)
- Raises `ValueError` if rotation is not a valid 90-degree increment

##### `rotate(delta)`
Rotate the sprite by a given amount.

- `delta`: The change in rotation in degrees (must result in a valid rotation)
- Raises `ValueError` if resulting rotation is not a valid 90-degree increment

##### `set_blocking(blocking)`
Set the sprite's blocking behavior.

- `blocking`: The new blocking behavior (BlockingMode enum value)
- Raises `ValueError` if blocking is not a BlockingMode enum value

##### `set_interaction(interaction)`
Set the sprite's interaction mode.

- `interaction`: The new interaction mode (InteractionMode enum value)
- Raises `ValueError` if interaction is not an InteractionMode enum value

##### `set_visible(visible)`
Set the sprite's visibility.

- `visible`: The new visibility state

##### `set_collidable(collidable)`
Set the sprite's collidable state.

- `collidable`: The new collidable state

##### `set_layer(layer)`
Set the sprite's rendering layer.

- `layer`: New layer value. Higher values render on top.

##### `set_mirror_ud(mirror_ud)`
Set the sprite's mirror up/down state.

- `mirror_ud`: True to flip vertically

##### `set_mirror_lr(mirror_lr)`
Set the sprite's mirror left/right state.

- `mirror_lr`: True to flip horizontally

##### `set_name(name)`
Set the sprite's name.

- `name`: New name for the sprite
- Raises `ValueError` if name is empty

##### `render()`
Render the sprite with current scale and rotation.

- Returns: The engine render grid
- Raises `ValueError` if downscaling factor doesn't evenly divide the sprite dimensions

##### `to_ascii(rendered=False)`
Format the sprite as a symbolic grid. By default it formats the source grid;
pass `rendered=True` to include rotation, mirroring, and scale.

- Returns: A newline-delimited string with one character per cell

##### `collides_with(other, ignoreMode=False)`
Check if this sprite collides with another sprite.

The collision check follows these rules:
1. A sprite cannot collide with itself
2. Non-collidable sprites (based on interaction mode) never collide (unless `ignoreMode=True`)
3. For collidable sprites, the collision detection method is based on their blocking mode:
   - NOT_BLOCKED: Always returns False
   - BOUNDING_BOX: Simple rectangular collision check
   - PIXEL_PERFECT: Precise pixel-level collision detection

- `other`: The other sprite to check collision with
- `ignoreMode`: If True, bypasses interaction and blocking checks
- Returns: True if the sprites collide, False otherwise

##### `color_remap(old_color, new_color)`
Remap the sprite's color.

- `old_color`: The old color symbol, or `None` to remap every visible color
- `new_color`: The new color symbol; `.` erases matching pixels and `X` makes
  them invisible but solid

```python
sprite.color_remap("R", "b")
```

##### `merge(other)`
Merge two sprites together.

This method creates a new sprite that combines the pixels of both sprites.
Only `.` cells are holes during merging; visible colors and invisible-solid
`X` cells participate, with the receiver's cells taking precedence on overlap.

- `other`: The other sprite to merge with
- Returns: A new Sprite instance containing the merged pixels

### BlockingMode

An enumeration defining different collision detection behaviors for sprites:

- `NOT_BLOCKED`: No collision detection
- `BOUNDING_BOX`: Collision detection using the sprite's bounding box
- `PIXEL_PERFECT`: Collision detection using pixel-perfect testing

### InteractionMode

An enumeration defining how a sprite interacts with the game world:

- `TANGIBLE`: Visible and can be collided with
- `INTANGIBLE`: Visible but cannot be collided with (ghost-like)
- `INVISIBLE`: Not visible but can be collided with (invisible wall)
- `REMOVED`: Not visible and cannot be collided with (effectively removed)

### `Camera`
Defines the viewport and renders sprites to a 64x64 output.

```python
from engine import Camera

# Create a default camera (64x64 viewport)
camera = Camera()

# Create a custom camera
camera = Camera(
    x=10,                    # X position in pixels
    y=20,                    # Y position in pixels
    width=32,                # Viewport width (max 64)
    height=32,               # Viewport height (max 64)
    background="w",          # Light gray
    letter_box="g",          # Gray
    interfaces=[],           # Optional list of renderable interfaces
)
```

#### Notes

- Output is always 64x64. The camera view is uniformly upscaled (nearest neighbor) and
  letterboxed with `letter_box` color as needed.
- The scale factor is `min(64 // width, 64 // height)`.
- `interfaces` is an optional list of `RenderableUserDisplay` overlays.

#### Properties

- `x: int`, `y: int`
- `width: int`, `height: int` (max 64)
- `background`, `letter_box`: ARC color symbols

#### Methods

##### `__init__(x=0, y=0, width=64, height=64, background="B", letter_box="B", interfaces=[])`

Initialize a new Camera.

Args:
- `x` (int): X coordinate in pixels (default: 0)
- `y` (int): Y coordinate in pixels (default: 0)
- `width` (int): Viewport width in pixels (default: 64, max: 64)
- `height` (int): Viewport height in pixels (default: 64, max: 64)
- `background` (str): Background color symbol (default: `"B"` - black)
- `letter_box` (str): Letter-box color symbol (default: `"B"` - black)
- `interfaces` (list[RenderableUserDisplay]): Optional list of renderable interfaces to initialize with

Raises:
- `ValueError`: If width or height exceed 64 pixels or are negative

##### `move(dx, dy)`
Move the camera by the specified delta.

- `dx`: Change in x position
- `dy`: Change in y position

##### `resize(width, height)`
Resize the camera viewport.

- `width`, `height`: New dimensions (max 64)

##### `render(sprites)`
Render the camera view.

The rendered output is always 64x64 pixels. If the camera's viewport is smaller, the view is scaled up uniformly (nearest neighbor) to fit within 64x64, and the remaining space is filled with the letter_box color.

Args:
- `sprites` (list[Sprite]): List of sprites to render

Returns:
- `np.ndarray`: The rendered view as a 64x64 numpy array

##### `replace_interface(new_interfaces)`
Replace the current interfaces with new ones. This method replaces all current interfaces with the provided ones and stores them as-is (no cloning).

Args:
- `new_interfaces` (list[RenderableUserDisplay]): List of new interfaces to use. These should be cloned before passing them in.

##### `display_to_grid(display_x, display_y)`
Convert display coordinates (64x64) to camera grid coordinates.

- `display_x`, `display_y`: Display-space coordinates (0-63)
- Returns: `(x, y)` grid coordinates, or `None` if the point lies in the letterbox area

### `RenderableUserDisplay`
The `RenderableUserDisplay` class is an abstract base class that defines the interface for UI elements that can be rendered by the camera. It is used as the final step in the camera's rendering pipeline to produce the 64x64 output frame.

```python
import numpy as np
from engine import RenderableUserDisplay, Sprite

class MyUI(RenderableUserDisplay):
    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        # Modify the frame in-place and return it
        return frame
```

#### Methods

##### `render_interface(frame)`
Render this UI element onto the given frame.

- `frame`: The 64x64 numpy array to render onto
- Returns: The modified frame (implementations should modify in-place)

##### `draw_sprite(frame, sprite, start_x, start_y)`
Helper to draw a sprite onto a frame with clipping.

- `frame`: The 64x64 numpy array to draw onto
- `sprite`: The sprite to draw
- `start_x`, `start_y`: Top-left position in frame coordinates
- Returns: The modified frame

### ToggleableUserDisplay

The `ToggleableUserDisplay` class is an example implementation of `RenderableUserDisplay` that manages a collection of sprite pairs (enabled/disabled states) and provides methods to toggle between them.

```python
from engine import ToggleableUserDisplay, Sprite

# Create a toggleable UI element with sprite pairs
ui_element = ToggleableUserDisplay([
    (enabled_sprite1, disabled_sprite1),
    (enabled_sprite2, disabled_sprite2)
])

# Enable/disable specific sprite pairs
ui_element.enable(0)  # Enable first pair
ui_element.disable(1)  # Disable second pair

# Check if a pair is enabled
is_enabled = ui_element.is_enabled(0)

```
#### Methods

##### `__init__(sprite_pairs)`
Initialize a new ToggleableUserDisplay.

- `sprite_pairs`: List of `(enabled_sprite, disabled_sprite)` tuples. Each sprite is cloned.

##### `clone()`
Create a deep copy of this UI element.

- Returns: A new ToggleableUserDisplay instance with cloned sprite pairs

##### `is_enabled(index)`
Check if a sprite pair is enabled.

- `index`: Index of the sprite pair to check
- Returns: True if the pair is enabled, False otherwise
- Raises `ValueError` if index is out of range

##### `enable(index)`
Enable a sprite pair.

- `index`: Index of the sprite pair to enable
- Raises `ValueError` if index is out of range

##### `disable(index)`
Disable a sprite pair.

- `index`: Index of the sprite pair to disable
- Raises `ValueError` if index is out of range

##### `enable_all_by_tag(tag)`
Enable all sprite pairs that have the given tag.

- `tag`: Tag to search for

##### `disabled_all_by_tag(tag)`
Disable all sprite pairs that have the given tag.

- `tag`: Tag to search for

##### `enable_first_by_tag(tag)`
Enable the first disabled sprite pair with the given tag.

- `tag`: Tag to search for
- Returns: True if a pair was enabled, False otherwise

##### `disabled_first_by_tag(tag)`
Disable the first enabled sprite pair with the given tag.

- `tag`: Tag to search for
- Returns: True if a pair was disabled, False otherwise

##### `render_interface(frame)`
Render the UI element onto the given frame.

- `frame`: The 64x64 numpy array to render onto

This method renders all sprite pairs, using the enabled sprite if the pair is enabled, and the disabled sprite if the pair is disabled.

### `Level`
Manages a collection of sprites and level metadata.

```python
from engine import Level, Sprite, PlaceableArea

sprites = [
    Sprite(["R"], name="player"),
    Sprite(["b"], name="enemy"),
]

# Create an empty level
level_empty = Level()

# Create a level with initial sprites
level = Level(
    sprites=sprites,
    grid_size=(16, 16),
    data={"difficulty": "easy"},
    name="level_1",
)
```

#### Properties

- `name: str`
- `grid_size: tuple[int, int] | None`

#### Methods

##### `__init__(sprites=None, grid_size=None, data={}, name="Level", placeable_areas=None)`
Initialize a new Level.

- `sprites`: Optional list of sprites to initialize the level with
- `grid_size`: Optional `(width, height)` tuple for grid sizing
- `data`: Optional metadata dictionary
- `name`: Level name

##### `add_sprite(sprite)`
Add a sprite to the level.

- `sprite`: The sprite to add

##### `remove_sprite(sprite)`
Remove a sprite from the level.

- `sprite`: The sprite to remove

##### `remove_all_sprites()`
Remove all sprites from the level.

##### `get_sprites()`
Get all sprites in the level.

- Returns: A copy of the sprite list

##### `get_sprites_by_name(name)`
Get all sprites with the given name.

- `name`: The name to search for
- Returns: List of sprites with the given name

##### `get_sprites_by_tag(tag)`
Get all sprites that have the given tag.

- `tag`: The tag to search for
- Returns: List of sprites that have the tag

##### `get_sprites_by_tags(tags)`
Get all sprites that have all of the given tags (AND).

- `tags`: Tags to search for
- Returns: List of sprites with all tags

##### `get_sprites_by_any_tag(tags)`
Get all sprites that have any of the specified tags (OR).

- `tags`: Tags to search for
- Returns: List of sprites that have any tag

##### `get_all_tags()`
Get all unique tags from all sprites in the level.

- Returns: A set of tag strings

##### `get_sprite_at(x, y, tag=None, ignore_collidable=False)`
Get the top-most sprite at the given coordinates.

- `x`, `y`: Coordinates to search
- `tag`: Optional tag filter
- `ignore_collidable`: If True, includes non-collidable sprites
- Returns: The first matching sprite or `None`

##### `collides_with(sprite, ignoreMode=False)`
Return all sprites in the level that collide with the given sprite.

- `sprite`: The sprite to check for collisions
- `ignoreMode`: If True, bypasses interaction/blocking checks

##### `get_data(key)`
Get metadata by key.

- Returns: The stored value or `None`

##### `clone()`
Create a deep copy of this level.

- Returns: A new `Level` instance with cloned sprites

## Development

To set up the development environment:

1. Clone the repository:
   ```bash
   git clone git@github.com:arcprize/ARCEngine.git
   cd ARCEngine
   ```

2. Create and activate a virtual environment using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   uv sync
   ```

4. Install git hooks:
   ```bash
   pre-commit install
   ```

This repo uses `ruff` to lint/format and `mypy` for type checking:

```bash
pre-commit run --all-files
```

Note: by default these tools run automatically before `git commit`. It's also recommended
to set up `ruff` inside your IDE (https://docs.astral.sh/ruff/editors/setup/).

## Contributions

This project does not accept external contributions.

## Citation

If you use this project in your research, please cite it as:

```bibtex
@software{arc_agi,
  author       = {ARC Prize Foundation},
  title        = {ARC Game Engine},
  year         = {2026},
  url          = {https://github.com/arcprize/ARCEngine},
  version      = {0.9.3}
}
```

## License

MIT License

Copyright (c) 2026 ARC Prize Foundation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
