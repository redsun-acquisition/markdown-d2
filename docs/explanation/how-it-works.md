# Drawing diagrams when the site is built

`markdown-d2` draws every diagram while the site is built, not in the reader's
browser. This page explains what that choice gives you, what happens during a
build, and where it shows its limits.

## Why at build time

A diagram drawn in the browser needs a drawing program sent with every page,
and the reader's browser runs it on every visit. A diagram drawn at build
time arrives as a finished picture, so the page loads no extra program and
shows the same thing in every browser. The cost moves to you: the build does
the drawing, once per change.

Drawing at build time also catches mistakes early. A diagram D2 cannot read
stops the build, so you find out before your readers do. A browser could only
show a broken picture, or nothing.

## What happens in a build

The build reaches a `d2` block and hands it to the
[formatter](glossary.md#formatter). The formatter first gathers what the
diagram needs: the block itself, every file it imports, and every icon,
whose bytes it puts into the diagram's text, so that the drawing never reads
the disk or the network.

The drawing itself happens in Node, the JavaScript program that comes with
`markdown-d2` through the `nodejs-wheel-binaries` package. Node runs the
WebAssembly build of D2, the same program the `d2` command uses, compiled to
run anywhere Node runs. The formatter starts Node at the first diagram and
keeps it running until the build ends, because starting it takes longer than
drawing most diagrams. Each diagram is one request: D2 lays it out, then draws
every [board](glossary.md#board) twice, once in the light
[theme](glossary.md#theme) and once in the dark one. If Node dies, the
formatter starts it again once before it gives up.

Two pictures of every board could clash on one page, because an SVG names its
parts with ids and its styles with class names, and the page shares both. So
each picture gets names of its own. The formatter hands D2 a short text,
different for every picture, that D2 mixes into its class names, and then
adds a number to every id. The page's
CSS then shows the light or the dark picture, following the site's mode,
with no script involved.

## The cache

Drawing is the slow part of a build, so the formatter keeps every result in
the [cache](glossary.md#cache). It finds a diagram by a key, a fingerprint
of everything that decides the picture: the diagram's text once every import
and icon is put into it, the two themes, and the versions of `markdown-d2`
and D2. A build that finds the key reuses the pictures without
starting Node at all, and any change to one of those parts makes a new key,
so an upgrade draws everything again.

Nothing removes old entries, so the folder only grows. It holds nothing you
cannot get back, so you can delete it whenever you like; the next build
draws every diagram again.

`zensical` keeps a [page cache](glossary.md#page-cache) of its own. It renders a page again
when the page's text or the site's settings change, but it does not know that
a page uses an imported file or an icon. That is why a change to one of those
files needs `zensical build --clean` before it shows.

## Moving between steps

The figure holds every board from the start, so changing step needs no
request. A small script in the page shows one board at a time and adds the
buttons. Without it, the reader still gets every board, one below the other.

The morph transition works because D2 marks each shape and connection with a
name that stays the same on every board. The script finds the shapes two
boards share, measures where each one was and where it is now, and slides it
between the two. A shape only the new board has fades in. A connection is moved
the same way, by stretching its old outline into the new one rather than
drawing a new path. That looks right for a short move, but a connection that
bends a different way on the new step looks bent out of shape until the
slide ends.
