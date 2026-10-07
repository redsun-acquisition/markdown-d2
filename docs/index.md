# markdown-d2

`markdown-d2` draws [D2](https://d2lang.com) diagrams in a Python-Markdown
site. You write a diagram in a `d2` code block, and when the site is built
the block becomes a picture, drawn twice so it follows the site's light and
dark theme. A diagram with several steps gets buttons to move through them,
and any diagram can be opened full screen to zoom and pan.

Everything happens when the site is built. Your readers download no extra
software, and a broken diagram stops the build with a message that says
which diagram and which line, instead of showing a broken picture.

## A first diagram

```d2 title="A web request"
browser -> server: HTTPS
server -> cache: look up
server -> database: query
cache -> database: refresh
```

Each example on this page is followed by the block that draws it:

````text
```d2 title="A web request"
browser -> server: HTTPS
server -> cache: look up
server -> database: query
cache -> database: refresh
```
````

The `title` becomes the caption under the picture, and the name screen
readers announce for it.

## Steps

D2 can split a diagram into steps, each adding to the one before. The
picture then shows one step at a time, with buttons and the arrow keys to
move between them:

```d2 title="Publishing a site"
pages: write the pages
steps: {
  1: { build: build the site; pages -> build }
  2: { check: check the links; build -> check }
  3: { publish: publish it; check -> publish }
}
```

````text
```d2 title="Publishing a site"
pages: write the pages
steps: {
  1: { build: build the site; pages -> build }
  2: { check: check the links; build -> check }
  3: { publish: publish it; check -> publish }
}
```
````

## Tooltips and links

A `tooltip` shows when the reader points at a shape, and a `link` makes the
shape clickable:

```d2
server: Server {
  tooltip: Answers requests from the browser
  link: https://d2lang.com/tour/interactive
}
browser -> server: requests
```

````text
```d2
server: Server {
  tooltip: Answers requests from the browser
  link: https://d2lang.com/tour/interactive
}
browser -> server: requests
```
````

## Formulas

A label written as LaTeX is typeset in the picture:

```d2
model: |latex
  I(x) = I_0 e^{-\mu x}
|
```

````text
```d2
model: |latex
  I(x) = I_0 e^{-\mu x}
|
```
````

## Imports and icons

A diagram can import another `.d2` file and use icon files, both found under
the `root` folder, which is `docs` for this site. Here `parts/storage.d2`
holds a database with an icon:

```d2
storage: @parts/storage
```

````text
```d2
storage: @parts/storage
```
````

An icon must be a file, an SVG, PNG or JPEG under `root`. A URL is refused,
so building the site never needs the network.

Zensical renders a page again only when the page itself changes. After you
edit an imported file or an icon, run `zensical build --clean` to see the
change.

## Settings

Most settings belong to D2 itself and go in the diagram, in `d2-config`,
such as the layout engine or sketch mode. The formatter takes these:

| setting | default | meaning |
| --- | --- | --- |
| `root` | the folder the build runs in | where imports and icons are looked up |
| `cache_dir` | `.cache/markdown-d2` | where drawn pictures are kept between builds; `None` keeps nothing |
| `light_theme`, `dark_theme` | `0`, `200` | D2 theme numbers for the light and the dark picture |
| `dark_selector` | `[data-md-color-scheme="slate"]` | the CSS selector under which the dark picture shows |
| `errors` | `raise` | `raise` stops the build on a broken diagram; `show` draws the error in the page |
| `timeout` | `60` | seconds to wait for one picture |
| `node` | the Node of `nodejs-wheel-binaries` | the Node program that draws the pictures |

In `zensical.toml`, you pass them through the formatter:

```toml
[project.markdown_extensions.pymdownx.superfences]
custom_fences = [
  { name = "d2", class = "d2", format = { object = "markdown_d2.formatter", kwds = { root = "docs" } }, validator = "markdown_d2.validator" },
]
```
