# BlueMask by Bluethroat Labs

Mask private details in photos and screenshots, locally in the browser.

People blur a seed phrase, an account number, or an address and then share the
screenshot. The blur looks finished. For text, it often is not. Pixelation and
Gaussian blur leave a measurement of the original pixels. When the alphabet is
small and the font, size, and baseline are known, an attacker can render
candidates, apply the same operator, and match the measurement. No model is
required. What comes back is the original string.

A solid mask is a different object. The covered region is a constant. Its
variance is zero, so every candidate scores the same. There is no ranking to
exploit and no compute budget that changes that.

That is why BlueMask replaces selected pixels by default, and why cosmetic blur
is labelled **Appearance only**.

Draw over sensitive details, review the result, and download a flattened PNG. There are
no accounts, image uploads, or runtime third-party dependencies.

**Status:** locally tested release candidate. The repository includes the editor,
self-contained offline build, synthetic model evidence, and verification scripts.
Public production sign-off and physical mobile-browser testing remain pending.

[Why it matters](#why-it-matters) · [Using BlueMask](#using-bluemask) ·
[Privacy](#privacy-design) · [Evidence](#model-evidence) ·
[Self-hosting](docs/SELF_HOSTING.md) · [Development](docs/DEVELOPMENT.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Contributing](CONTRIBUTING.md)

## Why it matters

One synthetic secret, four redactions, one attacker. The string is the
18-character hex address `0xB7e4Aa91cF3d0852`, rendered in a known monospace
font. The alphabet has 23 symbols, so a naive search is about 10^25
candidates. The error falls almost independently by character, so the search
collapses to tens of thousands of full re-renders. Nothing here is
probabilistic and nothing is a trained model.

| Redaction | Attack | Result |
| --- | --- | --- |
| Pixelation, 14px blocks | Render a candidate, apply the same mosaic, keep the closer match | Exact original. 19,566 renders, about a minute on one CPU core. |
| Gaussian blur, sigma 5 | Undo the convolution in the frequency domain. No search. | The text comes back. High frequencies are attenuated and still present in the signal. |
| Gaussian blur, sigma 9 | The same deconvolution, then the same search | Deconvolution is an unreadable smear. Search still returns the exact string. |
| Solid mask | The same search | Nothing. Region variance is 0.0. Every candidate scores identically. |

The heavy-blur row is the one that matters. The text looks destroyed, direct
inversion fails, and the secret still falls, because the signal that survives
is large compared with the number of strings it could have been. Heavier blur
raises the cost. The covered pixels remain a measurement.

The mask holds for a different reason. It is a constant fill, so the output
carries no mutual information about the covered pixels. Secure masking in
BlueMask removes those pixels before any cosmetic pass and paints an opaque
patch last. Changing source pixels inside a secure region cannot affect the
export when the region geometry stays fixed.

This demonstration has narrow limits, and they belong next to the result:

- It is about text. Exact recovery needs a small candidate space. A face has
  no alphabet. Machine-learning face deblurring produces a plausible face.
  Recovering the original face is a separate, weaker claim. BlueMask keeps the
  two results separate.
- The attacker needs the font, size, and baseline. That is realistic for
  interface screenshots, because the unredacted rest of the image is usually
  still there to calibrate from. It is a weaker assumption for an arbitrary
  photograph.
- JPEG recompression, rescaling, and screenshot scaling add noise and raise
  cost. For a constrained alphabet, the conclusion stays the same.
- The run used a clean synthetic render, quantised to 8-bit. A real screenshot
  adds antialiasing, subpixel rendering, and compression, which raises the
  number of renders. This run measured the clean render only.
- BlueMask's own cosmetic control is three passes of a box filter. That filter
  is still a measurement of the covered pixels. The Gaussian rows use a
  different operator, and a different setup from the DPIR / DarkIR experiment
  in [Model evidence](#model-evidence).

The method is prior art. [Unredacter](https://bishopfox.com/blog/unredacter-tool-never-pixelation)
(Dan Petro, Bishop Fox, 2022) recovers pixelated text the same way.
[Depix](https://github.com/spipm/Depix) recovers passwords from screenshots
processed with a linear box filter. The point of repeating it is the last row:
the redaction that holds is the one BlueMask does by default.

Run BlueMask from a clone, or open the offline file, with
[Self-hosting](docs/SELF_HOSTING.md).

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

The text-recovery demonstration above and this table answer different questions.
The demonstration shows that ordinary blur and pixelation of a short constrained
string can be matched back to the original. This table records two published
restoration models against twelve synthetic codes. Neither result is a claim
that BlueMask defeats every recovery method.

`dist/bluemask-model-evidence.zip` contains synthetic originals, processed images,
restoration outputs, measured OCR, model provenance, checksums and reproduction
instructions. Large model weights and development environments are excluded.

## Verification

Build integrity, source-archive reproduction, and the browser suites are run
with the commands in [Self-hosting](docs/SELF_HOSTING.md). Current coverage:
consent dialogs, secure defaults, export guards, generic PNG, PNG metadata
chunks, no image-processing HTTP requests, no web-storage writes, offline-file
open/mask/export, 160 seeded hidden-pixel perturbation cases with overlaps and
reversed order, real mouse/touch gestures, resize/undo, export races, and
recovery from rendering failures. Screenshots cover desktop, phone viewport,
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
| `docs/` | Self-hosting, architecture, development, privacy, release, and brand documentation |

Generated `dist/`, local environments, downloaded weights, caches, and the compiled
OCR helper are intentionally ignored. No application or research source code
depends on those files being committed.

