# ARCEngine package

The canonical documentation is the repository-level [README](../README.md).

Useful entry points:

- [Compact symbolic grid encoding](../README.md#compact-symbolic-grids)
- [Quick start](../README.md#quick-start)
- [API documentation](../README.md#api-documentation)
- [Architecture overview](OVERVIEW.md)
- [Copy-paste-ready agent prompt](../docs/AGENT_PROMPT.md)

Sprite source uses one character per cell:

```python
from arcengine import Camera, Sprite

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
passable; `X` is invisible and solid. Numeric sprite grids remain compatible,
and all runtime rendering and protocol output remain numeric.
