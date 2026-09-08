# Architecture

BlueMask is a static browser application. Python assembles its release artifacts;
it is not a processing backend. The delivered app has no runtime packages or AI
models and makes no server request to process an image.

## Files and responsibilities

| File or directory | Responsibility |
| --- | --- |
| `app.html` | Editor, controls, native dialogs, and build placeholders |
| `styles.css` | Responsive layout, themes, type scale, and parchment treatment |
| `app.js` | Image loading, editor state, gestures, consent, history, and export |
| `engine.js` | Rectangle normalization, secure replacement, cosmetic processing |
| `privacy-scroll.html` | About / FAQ content inserted at build time |
| `assets/` | Locally bundled fonts, licenses, logo, and artwork |
| `build.py` | Inline assets, CSP hashes, source archive, manifest, and checksums |
| `serve.py` | Loopback-only development server serving `dist/` |
| `scripts/` | Build verification and isolated-browser checks |
| `research/` | Optional synthetic recovery experiments and retained upstream code |
| `evidence/ai/` | Recorded fixtures, model results, outputs, and provenance |
| `evidence/runtime/` | Browser reports tied to a particular HTML hash |

## Image flow

1. `app.js` accepts a local PNG, JPEG, or WebP using a file input, drop, or paste.
   It enforces file-size and decoded-dimension limits, flattens transparency onto
   white, and stores the original canvas in memory for editing and preview.
2. Regions store image-space coordinates and their own method. Changing the
   method picker changes new regions, not existing ones.
3. `engine.js` normalizes rectangles and copies the source to a working canvas.
   It overwrites every secure region with opaque RGB `(110, 113, 118)`.
4. Cosmetic regions use three separable box-blur passes on the sanitized pixels.
   Secure masks are painted again last so they win in overlaps.
5. The editor displays the composite and a separate selection overlay. Export
   snapshots the composite into a fresh canvas and encodes a PNG.

For fixed region geometry and fixed pixels outside the secure regions, changing
covered source pixels must not change the export. The browser suite checks this
property using 160 seeded perturbation cases with overlapping methods and reversed
region order. It is separate from the model recovery measurements.

## Editor state and export

The state includes the source, composite, regions, selected region, method for new
regions, zoom, preview state, undo/redo history, active gesture, and busy/load
generation counters. A generation counter prevents stale asynchronous image-load
or export callbacks from replacing the current session.

An empty-area drag draws; a region drag moves; a selected corner drag resizes.
Draw explicitly starts a new region over existing masks and returns to direct
editing afterward. Coordinate fields provide keyboard-accessible editing.

Export is unavailable without a region, while the original is shown, during an
unfinished gesture, while busy, or when no composite exists. Encoding freezes
controls and snapshots the pixels. Cosmetic regions require a second export
confirmation. Preview overlays and selection handles are not exported.

## Build and network boundary

`build.py` embeds CSS, JavaScript, fonts, icons, artwork, FAQ, and displayed evidence
images. It emits identical `index.html` and `BlueMask.html` bytes. Its CSP allows
the exact script/style hashes and local data/blob images, and uses
`connect-src 'none'`. The app has no storage, service worker, or telemetry feature.

Explicit navigation and downloads are separate from image processing: the brand
link opens Bluethroat's website, and hosted artifact links request static files.
The standalone edition disables links to unavailable companion downloads.
See [PRIVACY.md](PRIVACY.md) for the limits of these controls.
