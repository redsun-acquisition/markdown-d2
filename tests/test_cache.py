"""SVGs and board lists kept on disk between builds."""

from __future__ import annotations

from pathlib import Path

from markdown_d2._cache import Cache, key


def test_keep_what_was_put_across_instances(tmp_path: Path) -> None:
    """Return text stored by an earlier cache on the same folder."""
    Cache(tmp_path / "cache").put("abc.svg", "<svg>µ</svg>")

    assert Cache(tmp_path / "cache").get("abc.svg") == "<svg>µ</svg>"
    assert Cache(tmp_path / "cache").get("missing.svg") is None


def test_store_nothing_when_turned_off(tmp_path: Path) -> None:
    """Keep nothing when the folder is `None`."""
    cache = Cache(None)
    cache.put("abc.svg", "<svg/>")

    assert cache.get("abc.svg") is None


def test_change_the_key_with_any_part() -> None:
    """Give a different key when any part differs, the same one otherwise."""
    base = key("a -> b", {"x.d2": "q"}, "steps.1", "dark", "0.1.34", "0.1.0")

    assert base == key("a -> b", {"x.d2": "q"}, "steps.1", "dark", "0.1.34", "0.1.0")
    assert base != key("a -> b", {"x.d2": "r"}, "steps.1", "dark", "0.1.34", "0.1.0")
    assert base != key("a -> b", {"x.d2": "q"}, "steps.1", "dark", "0.1.35", "0.1.0")


def test_leave_no_temporary_files(tmp_path: Path) -> None:
    """Leave only the finished file in the folder after a write."""
    Cache(tmp_path).put("abc.svg", "<svg/>")

    assert [path.name for path in tmp_path.iterdir()] == ["abc.svg"]
