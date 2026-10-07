# Use markdown-d2 without zensical

This guide shows how to draw diagrams in pages you build with Python-Markdown
yourself, in a script or another site generator.

## Add the fence

Hand `pymdownx.superfences` a custom
[fence](../explanation/glossary.md#fence) named `d2`, with
`markdown_d2.formatter()` as its format and `markdown_d2.validator` as its
validator:

```{.python}
--8<-- "examples/python_markdown.py:convert"
```

`root` is the folder your imports and icons live in. The formatter takes the
same [settings](../reference/settings.md) as in `zensical.toml`, as keyword
arguments.

## Put the result in a page

Each figure carries its own CSS and script, so the HTML works wherever you put
it. Place it in the body of your page template:

```{.python}
--8<-- "examples/python_markdown.py:page"
```

Without a site theme, the page has no dark mode, so the light picture shows.
If your template marks dark mode, set `dark_selector` to match it, as
[Change how a diagram looks](change-the-look.md#match-a-site-without-this-themes-dark-mode)
shows.

??? example "The whole script"

    ```{.python}
    --8<-- "examples/python_markdown.py"
    ```
