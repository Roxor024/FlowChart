import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from intake import accept  # noqa: E402


def test_duplicate_has_no_second_effect():
    store = {}
    assert accept(store, "O-1", {"n": 1}) == (202, "O-1")
    assert accept(store, "O-1", {"n": 2}) == (202, "O-1")
    assert store == {"O-1": {"n": 1}}


def test_missing_id_rejected():
    assert accept({}, "", {})[0] == 400
