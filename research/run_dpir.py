"""A fixed synthetic-only DPIR/DRUNet benchmark, not a user-image restoration tool.

The released DRUNet architecture and weights are used without modification. The
sf=1 half-quadratic data update is written directly with modern CPU FFTs; only
the denoiser runs on MPS when available. Gaussian controls give the evaluator
the exact kernel. No search, retraining, candidate dictionary or secret input.
"""
from pathlib import Path
import datetime
import hashlib
import json
import math
import platform
import subprocess
import sys
import time

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
OUT = ROOT / "evidence/ai"
sys.path.insert(0, str(RESEARCH / "dpir"))
from models.network_unet import UNetRes
from utils.utils_pnp import get_rho_sigma

SIGMAS = [2.0, 3.0]
ITERATIONS = 8


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kernel_fft(sigma, shape):
    radius = math.ceil(4 * sigma)
    coords = np.arange(-radius, radius + 1, dtype=np.float64)
    one = np.exp(-(coords ** 2) / (2 * sigma * sigma))
    one /= one.sum()
    kernel = np.outer(one, one)
    padded = np.zeros(shape)
    padded[:len(one), :len(one)] = kernel
    padded = np.roll(padded, (-radius, -radius), axis=(0, 1))
    return np.fft.fft2(padded)


def uint8(arr):
    return np.clip(np.round(arr * 255), 0, 255).astype(np.uint8)


def save(arr, path):
    Image.fromarray(uint8(arr)).save(path)


def restore(observed, sigma, model, device):
    # Algebraic sf=1 equivalent of DPIR utils_sisr.data_solution.
    transfer = kernel_fft(sigma, observed.shape)
    spectrum = np.conj(transfer) * np.fft.fft2(observed)
    magnitude = np.abs(transfer) ** 2
    rhos, levels = get_rho_sigma(sigma=1 / 255, iter_num=ITERATIONS,
                                modelSigma1=49, modelSigma2=1, w=1)
    current = observed.copy()
    with torch.inference_mode():
        for rho, level in zip(rhos, levels):
            current = np.fft.ifft2((spectrum + rho * np.fft.fft2(current)) /
                                  (magnitude + rho)).real
            image = torch.from_numpy(current.astype(np.float32))[None, None]
            noise_map = torch.full_like(image, float(level))
            current = model(torch.cat([image, noise_map], dim=1).to(device)).cpu().numpy()[0, 0]
    return np.clip(current, 0, 1)


def crop_psnr(arr, expected):
    mse = float(np.mean((arr[36:84, 24:232] - expected[36:84, 24:232]) ** 2))
    return None if mse == 0 else 10 * math.log10(1 / mse)


