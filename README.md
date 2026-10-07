# markdown-d2

`markdown-d2` draws [D2](https://d2lang.com) diagrams in a Python-Markdown
site. You write a diagram in a `d2` code block, and when the site is built the
block becomes a picture, drawn twice so it follows the site's light and dark
theme. A diagram with several steps gets buttons to move through them, and any
diagram can be opened full screen to zoom and pan.

Everything happens when the site is built, so your readers download no extra
software. A broken diagram stops the build with a message naming the page, the
diagram and the line, instead of showing a broken picture.

## Installation

```bash
uv add markdown-d2
```

The package brings its own Node through `nodejs-wheel-binaries`, so nothing
else needs installing.

## Use with Zensical

`markdown-d2` plugs into `pymdownx.superfences` as a custom fence. In
`zensical.toml`:

```toml
[project.markdown_extensions.pymdownx.superfences]
custom_fences = [
  { name = "d2", class = "d2", format = { object = "markdown_d2.formatter", kwds = { root = "docs" } }, validator = "markdown_d2.validator" },
]
```

Zensical renders a page again only when the page itself changes. After you
edit a file that a diagram imports, or an icon it uses, run
`zensical build --clean` to see the change.

## Use with Python-Markdown

```python
import markdown
import markdown_d2

md = markdown.Markdown(
    extensions=["pymdownx.superfences"],
    extension_configs={
        "pymdownx.superfences": {
            "custom_fences": [
                {
                    "name": "d2",
                    "class": "d2",
                    "format": markdown_d2.formatter(),
                    "validator": markdown_d2.validator,
                }
            ]
        }
    },
)
html = md.convert("```d2\na -> b\n```")
```

## Settings

Most settings belong to D2 itself and go in the diagram, in `d2-config`, such
as the layout engine or sketch mode. The formatter takes these:

| setting | default | meaning |
| --- | --- | --- |
| `root` | the folder the build runs in | where imports and icons are looked up |
| `cache_dir` | `.cache/markdown-d2` | where drawn pictures are kept between builds; `None` keeps nothing |
| `light_theme`, `dark_theme` | `0`, `200` | D2 theme numbers for the light and the dark picture |
| `dark_selector` | `[data-md-color-scheme="slate"]` | the CSS selector under which the dark picture shows |
| `errors` | `raise` | `raise` stops the build on a broken diagram; `show` draws the error in the page |
| `timeout` | `60` | seconds to wait for one picture |
| `node` | the Node of `nodejs-wheel-binaries` | the Node program that draws the pictures |

## Developing

```bash
uv sync
uv run tox                # lint, types, tests, docs
uv run tox -e browser     # the figure in a real browser, with screenshots
```

The build copies D2 into the package, so after a change to
`package-lock.json` run `uv sync --reinstall-package markdown-d2` before
testing; until then the tests still use the old copy.

## D2

The wheel contains the WebAssembly build of D2 from the `@d2lang/d2` package.
Its source is at <https://github.com/d2lang/d2> under the MPL-2.0, and its
licence and notices are installed with the package in
`markdown_d2/node_modules/@d2lang/d2/`.
