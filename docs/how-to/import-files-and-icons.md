# Import files and icons

This guide shows how to reuse a diagram kept in its own `.d2` file and how to
give shapes pictures from icon files. Both kinds of file live under the
[root](../explanation/glossary.md#root) folder you set in the formatter's
`root` setting, which is `docs` for this site.

## Import a file

Put the shared part in a `.d2` file under the root, then import it with `@`
and the file's path without `.d2`. Here `parts/storage.d2` holds a database
and its backup:

```d2
storage: @parts/storage
```

````markdown
```d2
storage: @parts/storage
```
````

A path with spaces goes in quotes: `@"my parts/storage"`. An import inside an
imported file is found relative to that file, as D2 finds it, so
`parts/storage.d2` would import `parts/disks.d2` as `@disks`.

## Add an icon

Give a shape an `icon` with the path of an SVG, PNG or JPEG file. The path
always starts from the root, in the block and in imported files alike, which
is why `parts/storage.d2` names its icon `icons/database.svg`:

```text
--8<-- "docs/parts/storage.d2"
```

The build puts the icon's bytes into the picture, so the published site needs
no copy of the file.

## Paths the build refuses

The build stops on an icon or an import that it cannot use, naming the
diagram and the path:

- a path that leads outside the root, such as `../secret.svg`
- an icon given as a URL, so building the site never needs the network
- an icon in another format, such as GIF

!!! warning "A changed import or icon does not show"

    `zensical` draws a page again only when the page itself changes, so after
    you edit an imported file or an icon, the site keeps the old picture. Run
    `zensical build --clean`, which empties that
    [page cache](../explanation/glossary.md#page-cache), then build or
    serve the site again to see the change.
