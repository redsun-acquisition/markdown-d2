# Draw your first diagram

In this tutorial you build a small `zensical` site with two diagrams: a plain
one, and one your reader steps through. On the way you watch the build draw
the pictures, see them follow the site's dark mode, and see the build stop on
a mistake.

## Before you start

!!! note "What you need"

    - `uv`, installed as its
      [installation guide](https://docs.astral.sh/uv/getting-started/installation/)
      shows
    - a terminal and a web browser

## 1. Create the project

Make a folder for the site and turn it into a `uv` project:

```bash
mkdir my-site
cd my-site
uv init --bare --python 3.11
```

`uv` writes a `pyproject.toml` file and nothing else. Every command from here
on runs in this folder.

## 2. Add the packages

```bash
uv add zensical markdown-d2
```

`uv` downloads `zensical`, which builds the site, and `markdown-d2`, which
draws the diagrams. `markdown-d2` brings the Node program it draws with, so
there is nothing else to install.

## 3. Turn on d2 blocks

Create a file named `zensical.toml` next to `pyproject.toml`, with this in it:

```toml
--8<-- "examples/first-diagram/zensical.toml"
```

The last table tells `zensical` to hand every `d2` block to `markdown-d2`. The
two palette tables give the site a button that switches between light and
dark mode.

## 4. Write a diagram

Create a folder named `docs`, and in it a file named `index.md`:

````markdown
# My site

--8<-- "examples/first-diagram/docs/index.md:first"
````

Each line of the block is a connection: an arrow from one shape to another,
with a label after the colon.

## 5. Look at the site

Start the site:

```bash
uv run zensical serve
```

The first build takes a few seconds, because `markdown-d2` starts Node and
draws the diagram. When the terminal says the site is being served, open
<http://localhost:8000> in your browser.

You see three boxes, `you`, `page` and `site`, joined by labelled arrows.
Click the sun icon at the top of the page: the site turns dark, and so does
the picture, because the build drew it in both themes.

## 6. Add steps

Add a second block to `docs/index.md`, below the first one:

````markdown
--8<-- "examples/first-diagram/docs/index.md:steps"
````

Save the file. The server builds the page again and the browser reloads it.

Notice the buttons under the new picture and the counter between them, which
reads `1 / 3`. Click the right arrow: a cup appears next to the kettle, and
the counter moves on. The title you gave the block shows under the picture.

## 7. Break it on purpose

Stop the server with ++ctrl+c++. In the first block, delete `site: build` from
the last line, so that it reads `page -> `, then build the site once:

```bash
uv run zensical build
```

The build stops with a long Python traceback. Look for the line that
contains `markdown-d2:`:

```text
markdown-d2: index.md: diagram starting "you -> page: write": line 2, column 1: connection missing destination
```

It names the page, the diagram and the line D2 could not read. Put
`site: build` back and build again: the build finishes without errors.

## What you built

You built a `zensical` site whose pages hold D2 diagrams. The build draws
each one in a light and a dark theme, gives a diagram with steps buttons to
move through them, and refuses to finish while a diagram is broken.

## Next steps

- [Show a diagram one step at a time](../how-to/show-steps.md), with a fade
  or a morph between the steps.
- [Import files and icons](../how-to/import-files-and-icons.md) to reuse
  parts of a diagram and give shapes pictures.
- [Change how a diagram looks](../how-to/change-the-look.md): themes, layout
  and sketch mode.

??? example "The whole `docs/index.md`"

    ````markdown
    --8<-- "examples/first-diagram/docs/index.md"
    ````
