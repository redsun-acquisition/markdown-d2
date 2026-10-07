"""The example scripts the documentation pages show."""

from __future__ import annotations

import runpy
from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_draw_a_diagram_with_python_markdown() -> None:
    """Run the Python-Markdown example and get a page holding the picture."""
    names = runpy.run_path(str(EXAMPLES / "python_markdown.py"))

    assert '<figure class="markdown-d2"' in names["page"]
    assert "<svg" in names["page"]
