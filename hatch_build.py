"""Put the D2 WebAssembly build and the compiled browser script into the wheel."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from hatchling.builders.config import BuilderConfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from nodejs_wheel import node, npm

D2_FILES = ("package.json", "LICENSE.txt", "THIRD_PARTY_NOTICES.txt")


def run(code: int, what: str) -> None:
    """Raise when a Node or npm command failed."""
    if code != 0:
        raise RuntimeError(f"{what} failed with exit code {code}")


class CustomBuildHook(BuildHookInterface[BuilderConfig]):
    """Install the locked `@d2lang/d2`, copy its Node build, compile `d2.ts`."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Prepare the files the wheel ships but git does not hold."""
        root = Path(self.root)
        run(npm(["ci", "--no-audit", "--no-fund"], cwd=root), "npm ci")
        source = root / "node_modules" / "@d2lang" / "d2"
        target = root / "src" / "markdown_d2" / "node_modules" / "@d2lang" / "d2"
        shutil.rmtree(target, ignore_errors=True)
        (target / "dist").mkdir(parents=True)
        for name in D2_FILES:
            shutil.copy2(source / name, target / name)
        shutil.copytree(source / "dist" / "node-esm", target / "dist" / "node-esm")
        tsc = root / "node_modules" / "typescript" / "bin" / "tsc"
        run(node([str(tsc), "-p", str(root / "tsconfig.browser.json")]), "tsc")
        build_data["artifacts"].extend(
            ["src/markdown_d2/node_modules", "src/markdown_d2/assets/d2.js"]
        )
