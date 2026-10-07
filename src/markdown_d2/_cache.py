"""SVGs and board lists kept on disk between builds."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def key(*parts: object) -> str:
    """Return the SHA-256 of *parts*, written as JSON with sorted keys."""
    text = json.dumps(parts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Cache:
    """Text files in one folder, or nothing at all when the folder is `None`.

    A file is written under a temporary name and renamed into place, so two
    builds writing the same entry never leave half a file.
    """

    def __init__(self, folder: Path | None) -> None:
        self._folder = folder

    def get(self, name: str) -> str | None:
        """Return the stored text, or `None` when there is none."""
        if self._folder is None:
            return None
        try:
            return (self._folder / name).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def put(self, name: str, text: str) -> None:
        """Store *text* under *name*."""
        if self._folder is None:
            return
        self._folder.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(dir=self._folder, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temporary, self._folder / name)
