# BlueMask by Bluethroat Labs

Mask private details in photos and screenshots, locally in the browser.

BlueMask is the first planned product from **Bluethroat Labs**. Draw over sensitive
details, review the result, and download a flattened PNG. Secure masking replaces
pixels; optional cosmetic blur is explicitly labelled **Appearance only**. There
are no accounts, image uploads, or runtime third-party dependencies.

**Status:** locally tested release candidate. The repository includes the editor,
self-contained offline build, synthetic model evidence, and verification scripts.
Public production sign-off and physical mobile-browser testing remain pending.

[Getting started](#run) · [Using BlueMask](#using-bluemask) ·
[Privacy](#privacy-design) · [Evidence](#model-evidence) ·
[Development](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Contributing](CONTRIBUTING.md)

## Run

Python 3.10+ builds and serves the app using only its standard library.
Node.js 22+ and macOS Google Chrome are needed only for the browser checks.

```sh
gh repo clone BluethroatLabs/bluemask
cd bluemask
python3 build.py
python3 serve.py --port 8791
```

Open http://127.0.0.1:8791/. The public deployment directory is `dist/` only.
`dist/BlueMask.html` is a self-contained offline edition: HTML, CSS, JavaScript,
fonts, artwork, FAQ and displayed benchmark images are embedded. Open the file
directly; no localhost server, installation or service worker is needed.

After editing source, rebuild and refresh the browser. There is no `npm install`
step, backend, database, or automatic rebuild. See [Development](docs/DEVELOPMENT.md)
for detailed prerequisites and commands.

## Using BlueMask

1. Choose, drop, or paste a PNG, JPEG, or WebP. **Try a sample** opens fictional data.
2. Drag an empty part of the image to draw a secure mask over a sensitive detail.
3. Drag a mask to move it or a selected corner to resize it. Use **Draw** when a new
   mask needs to begin inside an existing one. Coordinate fields offer precise edits.
4. Review coverage at **100%**, including edges and repeated sensitive details.
5. Choose **Download PNG** and inspect the downloaded file before sharing it.

Use **About** for the privacy FAQ and **Tests** for the measured recovery results.
**Paranoia Mode** explains how to download the offline edition and disconnect the
device before selecting an image. The website cannot disconnect the device itself.

Undo uses `⌘Z` / `Ctrl+Z`; redo adds `Shift`. With the image canvas focused,
`Delete` or `Backspace` removes the selected region. `Escape` cancels an unfinished
gesture. Editing shortcuts are inactive while typing in a coordinate field.

## Product behavior

- Secure masking is the default for every new image. It replaces selected pixels
  with an opaque neutral patch.
- Cosmetic blur is labelled **Appearance only**. Choosing it opens an explanation
  whose primary action recommends secure masking. Downloading an image containing
  cosmetic regions requires another explicit choice.
- Methods belong to individual regions. Selecting cosmetic blur does not change
  existing secure masks. Secure masking takes precedence in overlaps.
- Regions can be drawn with a pointer, moved, resized, or created and adjusted with
  keyboard-accessible controls. Undo, redo, zoom and original preview are provided.
- Drag an empty area to create a mask; drag an existing mask to move it or a
  selected corner to resize it. No separate Adjust mode is needed. Draw explicitly
  starts a new mask even over an existing one, then returns to direct editing.
- PNG, JPEG and WebP inputs are accepted, up to 35 MB, 24 megapixels and 12,000
  pixels per side. Output is a fresh opaque PNG named `bluemask.png`.
- Export is blocked with no regions, during a drag, or while showing the original.
  Editing is frozen while the export snapshot is encoded.
- Clear session releases the editor's image canvases and resets its controls.
  This does not claim secure erasure of browser or operating-system memory.
- About and Tests open separate monochrome parchment scrolls. The editor shows
  no test results until Tests is opened. Reports, source links and file hashes
  live in Tests; About contains expandable questions. Both work offline.
- Typography follows bluethroatlabs.com's measured scale: 16px base text, 18px
  navigation, 20px desktop reading copy, and 16px mobile reading copy. Supporting
  labels stay at least 14px. The title uses its 120/80/60px responsive display
  sizes. Shared rem-based tokens keep larger browser text settings usable.

## Privacy design

The app contains no image-upload, analytics, telemetry, cookie, local-storage,
IndexedDB or service-worker code. Fonts and artwork are embedded rather than
requested from other sites. A restrictive Content Security Policy uses hashes for
the two scripts and stylesheet and sets `connect-src 'none'`.

Choosing a file reads it into browser memory. Export creates a new image rather
than forwarding the original file or its filename and metadata. The engine first
flattens transparency onto white, removes every secure region, applies cosmetic
effects using that sanitized source, and reapplies opaque secure masks last.
Changing any source pixels inside a secure region cannot affect the output for
fixed region geometry. Visible context and the regions' geometry remain visible.

Paranoia Mode gives an offline workflow. A webpage cannot turn off the user's
internet. Disconnect the device before opening the private image, use the offline
edition, save and inspect the result, and close the editor before reconnecting.
The browser's network indicator is advisory; it is not an isolation certificate.

Offline functionality shows that the processing needs no server. It does not
prove that arbitrary code, a browser extension or the device itself is honest.
Source review, matching release artifacts, reproducible tests and independent
distribution of hashes provide additional evidence. The manifest is unsigned;
no independent certification, anonymity or universal AI-resistance claim is made.

## Model evidence

The current experiment uses twelve synthetic eight-digit codes, one font and
fixed geometry. Secure PNGs were generated by this exact `engine.js` and all twelve
are identical. Identical inference inputs were reused and disclosed.

| Model | Gaussian sigma 3, exact OCR before → after | Secure mask, before → after |
| --- | --- | --- |
| DPIR / DRUNet (2021) | 9/12 → 12/12 | 0/12 → 0/12 |
| DarkIR (CVPR 2025) | 9/12 → 0/12 | 0/12 → 0/12 |

DPIR is an established known-kernel baseline. DarkIR is a low-light photographic
restoration model and failed the screenshot blur control. Its mask result is not
evidence of a strong privacy attack being resisted. Gaussian controls differ from
BlueMask's cosmetic effect. OCR failure is not a proof of information removal.
These are neither face-anonymization results nor results against every current AI.

`dist/bluemask-model-evidence.zip` contains synthetic originals, processed images,
restoration outputs, measured OCR, model provenance, checksums and reproduction
instructions. Large model weights and development environments are excluded.

## Verification

Build integrity and source-archive reproduction:

```sh
python3 scripts/check_build.py
```

With a local server running and Google Chrome installed on macOS:

```sh
node scripts/verify.mjs
node scripts/interactions.mjs
```

The scripts use an isolated browser profile and the Chrome DevTools Protocol, not
the user's browsing profile. They exercise the actual built HTML, not a separate
test UI. The reports in `evidence/runtime/` bind checks to the delivered HTML hash.

Current coverage: consent dialogs, secure defaults, export guards, generic PNG,
PNG metadata chunks, no image-processing HTTP requests, no web-storage writes,
offline-file open/mask/export, 160 seeded hidden-pixel perturbation cases with
overlaps and reversed order, real mouse/touch gestures, resize/undo, export races,
and recovery from rendering failures. Screenshots cover desktop, phone viewport,
light appearance and the Privacy Scroll.

Browser-engine evidence is currently headless Chrome on macOS. Phone emulation is
not a physical iPhone/Safari or Android/Chrome test.

GitHub Actions runs build/reproducibility and JavaScript syntax checks. It does not
run the macOS browser suites or repeat the AI experiments. The optional research
environment and exact checkpoint provenance are documented in
[research/README.md](research/README.md).

## Repository map

| Path | Contents |
| --- | --- |
| `app.html`, `app.js`, `styles.css` | Editor UI, state, interactions, and visual design |
| `engine.js` | Pixel replacement and cosmetic rendering |
| `privacy-scroll.html`, `assets/` | FAQ, bundled fonts, artwork, and brand assets |
| `build.py`, `serve.py` | Deterministic packaging and local static server |
| `scripts/` | Build and browser verification |
| `research/` | Synthetic evaluation harnesses and retained upstream source |
| `evidence/ai/` | Fixtures, outputs, measured results, and reproducibility archive |
| `evidence/runtime/` | Recorded browser checks bound to a built HTML hash |
| `docs/` | Architecture, development, privacy, release, and brand documentation |

Generated `dist/`, local environments, downloaded weights, caches, and the compiled
OCR helper are intentionally ignored. No application or research source code
depends on those files being committed.

## Release artifacts and hosting

`build.py` is deterministic for a fixed source tree and recorded model evidence.
It emits identical hosted/offline HTML, a SHA-256 manifest, hash list and static
hosting header configuration. The bundled fonts retain their complete OFL notices.

Serve only `dist/`, with the headers in `_headers` applied by the hosting platform.
Disable hosting-provider analytics/script injection, use HTTPS, and do not add
image-upload endpoints. The local `serve.py` applies the equivalent security headers.
Do not publish the research environment, internal product notes or browser profiles.

Before a public production sign-off: smoke-test real Safari/iOS and Android devices,
review deployment headers and actual served bytes, and establish the public source
and independently verifiable release-signing/distribution process. Broader recent
model and photographic-content evaluations are needed before expanding the current
benchmark wording. This is a locally tested release candidate, not that sign-off.

See [Releasing](docs/RELEASING.md) for the artifact inventory and deployment workflow.

## Contributing, security, and licensing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing privacy behavior or evidence.
Report suspected security issues using [SECURITY.md](SECURITY.md), with synthetic
reproduction material. The detailed trust boundaries are in
[Privacy](docs/PRIVACY.md).

A project-wide license has not yet been selected. Bundled fonts and research code
retain their upstream licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Bluethroat branding and artwork have separate provenance records.
