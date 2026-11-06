import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from intake import accept  # noqa: E402


class Intake(unittest.TestCase):
    def test_duplicate_has_no_second_effect(self):
        store = {}
        self.assertEqual(accept(store, "O-1", {"n": 1}), (202, "O-1"))
        self.assertEqual(accept(store, "O-1", {"n": 2}), (202, "O-1"))
        self.assertEqual(store, {"O-1": {"n": 1}})

    def test_missing_id_rejected(self):
        self.assertEqual(accept({}, "", {})[0], 400)


if __name__ == "__main__":
    unittest.main()
