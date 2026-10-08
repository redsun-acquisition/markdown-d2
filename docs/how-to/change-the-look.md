# Change how a diagram looks

This guide shows how to change the colours, the layout and the style of your
diagrams, for the whole site or for one diagram, and how to restyle the
figure around them.

## Pick the site's themes

Each figure holds a light and a dark picture, drawn with two D2
[themes](../explanation/glossary.md#theme). To use other themes on every
diagram, set `light_theme` and `dark_theme` in the
[formatter's](../explanation/glossary.md#formatter) `kwds`, using
the numbers from D2's [list of themes](https://d2lang.com/tour/themes):

```toml
format = { object = "markdown_d2.formatter", kwds = { root = "docs", light_theme = 4, dark_theme = 201 } }
```

## Style one diagram

Everything D2 itself can set goes in the diagram, under
[`vars.d2-config`](../explanation/glossary.md#d2-config). These settings win over the formatter's, so one diagram can differ from the
rest of the site:

```d2
vars: {
  d2-config: {
    sketch: true
    layout-engine: elk
    theme-id: 4
    dark-theme-id: 201
  }
}
idea -> draft -> page
```

````markdown
```d2
vars: {
  d2-config: {
    sketch: true
    layout-engine: elk
    theme-id: 4
    dark-theme-id: 201
  }
}
idea -> draft -> page
```
````

`sketch` draws the diagram as if by hand, and `layout-engine` picks the
[layout engine](../explanation/glossary.md#layout-engine) that places the shapes: `dagre` by default, or `elk`.
[D2 features](../reference/d2-features.md) lists which settings work and
which do not.

## Add tooltips, links and formulas

A `tooltip` shows next to the pointer when the reader points at a shape, while
the other shapes fade, and a `link` makes the shape clickable. A label written
as LaTeX is typeset:

```d2
server: Server {
  tooltip: Answers requests from the browser
  link: https://d2lang.com/tour/interactive
}
model: |latex
  I(x) = I_0 e^{-\mu x}
|
server -> model
```

````markdown
```d2
server: Server {
  tooltip: Answers requests from the browser
  link: https://d2lang.com/tour/interactive
}
model: |latex
  I(x) = I_0 e^{-\mu x}
|
server -> model
```
````

## Match a site without this theme's dark mode

The dark picture shows when the page matches `dark_selector`, which is
`[data-md-color-scheme="slate"]`, the mark `zensical` puts on the page in
dark mode. If your site marks dark mode another way, such as a `dark` class
on the `html` element, set `dark_selector` to match it:

```toml
format = { object = "markdown_d2.formatter", kwds = { root = "docs", dark_selector = "html.dark" } }
```

On a site with no dark mode at all, the light picture always shows, so there
is nothing to set.

## Restyle the figure

The figure, its buttons and its counter carry classes starting with
`markdown-d2-`, so your site's CSS can change their spacing, sizes or colours.
[The figure](../reference/figure.md#classes) lists them.
