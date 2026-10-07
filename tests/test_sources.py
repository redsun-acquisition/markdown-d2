"""Icons and imported files, turned into what D2 compiles."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from markdown_d2._sources import SourceError, prepare, resolve_icon

SVG = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
DATA = "data:image/svg+xml;base64," + base64.b64encode(SVG).decode("ascii")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "icons").mkdir()
    (tmp_path / "icons" / "camera.svg").write_bytes(SVG)
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "stage.d2").write_text(
        "motor: { icon: icons/camera.svg }\nhome: @parts/home\n", encoding="utf-8"
    )
    (tmp_path / "parts" / "home.d2").write_text("origin\n", encoding="utf-8")
    return tmp_path


def test_embed_icons_and_collect_imports(root: Path) -> None:
    """Embed icons as quoted data URIs and gather imports, nested ones too."""
    files = prepare('cam: { icon: "icons/camera.svg" }\nstage: @parts/stage\n', root)

    assert files["index.d2"] == f'cam: {{ icon: "{DATA}" }}\nstage: @parts/stage\n'
    assert (
        files["parts/stage.d2"] == f'motor: {{ icon: "{DATA}" }}\nhome: @parts/home\n'
    )
    assert files["parts/home.d2"] == "origin\n"


def test_leave_an_at_sign_that_names_no_file(root: Path) -> None:
    """Pass an `@` that names no file through to D2 unchanged."""
    files = prepare("mail: write to me@example.org\n", root)

    assert files == {"index.d2": "mail: write to me@example.org\n"}


@pytest.mark.parametrize(
    ("reference", "message"),
    [
        ("https://icons.example.org/camera.svg", "URL icons are not enabled"),
        ("icons/missing.svg", "icon 'icons/missing.svg' not found in"),
        ("icons/camera.gif", "icon 'icons/camera.gif' is not SVG, PNG or JPEG"),
    ],
)
def test_refuse_icons_it_cannot_embed(root: Path, reference: str, message: str) -> None:
    """Refuse a URL, a missing file and a file of another type."""
    (root / "icons" / "camera.gif").write_bytes(b"GIF89a")

    with pytest.raises(SourceError, match=message):
        resolve_icon(reference, root)
