"""Compact symbolic encoding for ARC palette grids."""

from __future__ import annotations

from collections.abc import Sequence
from textwrap import dedent
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

ARC_COLOR_CHARS = "WwgGcBMPRbSYOrNp"
ARC_COLOR_LEGEND = "W=white, w=light gray, g=gray, G=dark gray, c=charcoal, B=black, M=magenta, P=pink, R=red, b=blue, S=sky blue, Y=yellow, O=orange, r=dark red, N=light green, p=purple"

# Sprite-only cells. ARC output frames contain colors 0..15 and never contain
# either of these negative internal values.
ARC_TRANSPARENT_CHAR = "."
ARC_INVISIBLE_BLOCKING_CHAR = "X"
ARC_SPRITE_LEGEND = f"{ARC_COLOR_LEGEND}, .=transparent/passable, X=transparent/solid"

ColorLike: TypeAlias = int | str
AsciiGrid: TypeAlias = str | Sequence[str] | Sequence[Sequence[str]]
NumericGrid: TypeAlias = Sequence[Sequence[int]] | NDArray[Any]

_COLOR_TO_INDEX = {char: index for index, char in enumerate(ARC_COLOR_CHARS)}
_SPECIAL_TO_INDEX = {
    ARC_TRANSPARENT_CHAR: -1,
    ARC_INVISIBLE_BLOCKING_CHAR: -2,
}


def color_to_index(color: ColorLike, *, allow_special: bool = False) -> int:
    """Convert one color symbol to its numeric palette index.

    Integer inputs are returned as integers for compatibility with the original
    numeric API. ``.`` and ``X`` are accepted only when ``allow_special=True``.
    """

    if not isinstance(color, str):
        try:
            return int(color)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"Color must be an integer or one-character symbol, got {color!r}") from exc

    if len(color) != 1:
        raise ValueError(f"Color symbol must be exactly one character, got {color!r}")

    index = _COLOR_TO_INDEX.get(color)
    if index is not None:
        return index

    if allow_special and color in _SPECIAL_TO_INDEX:
        return _SPECIAL_TO_INDEX[color]

    expected = ARC_COLOR_CHARS + (ARC_TRANSPARENT_CHAR + ARC_INVISIBLE_BLOCKING_CHAR if allow_special else "")
    raise ValueError(f"Unknown color symbol {color!r}; expected one of {expected!r}")


def _ascii_rows(grid: AsciiGrid) -> list[str]:
    """Normalize supported ASCII-grid inputs to a list of rows."""

    if isinstance(grid, str):
        text = dedent(grid)
        rows = text.splitlines()
        while rows and not rows[0].strip():
            rows.pop(0)
        while rows and not rows[-1].strip():
            rows.pop()
    else:
        raw_rows = list(grid)
        rows = []
        for row_number, row in enumerate(raw_rows, start=1):
            if isinstance(row, str):
                rows.append(row)
                continue
            try:
                cells = list(row)
            except TypeError as exc:
                raise TypeError(f"ASCII grid row {row_number} must be a string or a sequence of symbols") from exc
            if not all(isinstance(cell, str) and len(cell) == 1 for cell in cells):
                raise ValueError(f"ASCII grid row {row_number} must contain only one-character symbols")
            rows.append("".join(cells))

    if not rows:
        raise ValueError("ASCII grid cannot be empty")

    width = len(rows[0])
    if width == 0:
        raise ValueError("ASCII grid rows cannot be empty")

    for row_number, row in enumerate(rows, start=1):
        if len(row) != width:
            raise ValueError(f"ASCII grid rows must have equal length: row {row_number} has width {len(row)}, expected {width}")

    return rows


def parse_grid_ascii(grid: AsciiGrid) -> NDArray[np.int8]:
    """Decode compact symbolic sprite rows to a 2-D ``np.int8`` array.

    The 16 ARC color symbols map to palette indices 0..15. Sprite-only ``.``
    maps to -1 (transparent/passable) and ``X`` maps to -2
    (transparent/solid).
    """

    rows = _ascii_rows(grid)
    decoded: list[list[int]] = []

    for row_number, row in enumerate(rows, start=1):
        decoded_row: list[int] = []
        for column_number, char in enumerate(row, start=1):
            try:
                decoded_row.append(color_to_index(char, allow_special=True))
            except ValueError as exc:
                raise ValueError(f"Unknown pixel symbol {char!r} at row {row_number}, column {column_number}") from exc
        decoded.append(decoded_row)

    return np.asarray(decoded, dtype=np.int8)


def _validate_grid_array(grid: NumericGrid) -> None:
    if isinstance(grid, np.ndarray) and grid.ndim != 2:
        raise ValueError(f"Grid must be two-dimensional, got {grid.ndim} dimensions")


def format_grid_ascii(grid: NumericGrid) -> str:
    """Format a rendered numeric ARC grid using the compact 16-color alphabet.

    Values are clamped to 0..15, matching the ARC observation formatter. Use
    :func:`format_sprite_ascii` when negative sprite cells must round-trip.
    """

    _validate_grid_array(grid)
    if len(grid) == 0:
        return "(empty grid)"

    lines = []
    for row in grid:
        chars = []
        for value in row:
            chars.append(ARC_COLOR_CHARS[max(0, min(15, int(value)))])
        lines.append("".join(chars))
    return "\n".join(lines)


def format_sprite_ascii(grid: NumericGrid) -> str:
    """Format numeric sprite pixels, preserving both negative cell semantics."""

    _validate_grid_array(grid)
    if len(grid) == 0:
        return "(empty grid)"

    lines = []
    for row in grid:
        chars = []
        for value in row:
            index = int(value)
            if index == -1:
                chars.append(ARC_TRANSPARENT_CHAR)
            elif index < -1:
                chars.append(ARC_INVISIBLE_BLOCKING_CHAR)
            else:
                chars.append(ARC_COLOR_CHARS[max(0, min(15, index))])
        lines.append("".join(chars))
    return "\n".join(lines)


__all__ = [
    "ARC_COLOR_CHARS",
    "ARC_COLOR_LEGEND",
    "ARC_TRANSPARENT_CHAR",
    "ARC_INVISIBLE_BLOCKING_CHAR",
    "ARC_SPRITE_LEGEND",
    "AsciiGrid",
    "ColorLike",
    "NumericGrid",
    "color_to_index",
    "parse_grid_ascii",
    "format_grid_ascii",
    "format_sprite_ascii",
]
