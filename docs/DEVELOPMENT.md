# Development

## Requirements

- Python 3.10 or newer for building and serving; only the standard library is used.
- Node.js 22 or newer for the browser checks. No `npm install` is needed.
- Google Chrome on macOS at its standard application path for the existing
  `scripts/browser.mjs` harness. It launches a temporary headless profile, disables
  extensions, and removes that profile after the run.
- Research reproduction has additional macOS/Swift/PyTorch requirements described
  in [research/README.md](../research/README.md); ordinary development needs none.

## Start the application

```sh
gh repo clone BluethroatLabs/bluemask
cd bluemask
python3 build.py
python3 serve.py --port 8791
```

Open `http://127.0.0.1:8791/`. The server binds to loopback and serves `dist/` only.
After changing source, run `python3 build.py` again and refresh. There is no dev
bundler or automatic rebuild. Editing `dist/` directly loses changes on rebuild.

## Checks

```sh
python3 scripts/check_build.py
```

This rebuilds, verifies artifact hashes and hosted/offline parity, extracts the
source archive into a temporary directory, and checks that rebuilding it produces
the same artifacts. GitHub Actions runs this check and JavaScript syntax checks
on pushes and pull requests. CI does not run the macOS browser or AI suites.

With the local server running in another terminal:

```sh
node scripts/verify.mjs
node scripts/interactions.mjs
```

`verify.mjs` accepts an optional URL argument. `interactions.mjs` currently expects
port 8791. The browser suites write reports and screenshots to `evidence/runtime/`.
The two committed runtime reports represent one recorded build, identified by
`html_sha256`; rerunning a suite replaces its report. Do not interpret an older
report as validation of a changed HTML file.

Coverage includes consent and export guards, local/offline operation, PNG output,
metadata, storage/network observations, pixel non-interference, direct mouse/touch
editing, undo, export races, and rendering-failure recovery. Mobile emulation is
not physical iOS/Safari or Android testing.

## Research and evidence

Keep model evaluation separate from app development. The committed synthetic PNGs
are the reference dataset. Generating fixtures can overwrite them and can differ
with font rasterization across systems. Work on a branch before changing a run.

`research/README.md` documents dependencies, pinned source/checkpoints, Swift OCR,
and execution commands. Preserve source licenses and record any model or harness
change. `research/concertormer/` is an inspected candidate subset, not a complete
runner or a measured result.

## Files intentionally not committed

`dist/` is reproducible output. Virtual environments, model checkpoints, the
compiled Swift helper, bytecode, caches, local configuration, and most browser
screenshots are excluded. Their source or regeneration instructions are included.
The measured AI inputs/outputs and evidence archives remain committed.

The browser harness currently targets Chrome on macOS. Building and the static
build checks work without that browser; a Linux or Windows browser harness needs
an explicit implementation and verification before claiming support.
