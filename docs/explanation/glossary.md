# Glossary

Each word used across these pages with a meaning of its own is defined here
once. The other pages link to it the first time they use it.

## Block

A `d2` code block in a Markdown page. Each block becomes one
[figure](#figure) when the site is built.

## Board

One picture of a diagram. A diagram with no layers, scenarios or steps has one
board. Each layer, scenario and step D2 finds in it adds another, named by its
path, such as `steps.1` or `layers.detail`.

## Cache

The folder where the build keeps every picture it draws, so it only draws a
diagram again when the diagram or a setting changes. It is
`.cache/markdown-d2` unless you set `cache_dir`.

## d2-config

The `vars.d2-config` map at the top of a diagram, where D2's own settings go:
the layout engine, sketch mode, themes and others. It applies to that diagram
only.

## Fence

The kind of code block `pymdownx.superfences` hands to a function of your
choice instead of showing it as code. `markdown-d2` adds a fence named `d2`,
so every [block](#block) written with ```` ```d2 ```` becomes a figure.

## Figure

The HTML element a [block](#block) becomes: every [board](#board) of the
diagram, drawn once in the light [theme](#theme) and once in the dark one,
with buttons to move between boards and to open the diagram full screen.

## Formatter

The function `pymdownx.superfences` calls for each `d2` block. You create it
with `markdown_d2.formatter`, and its keyword arguments are the
[settings](../reference/settings.md). In `zensical.toml` they go in the `kwds`
table of the fence's `format`.

## Layout engine

The part of D2 that decides where each shape goes. D2 uses `dagre` unless a
diagram's [d2-config](#d2-config) picks another, such as `elk`.

## Page cache

The cache `zensical` keeps of whole pages, apart from the
[cache](#cache) of pictures. It renders a page again when the page's text or
the site's settings change, not when a file the page imports changes.

## Root

The folder that imports and icons are found in. A block can only use files
inside it.

## Step

What the reader moves to with the arrow buttons: the next [board](#board) of
the diagram. Every board counts, whether D2 made it from a layer, a scenario
or a step.

## Theme

A set of colours D2 draws with, picked by number, such as `0` for the light
default and `200` for a dark one. Each figure holds a light and a dark
picture, and the site's own light or dark mode decides which one shows.

## Transition

How the [figure](#figure) changes from one [step](#step) to the next: at
once, with a fade, or with a morph that moves each shared shape to its new
place.

## zensical

The site generator these pages are built with. It turns the Markdown pages in
`docs/` into a website, reading its settings from `zensical.toml`.
