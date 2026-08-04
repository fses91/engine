import json
import unittest
from datetime import datetime

from pydantic import ValidationError

from engine import MAX_REASONING_BYTES, ActionInput, GameAction


class TestActionInputReasoning(unittest.TestCase):
    def test_reasoning_omitted_defaults_to_none(self):
        obj = ActionInput()  # no arguments
        self.assertIsNone(obj.reasoning)
        self.assertEqual(obj.id, GameAction.RESET)
        self.assertEqual(obj.data, {})

    def test_accepts_small_string(self):
        payload = ActionInput(reasoning="just a note")
        self.assertEqual(payload.reasoning, "just a note")

    def test_accepts_json_object(self):
        blob = {"foo": 1, "bar": ["x", 2]}
        payload = ActionInput(reasoning=blob)
        self.assertEqual(payload.reasoning, blob)

    def test_rejects_non_serialisable_value(self):
        with self.assertRaises(ValidationError):
            # datetime is not JSON-serialisable by default
            ActionInput(reasoning=datetime.utcnow())

    def test_rejects_oversized_blob(self):
        big_string = "x" * (MAX_REASONING_BYTES + 1)
        with self.assertRaises(ValidationError):
            ActionInput(reasoning=big_string)

    def test_rejects_oversized_nested_blob(self):
        # more realistic: large dict/list
        huge_list = ["x"] * (MAX_REASONING_BYTES // 2)
        with self.assertRaises(ValidationError):
            ActionInput(reasoning=huge_list)

    # ---------- utility ---------------------------------------

    def test_validator_serialises_same_as_json(self):
        """Round-trip equivalence check for size counting."""
        blob = {"k": "v"}
        payload = ActionInput(reasoning=blob)
        # Recreate the bytes counted inside the validator:
        expected_bytes = json.dumps(blob, separators=(",", ":")).encode("utf-8")
        self.assertLessEqual(len(expected_bytes), MAX_REASONING_BYTES)
        self.assertEqual(payload.reasoning, blob)


class TestActionInputPosition(unittest.TestCase):
    def test_exposes_action6_coordinates(self):
        action = ActionInput(id=GameAction.ACTION6, data={"x": 39, "y": 29})

        self.assertEqual(action.x, 39)
        self.assertEqual(action.y, 29)
        self.assertEqual(action.position, (39, 29))
        self.assertEqual(action.require_position(), (39, 29))

    def test_positionless_action_returns_none(self):
        action = ActionInput(id=GameAction.ACTION1)

        self.assertIsNone(action.x)
        self.assertIsNone(action.y)
        self.assertIsNone(action.position)
        with self.assertRaisesRegex(ValueError, "has no position"):
            action.require_position()

    def test_rejects_incomplete_or_invalid_coordinates_on_access(self):
        with self.assertRaisesRegex(ValueError, "missing 'y'"):
            _ = ActionInput(id=GameAction.ACTION6, data={"x": 1}).position
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            _ = ActionInput(id=GameAction.ACTION6, data={"x": True, "y": 1}).position
        with self.assertRaisesRegex(ValueError, "between 0 and 63"):
            _ = ActionInput(id=GameAction.ACTION6, data={"x": 64, "y": 1}).position
