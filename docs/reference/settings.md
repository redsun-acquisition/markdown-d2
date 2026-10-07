# Settings

## Formatter settings

`markdown_d2.formatter` takes these keyword arguments. In `zensical.toml` they
go in the `kwds` table of the fence's `format`:

```toml
--8<-- "zensical.toml:fence"
```

| setting | default | meaning |
| --- | --- | --- |
| `root` | `"."`, the folder the build runs in | folder that imports and icons are found in; files outside it are refused |
| `cache_dir` | `".cache/markdown-d2"` | folder that keeps drawn pictures between builds; `None` keeps nothing |
| `light_theme` | `0` | D2 theme number of the light picture |
| `dark_theme` | `200` | D2 theme number of the dark picture |
| `dark_selector` | `'[data-md-color-scheme="slate"]'` | CSS selector of the page element that marks dark mode; the dark picture shows inside it |
| `errors` | `"raise"` | `"raise"` stops the build on a broken diagram; `"show"` puts the error in the page instead |
| `timeout` | `60` | seconds to wait for one diagram, every [board](../explanation/glossary.md#board) in both themes |
| `node` | the Node of `nodejs-wheel-binaries` | path of the Node program that draws the pictures |
| `transition` | `"fade"` | how a diagram changes between steps: `"none"`, `"fade"` or `"morph"` |

An unknown `transition` raises `ValueError` when the formatter is created.

## Block options

A `d2` block takes two options, written after `d2` on its first line:

````markdown
```d2 title="Publishing a site" transition="morph"
````

| option | meaning |
| --- | --- |
| `title` | caption under the picture, and the name screen readers announce for it |
| `transition` | transition of this diagram, overriding the formatter's `transition` |

Any other option stops the build with `unknown option "<name>"; set it in
d2-config instead`. Settings of D2 itself go in the diagram, under
`vars.d2-config`.
