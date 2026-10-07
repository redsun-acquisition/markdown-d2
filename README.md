# markdown-d2

`markdown-d2` turns [D2](https://d2lang.com) diagrams into pictures in a site
built with `zensical` or Python-Markdown. You write a diagram as text in a `d2`
code block, and the build draws it, once for the light theme and once for the
dark one. A diagram with several steps gets buttons to move through them, with
a fade or a morph between steps, and any diagram can be opened full screen.

Everything happens when the site is built, so your readers download no extra
software. A broken diagram stops the build with a message naming the page, the
diagram and the line, instead of showing a broken picture.

## Installation

```bash
uv add markdown-d2
```

The package brings its own Node through `nodejs-wheel-binaries`, so nothing
else needs installing.

## Use with zensical

Add the fence to `zensical.toml`:

```toml
[project.markdown_extensions.pymdownx.superfences]
custom_fences = [
  { name = "d2", class = "d2", format = { object = "markdown_d2.formatter", kwds = { root = "docs" } }, validator = "markdown_d2.validator" },
]
```

Then write a diagram in any page:

````markdown
```d2
you -> page: write
page -> site: build
```
````

The [documentation](https://redsun-acquisition.github.io/markdown-d2/)
starts with a
[tutorial](https://redsun-acquisition.github.io/markdown-d2/tutorials/first-diagram/), then shows how to step through
diagrams, import files and icons, change the look and
[use `markdown-d2` without `zensical`](https://redsun-acquisition.github.io/markdown-d2/how-to/use-python-markdown/),
and lists every [setting](https://redsun-acquisition.github.io/markdown-d2/reference/settings/).

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
