"""Icons and imported files, turned into the files D2 compiles."""

from __future__ import annotations

import base64
import posixpath
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

ICON = re.compile(
    r'((?:^|(?<=[{;.]))\s*icon\s*:\s*)(?:"([^"\n]*)"|([^\s;}\n]+))', re.MULTILINE
)
IMPORT = re.compile(r'@(?:"([^"\n]+)"|([A-Za-z0-9_][\w./-]*))')
TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class SourceError(Exception):
    """An icon or an import cannot be used."""


def inside(reference: str, root: Path) -> Path:
    """Return the path *reference* names under *root*.

    Raises
    ------
    SourceError
        If the path leads outside *root*.
    """
    path = (root / reference).resolve()
    if not path.is_relative_to(root.resolve()):
        raise SourceError(f"{reference!r} is outside root")
    return path


def resolve_icon(reference: str, root: Path) -> bytes:
    """Return the bytes of the icon file *reference* names under *root*.

    Raises
    ------
    SourceError
        If *reference* is a URL, names no file, names a file outside
        *root*, or names a file that is not SVG, PNG or JPEG.
    """
    if "://" in reference:
        raise SourceError(
            f"icons must be files under root; URL icons are not enabled: {reference}"
        )
    path = inside(reference, root)
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

    The block is `index.d2`. Each file it imports, directly or through
    another import, is added under its path relative to *root*, found as
    D2 finds it: relative to the folder of the file that imports it.

    Raises
    ------
    SourceError
        If an icon cannot be embedded, or an import leads outside *root*.
    """
    files = {"index.d2": embed_icons(source, root)}
    waiting = [("index.d2", source)]
    while waiting:
        importer, text = waiting.pop()
        for quoted, plain in IMPORT.findall(text):
            name = quoted or plain
            relative = (
                posixpath.normpath(
                    posixpath.join(
                        posixpath.dirname(importer), name.removesuffix(".d2")
                    )
                )
                + ".d2"
            )
            path = inside(relative, root)
            if relative in files or not path.is_file():
                continue
            imported = path.read_text(encoding="utf-8")
            files[relative] = embed_icons(imported, root)
            waiting.append((relative, imported))
    return files
