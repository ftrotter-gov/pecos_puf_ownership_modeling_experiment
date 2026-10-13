# `reports/` — the Evidence site

[Evidence](https://evidence.dev) reports over `data/pecos.duckdb`, **built
locally and published to GitHub Pages**. There is no CI: the site is built on
your machine and pushed from your machine, so what you tested is what ships.

Live at
<https://ftrotter-gov.github.io/pecos_puf_ownership_modeling_experiment/>.

## Quick start

```bash
make install        # once: installs the node dependencies
make all            # data -> graph -> test -> sources -> site
make serve          # dev server with live reload, at localhost:3000
make publish        # push the built site to GitHub Pages
```

From this directory, the underlying commands are `npm run sources`,
`npm run dev`, and `npm run build`.

## How the data gets here

```
data/*.csv
   │  build_hierarchy.py          five-category hierarchy
   │  build_ownership_graph.py    ultimate ownership resolution
   ▼
data/pecos.duckdb
   │  npm run sources             runs sources/pecos/*.sql
   ▼
reports/static/data/*.parquet
   │  npm run build
   ▼
reports/build/                    the static site
```

`sources/pecos/connection.yaml` points at `../../../data/pecos.duckdb`, which
is read **only** during `npm run sources`. The 17 MB database is never
published — only the small parquet extracts are. On the current snapshot that
is 47 KB of data (2,246 ultimate owners).

**The ownership graph is resolved in Python, not here.** Evidence runs queries
in the browser with DuckDB-WASM, and graph traversal client-side would be slow
and fragile. `build_ownership_graph.py` does that work once with
[igraph](https://python.igraph.org/); the SQL in `sources/` only ever selects
and aggregates.

## Three things that break a GitHub Pages deploy

**1. `.nojekyll`.** GitHub Pages runs Jekyll by default, and Jekyll refuses to
serve any directory whose name begins with an underscore. Evidence puts its
JavaScript in `_app/`, so without this file the site loads its HTML and then
hangs forever with no styling, no data, and no error in the console.
`publish_reports.py` writes it on every publish.

**2. `deployment.basePath` in `evidence.config.yaml`.** Pages serves this
repository from a subdirectory, not the domain root. Without the base path
every asset and parquet file resolves to `/` and 404s. If you fork this
repository under a different name, change it to match.

**3. The Pages source setting.** One-time, in the GitHub web UI:
*Settings → Pages → Build and deployment → Deploy from a branch →
`gh_reports_branch` / `(root)`*.

## Why the build is 86 MB

Almost all of it is the DuckDB WebAssembly engine (`duckdb-mvp.wasm` 38 MB,
`duckdb-eh.wasm` 33 MB) that Evidence ships so the browser can run SQL. The
actual report data is 47 KB. The engine is cached by the browser after first
load, and only one of the two `.wasm` builds is fetched.

Because of that size, `gh_reports_branch` is rebuilt as a single orphan commit
and force-pushed on every publish rather than accumulating history. See the
module docstring of `publish_reports.py`.

## Layout

| Path | Purpose |
| :--- | :------ |
| `evidence.config.yaml` | Base path, plugins, title |
| `sources/pecos/connection.yaml` | DuckDB connection (relative path, no secrets) |
| `sources/pecos/*.sql` | Queries extracted to parquet at build time |
| `pages/index.md` | The Ultimate Owners report |

## Node dependencies

`@evidence-dev/evidence` declares its build toolchain as **peer** dependencies
with exact pinned versions, which npm will not install on its own. They are
listed explicitly in `devDependencies`; without them `npm install` fails on an
`ERESOLVE` conflict between `svelte2tsx` and `typescript`. Do not loosen those
pins to ranges.

If `npm run sources` fails with a WebAssembly `CompileError`, or an `ENOENT`
on a `.wasm` file, the install was incomplete — the WASM binaries are large
and an interrupted `npm install` leaves truncated files behind. Fix it with:

```bash
rm -rf node_modules package-lock.json && npm install
```