def main():
    started = time.monotonic()
    manifest = json.loads((OUT / "fixtures/manifest.json").read_text())
    assert manifest["synthetic_only"] and manifest["sample_count"] == 12
    source = json.loads((RESEARCH / "dpir-source.json").read_text())
    weights = RESEARCH / "models/drunet_gray.pth"
    torch.set_num_threads(4)
    torch.manual_seed(0)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = UNetRes(in_nc=2, out_nc=1, nc=[64, 128, 256, 512], nb=4,
                    act_mode="R", downsample_mode="strideconv", upsample_mode="convtranspose")
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True), strict=True)
    model.eval().requires_grad_(False).to(device)
    (OUT / "outputs").mkdir(exist_ok=True)
    rows, restore_cache = [], {}
    for item in manifest["samples"]:
        original_path = ROOT / item["original"]
        original = np.asarray(Image.open(original_path).convert("L"), dtype=np.float64) / 255
        secure_path = OUT / "fixtures" / (item["id"] + "-secure.png")
        if not secure_path.exists():
            raise RuntimeError(f"Actual BlueMask render required before evaluation: {secure_path}")
        secure = np.asarray(Image.open(secure_path).convert("L"), dtype=np.float64) / 255
        rows.append({"id": item["id"], "method": "clear", "secret": item["secret"],
                     "input": original_path.relative_to(ROOT).as_posix(), "output": None,
                     "input_roi_psnr_db": None, "output_roi_psnr_db": None})
        for sigma in SIGMAS:
            suffix = str(sigma).replace(".", "_")
            blurred = np.fft.ifft2(np.fft.fft2(original) * kernel_fft(sigma, original.shape)).real
            blur_path = OUT / "fixtures" / f"{item['id']}-gaussian-{suffix}.png"
            save(blurred, blur_path)
            # Restore exactly the quantized PNG a reader receives.
            blurred = np.asarray(Image.open(blur_path), dtype=np.float64) / 255
            for method, observed, input_path in [("gaussian", blurred, blur_path),
                                                  ("secure", secure, secure_path)]:
                key = (hashlib.sha256(observed.tobytes()).hexdigest(), sigma)
                run_start = time.monotonic()
                reused = key in restore_cache
                if not reused:
                    restore_cache[key] = restore(observed, sigma, model, device)
                restored = restore_cache[key]
                output_path = OUT / "outputs" / f"{item['id']}-{method}-{suffix}-dpir.png"
                save(restored, output_path)
                rows.append({"id": item["id"], "method": method, "secret": item["secret"],
                             "assumed_gaussian_sigma": sigma,
                             "input": input_path.relative_to(ROOT).as_posix(),
                             "output": output_path.relative_to(ROOT).as_posix(),
                             "input_roi_psnr_db": crop_psnr(observed, original),
                             "output_roi_psnr_db": crop_psnr(uint8(restored) / 255, original),
                             "inference_reused_identical_input": reused,
                             "wall_seconds": round(time.monotonic() - run_start, 4)})
                print(f"{item['id']} {method} sigma={sigma} reused={reused}", flush=True)
    paths = sorted({row[k] for row in rows for k in ("input", "output") if row[k]})
    ocr_process = subprocess.run([str(RESEARCH / "vision-ocr"), *[str(ROOT / p) for p in paths]],
                                 check=True, capture_output=True, text=True)
    ocr = json.loads(ocr_process.stdout)
    # Public receipts use repository-relative paths, never laptop usernames.
    for observation in ocr:
        observation["file"] = str(Path(observation["file"]).relative_to(ROOT))
    (OUT / "ocr-results.json").write_text(json.dumps(ocr, indent=2) + "\n")
    by_path = {r["file"]: r for r in ocr}
    for row in rows:
        for stage in ("input", "output"):
            if not row[stage]:
                continue
            result = by_path[row[stage]]
            texts = [r["text"] for r in result.get("observations", [])]
            # Exact full OCR line after removing whitespace; no fuzzy matching.
            row[stage + "_ocr_text"] = texts
            row[stage + "_exact_secret_match"] = row["secret"] in ["".join(t.split()) for t in texts]
    summary = []
    for method, sigma in [("clear", None), *[(m, s) for m in ("gaussian", "secure") for s in SIGMAS]]:
        subset = [r for r in rows if r["method"] == method and r.get("assumed_gaussian_sigma") == sigma]
        summary.append({"method": method, "assumed_gaussian_sigma": sigma, "samples": len(subset),
                        "exact_ocr_before": sum(r["input_exact_secret_match"] for r in subset),
                        "exact_ocr_after": None if method == "clear" else sum(r["output_exact_secret_match"] for r in subset),
                        "mean_roi_psnr_before_db": None if method == "clear" else float(np.mean([r["input_roi_psnr_db"] for r in subset])),
                        "mean_roi_psnr_after_db": None if method == "clear" else float(np.mean([r["output_roi_psnr_db"] for r in subset]))})
    result = {"schema_version": 1, "status": "run", "synthetic_only": True,
              "run_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "model": {"name": "DPIR with DRUNet grayscale", "year": 2021,
                        "classification": "Established released baseline; not a current frontier claim",
                        "source": source, "weights_url": "https://github.com/cszn/KAIR/releases/download/v1.0/drunet_gray.pth",
                        "weights_sha256": sha(weights), "weights_bytes": weights.stat().st_size,
                        "iterations": ITERATIONS, "x8_augmentation": False,
                        "regularization_noise_level": 1 / 255, "model_sigma_start": 49, "model_sigma_end": 1},
              "environment": {"platform": platform.platform(), "python": platform.python_version(),
                              "torch": torch.__version__, "numpy": np.__version__, "device": str(device),
                              "ocr": "Apple Vision VNRecognizeTextRequest, accurate, en-US, no language correction",
                              "ocr_revision": sorted({r["revision"] for r in ocr if "revision" in r})},
              "fixture_manifest_sha256": sha(OUT / "fixtures/manifest.json"),
              "fixture_count": len(manifest["samples"]), "unique_inference_inputs": len(restore_cache),
              "secure_unique_png_hashes": len({sha(OUT / 'fixtures' / (i['id'] + '-secure.png')) for i in manifest['samples']}),
              "wall_seconds": round(time.monotonic() - started, 3), "summary": summary, "rows": rows,
              "limitations": ["Twelve synthetic 8-digit tokens, one font and fixed geometry; no faces or real documents.",
                              "Gaussian controls are full-image synthetic known-kernel blur, not BlueMask cosmetic mode.",
                              "Secure images come from the product canvas renderer; generation provenance is recorded separately.",
                              "A deblurring model is not an inpainting model, context-inference model or exhaustive privacy adversary.",
                              "The same masked image is shared by twelve different originals; cached identical inference is disclosed.",
                              "Apple Vision OCR can miss readable characters. Exact-match failure is not proof of no leakage.",
                              "No statistical population guarantee, all-model guarantee, anonymity guarantee or AI-proof claim."]}
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "status.json").write_text(json.dumps({"status": "run", "model": result["model"]["name"],
                                                 "result_file": "results.json", "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
