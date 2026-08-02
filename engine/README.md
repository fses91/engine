# Engine package

The canonical documentation is the repository-level [README](../README.md).

Useful entry points:

- [Compact symbolic grid encoding](../README.md#compact-symbolic-grids)
- [Quick start](../README.md#quick-start)
- [API documentation](../README.md#api-documentation)
- [Architecture overview](OVERVIEW.md)
- [Copy-paste-ready agent prompt](../docs/AGENT_PROMPT.md)

Sprite source uses one character per cell:

```python
from engine import Camera, Sprite

sprite = Sprite(
    [
        ".RR.",
        "RRRR",
        ".RR.",
    ]
)
camera = Camera(background="B", letter_box="G")
```

`WwgGcBMPRbSYOrNp` encodes the 16 ARC colors. `.` is transparent and
passable; `X` is invisible and solid. Game source uses symbols throughout;
storage and protocol conversion are handled inside the engine.

Both `sprite.pixels` and `sprite.render()` return immutable tuples of compact
row strings. Numeric palette indices appear only in generated camera/protocol
frames, such as `game.perform_action(...).frame`.
Use `set_pixel()` or `set_pixels()` when game logic needs to mutate the grid.
