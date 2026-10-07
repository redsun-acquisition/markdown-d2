"""D2 diagrams for Python-Markdown, rendered when the site is built."""

from __future__ import annotations

from ._fence import formatter, validator
from ._paths import VERSION as __version__

__all__ = ["__version__", "formatter", "validator"]
