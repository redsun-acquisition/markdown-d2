"""Where the package keeps the files it runs."""

from __future__ import annotations

import json
import os
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from nodejs_wheel.executable import ROOT_DIR

try:
    VERSION = version("markdown-d2")
except PackageNotFoundError:
    VERSION = "unknown"
PACKAGE = Path(__file__).parent
RENDER_SCRIPT = PACKAGE / "render.mts"
D2_PACKAGE = PACKAGE / "node_modules" / "@d2lang" / "d2"
ASSETS = PACKAGE / "assets"


def d2_version() -> str:
    """Return the version of the `@d2lang/d2` copy the package ships.

    Raises
    ------
    FileNotFoundError
        If the build hook has not copied D2 in; reinstall the package.
    """
    data = json.loads((D2_PACKAGE / "package.json").read_text(encoding="utf-8"))
    return str(data["version"])


def default_node() -> Path:
    """Return the Node program `nodejs-wheel-binaries` installed.

    Raises
    ------
    FileNotFoundError
        If the wheel holds no Node program for this platform.
    """
    folder = ROOT_DIR if os.name == "nt" else os.path.join(ROOT_DIR, "bin")
    found = shutil.which("node", path=folder)
    if found is None:
        raise FileNotFoundError(f"no node program in {folder}")
    return Path(found)
