# Fix a broken diagram

This guide shows how to find what is wrong when the build stops on a diagram,
and how to keep working on a page while one of its diagrams is broken.

## Read the message

When a diagram is broken, the build stops with a message that starts with
`markdown-d2:`. With `zensical` it sits inside a long Python traceback, so
search the output for that word:

```text
markdown-d2: index.md: diagram starting "you -> page: write": line 2, column 1: connection missing destination
```

The message names the page, then the diagram, by its `title` if it has one or
else by its first line, then what went wrong. A line and column count from the
start of the block, so `line 2` is the second line inside the block.

## Keep building while you work

While you write a page, you may want the rest of the site to keep building.
Set `errors` to `show` in the
[formatter's](../explanation/glossary.md#formatter) `kwds`, and a broken diagram turns
into a red box holding the same message, in place of the picture:

```toml
format = { object = "markdown_d2.formatter", kwds = { root = "docs", errors = "show" } }
```

!!! warning "A shown error gets published"

    With `errors = "show"`, a site with a broken diagram builds and can be
    published with the red box in it. Set `errors` back to `raise`, the
    default, before you publish.

## Give a large diagram more time

The build waits 60 seconds for each diagram, every step in both themes,
before it gives up with `no answer within 60 s`. For a very large diagram,
raise `timeout` in the formatter's `kwds`:

```toml
format = { object = "markdown_d2.formatter", kwds = { root = "docs", timeout = 180 } }
```

## Other messages

| message | what to do |
| --- | --- |
| `unknown option "layout"; set it in d2-config instead` | Move the setting into the diagram's `vars.d2-config`, as [Change how a diagram looks](change-the-look.md#style-one-diagram) shows. A block takes only `title` and `transition`. |
| `unknown transition "spin"; use none, fade or morph` | Use one of the three transitions. |
| `icon 'x.gif' is not SVG, PNG or JPEG` | Convert the icon to one of those formats. |
| `icon 'x.svg' not found in docs` | Check the path, which starts from the [root](../explanation/glossary.md#root) folder. |
| `icons must be files under root; URL icons are not enabled: https://...` | Download the icon into the root folder and use its path. |
| `'../x.svg' is outside root` | Move the file under the root folder. |
| `failed to import "x.d2": file does not exist` | Check the path: an import inside an imported file is found relative to that file. |
| `cannot start ...` | The Node program could not start. Reinstall `markdown-d2`, or point the `node` setting at a Node you have. |

A diagram that builds but shows an old picture is not broken:
[a changed import or icon does not show](import-files-and-icons.md#paths-the-build-refuses)
until the [page cache](../explanation/glossary.md#page-cache) is cleared.
