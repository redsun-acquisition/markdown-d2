"""Where the package finds Node, the render script and D2."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from markdown_d2 import _paths

ROOT = Path(__file__).parent.parent


def test_the_copied_d2_is_the_locked_version() -> None:
    """Ship the `@d2lang/d2` version the lock file pins."""
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    locked = lock["packages"]["node_modules/@d2lang/d2"]["version"]

    assert _paths.d2_version() == locked


def test_the_default_node_runs() -> None:
    """Find a Node program that runs, from `nodejs-wheel-binaries`."""
    result = subprocess.run(
        [str(_paths.default_node()), "--version"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.startswith("v24.")
