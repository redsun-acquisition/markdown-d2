"""Turn a Markdown page with a d2 block into HTML with Python-Markdown alone."""

from __future__ import annotations

from pathlib import Path

import markdown

import markdown_d2

# --8<-- [start:convert]
md = markdown.Markdown(
    extensions=["pymdownx.superfences"],
    extension_configs={
        "pymdownx.superfences": {
            "custom_fences": [
                {
                    "name": "d2",
                    "class": "d2",
                    "format": markdown_d2.formatter(root="pages"),
                    "validator": markdown_d2.validator,
                }
            ]
        }
    },
)
html = md.convert("```d2\nyou -> page: write\n```")
# --8<-- [end:convert]

# --8<-- [start:page]
page = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>My page</title></head>
<body>{html}</body>
</html>
"""
# --8<-- [end:page]

if __name__ == "__main__":
    Path("page.html").write_text(page, encoding="utf-8")
