# markdown-d2

`markdown-d2` turns [D2](https://d2lang.com) diagrams into pictures in a site
built with [`zensical`](explanation/glossary.md#zensical) or Python-Markdown. You write a diagram as text in a `d2`
code block, and the build draws it, once for the light theme and once for the
dark one. Your readers get the picture with the page: they download no extra
software, and they can [step](explanation/glossary.md#step) through the diagram and open it full screen.

```d2 title="A web request"
browser -> server: HTTPS
server -> cache: look up
server -> database: query
cache -> database: refresh
```

This picture comes from this block:

````markdown
```d2 title="A web request"
browser -> server: HTTPS
server -> cache: look up
server -> database: query
cache -> database: refresh
```
````

Because the build draws every diagram, a mistake in one stops the build with a
message naming the page, the diagram and the line, so a broken picture never
reaches your readers.

## Where to go next

- To start, [draw your first diagram](tutorials/first-diagram.md) in a small
  site of your own.
- If you have a site already, the how-to guides show how to
  [show a diagram one step at a time](how-to/show-steps.md),
  [import files and icons](how-to/import-files-and-icons.md),
  [change how a diagram looks](how-to/change-the-look.md),
  [fix a broken diagram](how-to/fix-a-broken-diagram.md) and
  [use `markdown-d2` without `zensical`](how-to/use-python-markdown.md).
- To look something up, the reference lists the
  [settings](reference/settings.md), [what the figure holds](reference/figure.md),
  [which D2 features work](reference/d2-features.md) and the
  [Python API](reference/api.md).
- To understand how it works, read about
  [drawing diagrams when the site is built](explanation/how-it-works.md).
