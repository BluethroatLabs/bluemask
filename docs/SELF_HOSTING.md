# Self-hosting BlueMask

BlueMask is a static site. Python 3.10+ builds and serves it using only the
standard library. Node.js 22+ and macOS Google Chrome are needed only for the
browser checks.

## Run locally

```sh
gh repo clone BluethroatLabs/bluemask
cd bluemask
python3 build.py
python3 serve.py --port 8791
```

Open http://127.0.0.1:8791/. The server binds to loopback and serves `dist/`
only. After editing source, rebuild and refresh the browser. There is no
`npm install` step, backend, database, or automatic rebuild. Editing `dist/`
directly loses changes on the next build.

`dist/BlueMask.html` is a self-contained offline edition: HTML, CSS,
JavaScript, fonts, artwork, FAQ and displayed benchmark images are embedded.
Open the file directly; no localhost server, installation or service worker is
needed.

See [Development](DEVELOPMENT.md) for prerequisites, the browser harness, and
research reproduction.

## Check a local build

Build integrity and source-archive reproduction:

```sh
python3 scripts/check_build.py
```

With a local server running and Google Chrome installed on macOS:

```sh
node scripts/verify.mjs
node scripts/interactions.mjs
```

The scripts use an isolated browser profile and the Chrome DevTools Protocol,
not the user's browsing profile. They exercise the actual built HTML, not a
separate test UI. The reports in `evidence/runtime/` bind checks to the
delivered HTML hash. `verify.mjs` accepts an optional URL argument.
`interactions.mjs` currently expects port 8791.

GitHub Actions runs build/reproducibility and JavaScript syntax checks. It does
not run the macOS browser suites or repeat the AI experiments.

## Publish a static copy

`build.py` is deterministic for a fixed source tree and recorded model evidence.
It emits identical hosted and offline HTML, a SHA-256 manifest, a hash list and
static hosting header configuration. The bundled fonts retain their complete OFL
notices.

| Output in `dist/` | Purpose |
| --- | --- |
| `index.html` | Hosted application |
| `BlueMask.html` | Identical standalone offline edition |
| `bluemask-source.zip` | Source, documentation, and inputs needed to rebuild |
| `bluemask-model-evidence.zip` | Recorded synthetic experiment and reproduction files |
| `manifest.json` | Build ID, engine hash, and artifact SHA-256 values |
| `SHA256SUMS` | Hash list for distribution verification |
| `_headers` | Static-hosting security-header configuration |

Serve only `dist/`, with the headers in `_headers` applied by the hosting
platform. The local `serve.py` applies the equivalent security headers. Disable
hosting-provider analytics and script injection, use HTTPS, and do not add
image-upload endpoints. Do not publish the research environment, internal
product notes, or browser profiles.

After deployment, inspect response headers and compare served HTML with the
intended build. A local test is not evidence about bytes modified by a hosting
platform.

See [Releasing](RELEASING.md) for the artifact inventory, device checks, and the
steps still required before a public production sign-off.
