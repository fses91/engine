"""Tests for the compact symbolic ARC palette API."""

import unittest

import numpy as np

from arcengine import (
    ARC_COLOR_CHARS,
    ARC_COLOR_LEGEND,
    ARC_INVISIBLE_BLOCKING_CHAR,
    ARC_TRANSPARENT_CHAR,
    BlockingMode,
    Camera,
    Sprite,
    format_grid_ascii,
)
from arcengine.palette import (
    color_to_index,
    format_sprite_ascii,
    parse_grid_ascii,
)

EXPECTED_COLOR_LEGEND = "W=white, w=light gray, g=gray, G=dark gray, c=charcoal, B=black, M=magenta, P=pink, R=red, b=blue, S=sky blue, Y=yellow, O=orange, r=dark red, N=light green, p=purple"


class TestPaletteConstantsAndHelpers(unittest.TestCase):
    def test_palette_values_and_legend_are_exact(self):
        self.assertEqual(ARC_COLOR_CHARS, "WwgGcBMPRbSYOrNp")
        self.assertEqual(ARC_COLOR_LEGEND, EXPECTED_COLOR_LEGEND)
        self.assertEqual(ARC_TRANSPARENT_CHAR, ".")
        self.assertEqual(ARC_INVISIBLE_BLOCKING_CHAR, "X")
        self.assertEqual(len(set(ARC_COLOR_CHARS)), 16)

    def test_every_palette_symbol_maps_to_its_index(self):
        for expected_index, symbol in enumerate(ARC_COLOR_CHARS):
            with self.subTest(symbol=symbol):
                self.assertEqual(color_to_index(symbol), expected_index)

        self.assertEqual(color_to_index(ARC_TRANSPARENT_CHAR, allow_special=True), -1)
        self.assertEqual(color_to_index(ARC_INVISIBLE_BLOCKING_CHAR, allow_special=True), -2)

    def test_palette_mapping_is_case_sensitive(self):
        self.assertNotEqual(color_to_index("W"), color_to_index("w"))
        self.assertNotEqual(color_to_index("G"), color_to_index("g"))
        self.assertNotEqual(color_to_index("B"), color_to_index("b"))
        self.assertNotEqual(color_to_index("P"), color_to_index("p"))

    def test_unknown_color_symbol_is_rejected(self):
        with self.assertRaises(ValueError):
            color_to_index("?")
        with self.assertRaises(ValueError):
            color_to_index("WW")

    def test_parse_and_format_all_palette_values(self):
        parsed = parse_grid_ascii([ARC_COLOR_CHARS])

        self.assertIsInstance(parsed, np.ndarray)
        self.assertEqual(parsed.dtype, np.int8)
        np.testing.assert_array_equal(parsed, np.arange(16, dtype=np.int8).reshape(1, 16))
        self.assertEqual(format_grid_ascii(parsed), ARC_COLOR_CHARS)

    def test_display_formatter_uses_exact_clamping_semantics(self):
        # Display formatting follows the supplied ARC formatter: values below
        # zero become W and values above 15 become p.
        self.assertEqual(format_grid_ascii([[-2, -1, 0, 15, 16]]), "WWWpp")

        grid = np.arange(16, dtype=np.int16).reshape(2, 8)
        self.assertEqual(format_grid_ascii(grid), "WwgGcBMP\nRbSYOrNp")

    def test_display_formatter_handles_empty_python_and_numpy_grids(self):
        self.assertEqual(format_grid_ascii([]), "(empty grid)")
        self.assertEqual(format_grid_ascii(np.empty((0, 4), dtype=np.int8)), "(empty grid)")

    def test_sprite_formatter_preserves_special_cells(self):
        pixels = np.array([[-2, -1, 0, 15]], dtype=np.int8)
        self.assertEqual(format_sprite_ascii(pixels), "X.Wp")


class TestAsciiGridValidation(unittest.TestCase):
    def assert_unknown_cell_has_location(self, grid):
        with self.assertRaises(ValueError) as ctx:
            parse_grid_ascii(grid)

        message = str(ctx.exception)
        self.assertIn("?", message)
        self.assertIn("row", message.lower())
        self.assertIn("column", message.lower())

    def test_unknown_cells_report_row_and_column(self):
        self.assert_unknown_cell_has_location(["WW", "W?"])
        self.assert_unknown_cell_has_location(
            """
                WW
                W?
            """
        )

    def test_ragged_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_grid_ascii(["WW", "W"])
        with self.assertRaises(ValueError):
            Sprite(["WW", "W"])

    def test_empty_grids_are_rejected(self):
        for grid in ([], "", " \n "):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                parse_grid_ascii(grid)
            with self.subTest(sprite_grid=grid), self.assertRaises(ValueError):
                Sprite(grid)

    def test_empty_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_grid_ascii([""])
        with self.assertRaises(ValueError):
            Sprite([[]])

    def test_nested_symbol_cells_must_be_single_characters(self):
        with self.assertRaises(ValueError):
            Sprite([["WW", "g"]])

    def test_sprite_unknown_cell_error_keeps_location(self):
        with self.assertRaises(ValueError) as ctx:
            Sprite(["W?"])

        message = str(ctx.exception)
        self.assertIn("?", message)
        self.assertIn("row", message.lower())
        self.assertIn("column", message.lower())


