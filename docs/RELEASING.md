# Building and releasing

The repository contains a locally tested release candidate. Creating this GitHub
repository does not deploy the website or establish production sign-off.

## Build artifacts

```sh
python3 scripts/check_build.py
```

| Output in `dist/` | Purpose |
| --- | --- |
| `index.html` | Hosted application |
| `BlueMask.html` | Identical standalone offline edition |
| `bluemask-source.zip` | Source, documentation, and inputs needed to rebuild |
| `bluemask-model-evidence.zip` | Recorded synthetic experiment and reproduction files |
| `manifest.json` | Build ID, engine hash, and artifact SHA-256 values |
| `SHA256SUMS` | Hash list for distribution verification |
| `_headers` | Static-hosting security-header configuration |

The source archive rebuild check uses the current Python/compression environment.
Record that environment with a release; cross-environment compression equivalence
has not been established. Model measurements and their archived provenance are
historical records. Updating docs or packaging does not constitute a new AI run.

## Before publishing a release

1. Run the browser suites against the final build and retain the reports' HTML
   hashes. Verify direct drawing, movement, resizing, consent, and PNG export.
2. Check real Safari/iOS and Android devices, including an offline-file import and
   export. Emulated phone checks do not complete this step.
3. Review the final source and third-party notices. Select project licensing before
   making an open-source licensing claim. Keep internal product notes out of the
   hosted distribution.
4. If the renderer changed, regenerate and evaluate synthetic fixtures before
   attaching old model claims to it. Publish controls and limitations together.
5. Establish release signing and independently distributed verification material
   before claiming signed or independently verified releases.

## Hosting

Deploy only `dist/` to a static HTTPS host. Apply `_headers` or the platform's
equivalent configuration. Disable injected analytics and other host-added scripts.
Do not deploy the development server, repository root, research environment, model
weights, or session notes. No API, database, or image-upload service is required.

After deployment, inspect response headers and compare served HTML with the
intended build. Check image processing for network requests and test the downloaded
offline edition while disconnected. A local test is not evidence about bytes
modified by a hosting platform.

Tag the reviewed commit and attach the built files to a release when publication
is approved. The current manifest is unsigned; do not label it a signature.
