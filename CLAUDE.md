# markdown-d2 agent & contributor conventions

Single source of conventions for agents (Claude, Copilot) and contributors:
cross-link, don't duplicate. The design lives outside the repository; this
file is what a session in the repository needs.

## What the package does

`markdown-d2` turns a `d2` code block into inline SVG when a Python-Markdown
site is built. It is a `pymdown-extensions` fence formatter: Python prepares
the files D2 compiles, looks each SVG up in a local cache, and asks one
long-running Node process for the ones it lacks. Node runs `render.mts`, which
drives `@d2lang/d2`, the WebAssembly build of D2. The browser side is a small
TypeScript file compiled to JavaScript and written inline into the page with
its CSS.

## Repository layout

```text
markdown-d2/
|-- src/markdown_d2/
|   |-- __init__.py          formatter, validator, __version__
|   |-- _paths.py            where Node, the render script, D2 and the assets are
|   |-- _renderer.py         the long-running Node process
|   |-- render.mts           the Node side: compile, list boards, render
|   |-- _cache.py            SVGs and board lists on disk, by key
|   |-- _sources.py          icons and imports: the files D2 compiles
|   |-- _fence.py            formatter, validator, HTML
|   |-- assets/              d2.css, d2.ts (compiled to d2.js, ignored by git)
|   `-- node_modules/        @d2lang/d2, copied in by the build hook (ignored by git)
|-- tests/                   pytest; stand_ins/ holds scripts that play a failing Node
|   `-- browser/             Playwright tests, marked browser
|-- docs/                    the package's own Zensical site
|-- hatch_build.py           build hook: npm ci, copy D2 into the package, compile d2.ts
|-- package.json             pins @d2lang/d2; typescript and @types/node for development
|-- package-lock.json
|-- tsconfig.json            type-checks render.mts
|-- tsconfig.browser.json    compiles assets/d2.ts
|-- pyproject.toml           metadata, hatch, ruff, mypy, pytest, tox
`-- uv.lock
```

## Build & validate

`tox` is the entry point, configured under `[tool.tox]` in `pyproject.toml`.
Every environment installs from `uv.lock` through `tox-uv-bare`, so a local
run uses the versions CI resolves:

```bash
uv run prek install              # once: run the prek.toml hooks on every commit
uv run tox                       # lint, types, tests, docs
uv run tox -e tests              # one environment
uv run tox -e tests -- tests/test_cache.py -x   # posargs reach pytest
uv run tox -e browser            # Playwright tests, not in the default list
```

| environment | what it runs |
| --- | --- |
| `lint` | `prek run --all-files`: the commit hooks, ruff included |
| `types` | strict `mypy`, then `tsc` over `render.mts` and `d2.ts` |
| `tests` | `pytest -q`, browser tests excluded |
| `browser` | `playwright install chromium`, then the `browser` tests |
| `docs` | `zensical build --strict` |

**Run what the change can break.** A change to `docs/` alone runs `docs`; to
TypeScript, `types` and `tests`; anything else, the full `uv run tox`.

### Node and D2

- **Node comes only from `nodejs-wheel-binaries`**, at runtime and at build
  time. Never call a `node` or `npm` found on `PATH`; run them through
  `nodejs_wheel` (`python -m nodejs_wheel ...`, or `node()` and `npm()` from
  Python).
- **`@d2lang/d2` is pinned exactly in `package.json`.** The build hook runs
  `npm ci` and copies the Node ES-module build into
  `src/markdown_d2/node_modules/`. After the lock file changes, refresh the
  copy with `uv sync --reinstall-package markdown-d2`.
- **`render.mts` is run directly by Node 24**, which strips the types itself.
  So no `enum` or `namespace` (`tsc` refuses them through
  `erasableSyntaxOnly`), and relative imports keep their `.ts` extension.
- The version is dynamic: `hatch-vcs` reads it from the git tags.

## Invariants

- **Every error the formatter raises is a
  `pymdownx.superfences.SuperFencesException`**, and its message starts with
  `markdown-d2: `. Any other exception makes the fenced-code extension show the
  block as plain code, silently, even under `zensical build --strict`.
- **A site build makes no network request.** Icons and imports are files under
  `root`; a URL icon is refused.
- **One Node process per Python process**, started on the first cache miss and
  stopped at exit; a crash is restarted once.
- **A cache key covers everything the SVG depends on**: the source after icon
  replacement, every imported file, the board, the theme, the `@d2lang/d2`
  version and the package version. An entry is never served for a changed
  input, so there is no invalidation and no automatic cleanup.
- **D2's own settings stay in D2's `d2-config`.** The fence takes only what D2
  does not know about (`title`); any other fence option is an error.
- The public surface is `markdown_d2.formatter`, `markdown_d2.validator` and
  `markdown_d2.__version__`.

## Code conventions

- Python >=3.11, `from __future__ import annotations` everywhere (ruff
  `FA102`).
- **Module-level names come first, after the imports:** constants, type
  aliases, `TypeVar`s, before any function or class.
- Ruff lint has `D` (numpy docstring convention) and `TC` enabled:
  runtime-unneeded imports go under `if TYPE_CHECKING:`.
- **Private modules are `_underscored`, and their module-level names carry no
  underscore**; the module name already says they are private. Class members
  keep the underscore. A non-underscore function in a private module needs a
  docstring (ruff `D103`).
- **Import a private module relatively, a public one absolutely.** Tests
  import everything absolutely.
- **All imports at the top of the module**, in `src/` and `tests/` alike. ruff's
  `E402` and `PLC0415` enforce it.
- **Prefer `match` to an `if` chain testing one value.**
- **Don't annotate what the assignment already says**, and don't alias an
  attribute to a local for a single use.
- **No comments in the import block**, and no comment that describes the code
  that follows; a comment explains why one statement is the way it is.

### Docstrings

- numpydoc: a one-line summary, a blank line, an optional extended
  description, then only the sections that add something.
- **No types in docstrings when the signature is annotated.** A `Parameters`
  entry is the bare name; what a function returns is said in the summary.
- Cross-references are Markdown, mkdocs style, never reStructuredText.
- Write for a reader who has nothing but the docstring: no design documents,
  no history.

## Testing conventions

- **Every test has a one-line docstring**: an imperative sentence saying what
  it checks.
- A test must be able to fail for a reason that matters; no tautological
  tests, and none written for a coverage number.
- Assert on what a caller can see: the HTML, the raised exception and its
  message, the files in the cache. Not private attributes.
- A failing Node is played by a stand-in script under `tests/stand_ins/`,
  passed through the `node` setting, never by patching the renderer.
- Browser tests are marked `browser` and run only in `tox -e browser`.

## Docs conventions

The package's docs live in `docs/` and are built with Zensical and
`markdown-d2` itself, so the `docs` environment is the integration test. Write
them for someone new, in plain words, with headings that name the topic.
Package names are code spans at every mention.

## Commits and branches

- One-line Conventional Commits messages, in the imperative, 72 characters at
  most, no body and no trailer.
- A branch is `<type>/<name>`. Work never goes on `main` directly.

## Response style (agents)

- Terse. No preamble, no restatement of the request, no summary of what you
  just did.
- No em dashes and no en dashes, anywhere. Arrows are `->` and `<-`.

## Updating this guide

Say **"Update CLAUDE.md with..."** to persist a convention here.
