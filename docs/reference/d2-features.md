# D2 features

`markdown-d2` draws diagrams with the WebAssembly build of D2 from the
`@d2lang/d2` package. This page lists what works through it and what does
not.

## Supported

- shapes, connections and containers, including `sql_table` and
  `sequence_diagram`
- labels written as Markdown (`|md`), code (`|python` and other languages)
  and LaTeX (`|latex`)
- `tooltip` and `link`
- `icon`, from an SVG, PNG or JPEG file under the root
- imports with `@`, quoted or not
- `layers`, `scenarios` and `steps`, each board shown as a step
- `vars.d2-config` settings: `theme-id`, `dark-theme-id`, `sketch`,
  `layout-engine` with `dagre` or `elk`, `pad` and `center`

## Not supported

| feature | what happens |
| --- | --- |
| `animate-interval` | D2 refuses it with `"animate-interval" is not a valid config`; use a [transition](settings.md#block-options) instead |
| `layout-engine: tala` | TALA is a separate, paid layout engine that this package does not include |
| icons given as a URL | the build stops; icons must be files under the root |
| `theme-id: 0` in a diagram | ignored when the formatter's `light_theme` is not `0`, because D2 reports `0` for a diagram that sets no theme |
