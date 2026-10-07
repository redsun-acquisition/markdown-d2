"""Render Markdown pages with the d2 fence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import markdown
import pytest

from markdown_d2 import formatter, validator


@pytest.fixture
def page(tmp_path: Path) -> Callable[..., str]:
    def render(text: str, **settings: Any) -> str:
        settings.setdefault("root", tmp_path)
        settings.setdefault("cache_dir", tmp_path / "cache")
        fence = {
            "name": "d2",
            "class": "d2",
            "format": formatter(**settings),
            "validator": validator,
        }
        md = markdown.Markdown(
            extensions=["pymdownx.superfences"],
            extension_configs={"pymdownx.superfences": {"custom_fences": [fence]}},
        )
        return md.convert(text)

    return render
