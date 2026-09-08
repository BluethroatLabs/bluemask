# BlueMask synthetic model benchmark

Read `../evidence/ai/status.json` first. Only `status: "run"` plus a completed
`results.json` represents an executed evaluation. Source code or downloaded
weights alone do not establish a result.

This research harness is separate from BlueMask's browser code. BlueMask does
not load an AI model, Python, OCR engine or network service to mask pictures.
Every benchmark original is an artificial eight-digit token generated here.
The harness does not accept personal-image paths or arbitrary input directories.

The released model is **DPIR with DRUNet grayscale (2021)**. It is an established
learned deblurring baseline, not a current frontier claim. See
[MODEL_SELECTION.md](MODEL_SELECTION.md) for selection and unrun candidates.

## Inputs and controls

- Twelve 256×96 synthetic images, eight-digit strings, one font, fixed geometry.
- Unredacted originals establish the OCR measurement's basic ability to read them.
- Conventional full-image Gaussian blur at sigma 2 and 3 is generated with a
  truncated separable kernel, circular boundary conditions and PNG quantization.
  The restoration baseline receives the exact kernel used for each blur.
- Secure fixtures use the real `BlueMaskEngine.render` function, exported through
  Chrome while browser network emulation is offline. Engine and browser provenance
  is recorded separately. Their marked pixels are replaced with RGB 110,113,118.
- The deblurring baseline attempts the same sigma settings on secure exports.
  All twelve masked images should be identical because all differences are inside
  the same fixed mask. Reused identical inference inputs are explicitly recorded.

The grayscale model uses the released architecture and weights, eight iterations,
no x8 augmentation, model-noise schedule 49→1, and regularization noise 1/255.
`run_dpir.py` expresses DPIR's scale-factor-1 data update directly with NumPy FFTs;
only the learned denoiser runs on MPS when available. Its source documents the
numerical adaptation. No parameter sweep or retraining is performed.

OCR is Apple Vision's accurate English recognizer with language correction off.
Exact recovery requires the entire original token in one OCR line after whitespace
removal. Every transcription is retained. Region PSNR is secondary image similarity,
not a privacy score or a recovery verdict. A visually plausible reconstruction does
not count unless it matches the known original.

## Local reproduction on macOS arm64

Prerequisites: Python 3.14, Node, Google Chrome at the standard application path,
Xcode command-line tools/Swift, and the system Menlo font. Install research
dependencies into an isolated environment:

```sh
cd research
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
swiftc ocr.swift -o vision-ocr
```

DPIR source is pinned in `dpir-source.json`; the required architecture, helper,
reference driver and upstream MIT license are under `dpir/`. Download only
`drunet_gray.pth` from the URL in `MODEL_SELECTION.md`'s official downloader to
`research/models/drunet_gray.pth`. The executed checkpoint is 130,569,961 bytes,
SHA-256 `e27fb29456732c604c8ee3ac3e92ecadd2a7a4e36a8be675e92ebbf93a240de4`.
Verify both before reproducing. A `.partial` file is incomplete and must never
be loaded as a model.

From the project root:

```sh
research/.venv/bin/python research/generate_fixtures.py
node research/render_fixtures.mjs
research/.venv/bin/python research/run_dpir.py
```

The recorded run used macOS `sandbox-exec` to deny network operations to the
benchmark process and its child OCR process; the exact command is in
`../evidence/ai/execution-provenance.json`. This did not disconnect the device's
internet. Package downloads occurred earlier, outside the inference sandbox.

The stored original PNGs and manifest are the reference dataset; font rasterization
can differ on another OS. All inference uses local data. No paid API, cloud resource,
credentials or private image is involved.

## Publication boundary

Publish the sample count, model/version, before/after exact-match counts, inputs,
outputs, transcriptions and limitations together. If the conventional-blur control
does not improve, say so; a weak or mismatched attack cannot support a broad privacy
claim. Even successful controls do not turn twelve trials into a statistical,
all-model or anonymity guarantee. This experiment does not test faces, documents,
pixelation, inpainting, multi-image composition or inference from unmasked context.

## Recent-model cross-check

`run_darkir.py` evaluates the unchanged official DarkIR-m checkpoint from CVPR
2025 on exactly the same PNG inputs. See `../evidence/ai/darkir/SUMMARY.md` and
`results.json` there. This model made the Gaussian-blur controls less readable;
its secure-mask result is therefore not used as supporting evidence for a broad
privacy claim. Its intended domain is low-light photographs, unlike these inputs.

Reproduce after the fixture commands above by downloading the exact checkpoint
URL in `darkir-source.json` to `models/DarkIR_384.pt`, verifying its SHA-256, and
running `.venv/bin/python run_darkir.py` from `research/`. No extra Python packages
are required. The published run uses CPU so the official complex FFT operations
work without changing the architecture. The code's MIT license is retained under
`darkir/LICENSE`; the official model card lists the checkpoint as CC-BY-4.0.
DarkIR is by Daniel Feijoo, Juan C. Benito, Alvaro Garcia and Marcos V. Conde.
