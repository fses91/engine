"""
Module for level-related functionality in the Engine.
"""

import copy
from typing import Any, List, Optional, Tuple

from .enums import BlockingMode, PlaceableArea
from .sprites import Sprite


class Level:
    """A level that manages a collection of sprites."""

    _sprites: List[Sprite]
    _grid_size: Tuple[int, int] | None
    _data: dict[str, Any]
    _name: str
    _placeable_areas: List[PlaceableArea]

    def __init__(
        self,
        sprites: Optional[List[Sprite]] = None,
        grid_size: Tuple[int, int] | None = None,
        data: dict[str, Any] = {},
        name: str = "Level",
        placeable_areas: Optional[List[PlaceableArea]] = None,
    ):
        """Initialize a new level.

        Args:
            sprites: List of sprites to add to the level
            grid_size: Tuple of width and height of the grid
            data: Dictionary of data to store in the level
            name: Name of the level
            placeable_areas: List of placeable areas in the level
        """
        self._sprites = []
        self._grid_size = grid_size
        self._data = data
        self._name = name
        self._placeable_areas = placeable_areas if placeable_areas is not None else []
        if sprites:
            # Add first (fast path), then do one-time merge+sort.
            self._sprites.extend(sprites)
            self._merge_sys_static_pixel_perfect_on_init()

    def _merge_sys_static_pixel_perfect_on_init(self) -> None:
        """
        Merge any sprites that are:
          - PIXEL_PERFECT
          - have tag "sys_static"
        into ONE sprite per layer.

        This runs only during construction.
        """
        if not self._sprites:
            return

        # Partition sprites into merge-candidates (by layer) and others.
        by_layer: dict[int, List[Sprite]] = {}
        others: List[Sprite] = []

        for s in self._sprites:
            if s.blocking == BlockingMode.PIXEL_PERFECT and "sys_static" in s.tags:
                by_layer.setdefault(s.layer, []).append(s)
            else:
                others.append(s)

        merged: List[Sprite] = []
        for layer, group in by_layer.items():
            if not group:
                continue
            if len(group) == 1:
                merged.append(group[0])
                continue

            # Merge left-to-right; merge() returns a NEW Sprite each time.
            base = group[0]
            for nxt in group[1:]:
                base = base.merge(nxt)

            # Ensure the merged sprite stays on this layer.
            # (merge() uses max layer, but all are same layer anyway; set explicitly for safety.)
            base.set_layer(layer)

            # Ensure sys_static remains (merge unions tags, so it should already be present)
            if "sys_static" not in base.tags:
                base.tags.append("sys_static")

            merged.append(base)

        self._sprites = others + merged

    def remove_all_sprites(self) -> None:
        """Remove all sprites from the level."""
        self._sprites = []

    def add_sprite(self, sprite: Sprite) -> None:
        """Add a sprite to the level.

        Args:
            sprite: The sprite to add
        """
        self._sprites.append(sprite)

    def remove_sprite(self, sprite: Sprite) -> None:
        """Remove a sprite from the level.

        Args:
            sprite: The sprite to remove
        """
        if sprite in self._sprites:
            self._sprites.remove(sprite)

    def get_sprites(self) -> List[Sprite]:
        """Get all sprites in the level.

        Returns:
            List[Sprite]: All sprites in the level
        """
        return self._sprites.copy()  # Return copy to prevent external modification

    def get_sprites_by_name(self, name: str) -> List[Sprite]:
        """Get all sprites with the given name.

        Args:
            name: The name to search for

        Returns:
            List[Sprite]: All sprites with the given name
        """
        return [s for s in self._sprites if s.name == name]

    def require_sprite(self, name: str) -> Sprite:
        """Return the single sprite with the given name.

        This method is intended for game logic that requires an unambiguous
        entity reference. Use :meth:`get_sprites_by_name` when duplicate names
        are expected.

        Args:
            name: The exact sprite name to find.

        Returns:
            The uniquely named sprite.

        Raises:
            ValueError: If no sprite or multiple sprites have the given name.
        """
        sprites = self.get_sprites_by_name(name)
        if len(sprites) != 1:
            raise ValueError(f"Expected exactly one sprite named {name!r}, found {len(sprites)}")
        return sprites[0]

    def replace_sprite(
        self,
        old: Sprite,
        replacement: Sprite,
        *,
        preserve_position: bool = True,
        preserve_layer: bool = True,
    ) -> Sprite:
        """Atomically replace one sprite in the level.

        The replacement occupies the same list position so equal-layer render
        order remains stable. By default, its world position and layer are
        copied from the old sprite; its visual data and other properties remain
        those of the replacement.

        Args:
            old: Sprite currently owned by this level.
            replacement: Sprite to insert. It must not already belong to this
                level at another position.
            preserve_position: Copy the old sprite's world position.
            preserve_layer: Copy the old sprite's rendering layer.

        Returns:
            The inserted replacement sprite.

        Raises:
            ValueError: If ``old`` is not in the level or ``replacement`` is
                already in the level at another position.
        """
        old_index = next((index for index, sprite in enumerate(self._sprites) if sprite is old), None)
        if old_index is None:
            raise ValueError(f"Cannot replace sprite {old.name!r}: it does not belong to this level")
        if replacement is old:
            return old
        if any(sprite is replacement for sprite in self._sprites):
            raise ValueError(f"Cannot use sprite {replacement.name!r} as a replacement: it already belongs to this level")

        if preserve_position:
            replacement.set_position(old.x, old.y)
        if preserve_layer:
            replacement.set_layer(old.layer)
        self._sprites[old_index] = replacement
        return replacement

    def get_sprites_by_tag(self, tag: str) -> List[Sprite]:
        """Get all sprites that have the given tag.

        Args:
            tag: The tag to search for

        Returns:
            List[Sprite]: All sprites that have the given tag
        """
        return [s for s in self._sprites if tag in s.tags]

    def get_sprites_by_tags(self, tags: List[str]) -> List[Sprite]:
        """Get all sprites that have all of the given tags.

        Args:
            tags: The tags to search for

        Returns:
            List[Sprite]: All sprites that have all of the given tags
        """
        if not tags:
            return []
        return [s for s in self._sprites if all(tag in s.tags for tag in tags)]

    def get_sprites_by_any_tag(self, tags: List[str]) -> List[Sprite]:
        """Get all sprites that have any of the specified tags.

        Args:
            tags: List of tags to search for

        Returns:
            List[Sprite]: List of sprites that have any of the specified tags
        """
        return [sprite for sprite in self._sprites if any(tag in sprite.tags for tag in tags)]

    def get_all_tags(self) -> set[str]:
        """Get all unique tags from all sprites in the level.

        This method collects all tags from all sprites and returns them as a set,
        ensuring each tag appears only once in the result.

        Returns:
            set[str]: A set containing all unique tags from all sprites
        """
        all_tags = set()
        for sprite in self._sprites:
            all_tags.update(sprite.tags)
        return all_tags

    def get_sprite_at(self, x: int, y: int, tag: Optional[str] = None, ignore_collidable: bool = False) -> Sprite | None:
        """Get the sprite at the given coordinates.

        This method returns the first sprite that is at the given coordinates.
        If a tag is provided, it will return the first sprite that has the given tag.

        Args:
            x: The x coordinate
            y: The y coordinate
            tag: The tag to search for
        """
        sprites = self.get_sprites_at(x, y, tag=tag, ignore_collidable=ignore_collidable)
        return sprites[0] if sprites else None

    def get_sprites_at(
        self,
        x: int,
        y: int,
        tag: Optional[str] = None,
        ignore_collidable: bool = False,
        *,
        top_first: bool = True,
    ) -> List[Sprite]:
        """Return every sprite containing a world coordinate in layer order.

        Pixel-perfect sprites treat ``.`` as a hole. Other blocking modes use
        their rendered bounding boxes, matching :meth:`get_sprite_at`.
        Sorting happens at query time so runtime ``set_layer`` changes are
        reflected immediately.

        Args:
            x: World x-coordinate.
            y: World y-coordinate.
            tag: Optional required sprite tag.
            ignore_collidable: Include non-collidable sprites when true.
            top_first: Return higher layers first when true, lower layers first
                otherwise.
        """

        ordered = sorted(self._sprites, key=lambda sprite: sprite.layer, reverse=top_first)
        return [
            sprite
            for sprite in ordered
            if (ignore_collidable or sprite.is_collidable)
            and (tag is None or tag in sprite.tags)
            and sprite.contains_point(x, y, pixel_perfect=sprite.blocking == BlockingMode.PIXEL_PERFECT)
        ]

    def collides_with(self, sprite: Sprite, ignoreMode: bool = False) -> List[Sprite]:
        """Checks all sprites in the level for collisions with the given sprite.

        Args:
            sprite: The sprite to check for collisions
        """
        return [s for s in self._sprites if sprite.collides_with(other=s, ignoreMode=ignoreMode)]

    @property
    def name(self) -> str:
        """Get the name of the level."""
        return self._name

    def get_data(self, key: str) -> Any:
        return self._data.get(key)

    @property
    def grid_size(self) -> Tuple[int, int] | None:
        """Get the grid size of the level.

        Returns:
            Tuple[int, int]: The grid size of the level
        """
        return self._grid_size

    @property
    def placeable_areas(self) -> List[PlaceableArea]:
        """Get the placeable areas of the level."""
        return self._placeable_areas

    def clone(self) -> "Level":
        """Create a deep copy of this level.

        Returns:
            Level: A new Level instance with cloned sprites
        """
        # Clone each sprite and create new level
        cloned_sprites = [sprite.clone() for sprite in self._sprites]
        return Level(name=self._name, sprites=cloned_sprites, grid_size=self._grid_size, data=copy.deepcopy(self._data), placeable_areas=self._placeable_areas)
