"""Icons and imported files, turned into the files D2 compiles."""

from __future__ import annotations

import base64
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

ICON = re.compile(r'(\bicon\s*:\s*)(?:"([^"\n]*)"|([^\s;}\n]+))')
IMPORT = re.compile(r"@([A-Za-z0-9_][\w./-]*)")
TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class SourceError(Exception):
    """An icon or an import cannot be used."""


def resolve_icon(reference: str, root: Path) -> bytes:
    """Return the bytes of the icon file *reference* names under *root*.

    Raises
    ------
    SourceError
        If *reference* is a URL, names no file, or names a file that is not
        SVG, PNG or JPEG.
    """
    if "://" in reference:
        raise SourceError(
            f"icons must be files under `root`; URL icons are not enabled: {reference}"
        )
    path = root / reference
    if path.suffix.lower() not in TYPES:
        raise SourceError(f"icon {reference!r} is not SVG, PNG or JPEG")
    if not path.is_file():
        raise SourceError(f"icon {reference!r} not found in {root}")
    return path.read_bytes()


def embed_icons(text: str, root: Path) -> str:
    """Return *text* with every icon file replaced by a quoted data URI."""

    def replace(match: re.Match[str]) -> str:
        reference = match.group(2) if match.group(2) is not None else match.group(3)
        if reference.startswith("data:"):
            return match.group(0)
        kind = TYPES.get((root / reference).suffix.lower(), "")
        data = base64.b64encode(resolve_icon(reference, root)).decode("ascii")
        return f'{match.group(1)}"data:{kind};base64,{data}"'

    return ICON.sub(replace, text)


def prepare(source: str, root: Path) -> dict[str, str]:
    """Return the files D2 compiles for one block, keyed as D2 imports them.

    The block is `index.d2`; each file it imports, directly or through
    another import, is added under its path relative to *root* with `.d2`.

    Raises
    ------
    SourceError
        If an icon cannot be embedded.
    """
    files = {"index.d2": embed_icons(source, root)}
    waiting = [source]
    while waiting:
        for name in IMPORT.findall(waiting.pop()):
            relative = name.removesuffix(".d2") + ".d2"
            path = root / relative
            if relative in files or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            files[relative] = embed_icons(text, root)
            waiting.append(text)
    return files