class TestSymbolicSprite(unittest.TestCase):
    def test_list_of_symbol_rows_normalizes_to_numeric_int8(self):
        sprite = Sprite(["Ww.", "gGX"])
        expected = np.array([[0, 1, -1], [2, 3, -2]], dtype=np.int8)

        self.assertEqual(sprite.pixels.dtype, np.int8)
        self.assertEqual(sprite.render().dtype, np.int8)
        np.testing.assert_array_equal(sprite.pixels, expected)
        np.testing.assert_array_equal(sprite.render(), expected)

    def test_dedented_multiline_sprite(self):
        sprite = Sprite(
            """
                Ww.
                gGX
            """
        )
        expected = np.array([[0, 1, -1], [2, 3, -2]], dtype=np.int8)

        np.testing.assert_array_equal(sprite.pixels, expected)

    def test_nested_single_character_symbol_lists(self):
        sprite = Sprite([["W", "w", "."], ["g", "G", "X"]])
        expected = np.array([[0, 1, -1], [2, 3, -2]], dtype=np.int8)

        np.testing.assert_array_equal(sprite.pixels, expected)

    def test_symbolic_and_numeric_sprites_render_identically(self):
        symbolic = Sprite(
            ["Ww.", "gGX"],
            rotation=90,
            mirror_lr=True,
            scale=2,
        )
        numeric = Sprite(
            [[0, 1, -1], [2, 3, -2]],
            rotation=90,
            mirror_lr=True,
            scale=2,
        )

        self.assertEqual(symbolic.render().dtype, np.int8)
        np.testing.assert_array_equal(symbolic.pixels, numeric.pixels)
        np.testing.assert_array_equal(symbolic.render(), numeric.render())

    def test_to_ascii_can_format_source_or_rendered_pixels(self):
        sprite = Sprite(["Ww", "gG"], rotation=90)

        self.assertEqual(sprite.symbols, ("Ww", "gG"))
        self.assertEqual(sprite.to_ascii(), "Ww\ngG")
        self.assertEqual(sprite.to_ascii(rendered=False), "Ww\ngG")
        self.assertEqual(sprite.to_ascii(rendered=True), "gW\nGw")

    def test_special_cells_have_distinct_collision_behavior(self):
        transparent = Sprite(["."], blocking=BlockingMode.PIXEL_PERFECT)
        invisible_blocking = Sprite(["X"], blocking=BlockingMode.PIXEL_PERFECT)
        visible = Sprite(["W"], blocking=BlockingMode.PIXEL_PERFECT)

        self.assertFalse(transparent.collides_with(visible))
        self.assertTrue(invisible_blocking.collides_with(visible))

        camera = Camera(width=1, height=1, background="g")
        hidden_render = camera._raw_render([invisible_blocking])
        self.assertEqual(hidden_render.dtype, np.int8)
        np.testing.assert_array_equal(hidden_render, np.array([[2]], dtype=np.int8))

    def test_invisible_solid_cells_survive_downscaling(self):
        sprite = Sprite(["XX", "XX"], scale=-1)

        np.testing.assert_array_equal(sprite.render(), np.array([[-2]], dtype=np.int8))


class TestSymbolicColorOperations(unittest.TestCase):
    def test_camera_accepts_symbolic_background_and_letter_box(self):
        camera = Camera(width=2, height=1, background="w", letter_box="G")

        self.assertEqual(camera.background, "w")
        self.assertEqual(camera.letter_box, "G")

        raw = camera._raw_render([])
        rendered = camera.render([])
        self.assertEqual(raw.dtype, np.int8)
        self.assertEqual(rendered.dtype, np.int8)
        np.testing.assert_array_equal(raw, np.ones((1, 2), dtype=np.int8))
        self.assertEqual(rendered.shape, (64, 64))
        self.assertTrue(np.all(rendered[:16] == 3))
        self.assertTrue(np.all(rendered[16:48] == 1))
        self.assertTrue(np.all(rendered[48:] == 3))

    def test_camera_color_setters_keep_the_public_api_symbolic(self):
        camera = Camera()

        camera.background = "R"
        camera.letter_box = "p"
        self.assertEqual(camera.background, "R")
        self.assertEqual(camera.letter_box, "p")

        # Legacy numeric assignment is normalized at the compatibility edge;
        # reading public state still returns symbols.
        camera.background = 4
        camera.letter_box = 5
        self.assertEqual(camera.background, "c")
        self.assertEqual(camera.letter_box, "B")

    def test_color_remap_accepts_palette_and_special_symbols(self):
        sprite = Sprite(["Ww.X"])

        sprite.color_remap("W", "R")
        np.testing.assert_array_equal(sprite.pixels, np.array([[8, 1, -1, -2]], dtype=np.int8))

        sprite.color_remap(".", "g")
        np.testing.assert_array_equal(sprite.pixels, np.array([[8, 1, 2, -2]], dtype=np.int8))

        sprite.color_remap("X", ".")
        np.testing.assert_array_equal(sprite.pixels, np.array([[8, 1, 2, -1]], dtype=np.int8))

    def test_color_remap_none_changes_only_visible_cells(self):
        sprite = Sprite(["W.X"])

        sprite.color_remap(None, "N")

        np.testing.assert_array_equal(sprite.pixels, np.array([[14, -1, -2]], dtype=np.int8))
        self.assertEqual(sprite.pixels.dtype, np.int8)


if __name__ == "__main__":
    unittest.main()
