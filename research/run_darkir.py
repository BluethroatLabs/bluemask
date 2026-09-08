"""One recent released model on the same fixed synthetic inputs; no user images.

DarkIR targets low-light photographic restoration. White-background Gaussian
screenshots are outside that distribution. The unchanged official architecture
is evaluated with its default LOLBlur configuration and official checkpoint.
"""
from pathlib import Path
import datetime
import hashlib
import json
import platform
import subprocess
import sys
import time

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
EVIDENCE = ROOT / "evidence/ai"
OUT = EVIDENCE / "darkir"
sys.path.insert(0, str(RESEARCH / "darkir/archs"))
from DarkIR import DarkIR


def main():
    started = time.monotonic()
    OUT.mkdir(exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    manifest = json.loads((EVIDENCE / "fixtures/manifest.json").read_text())
    assert manifest["synthetic_only"] and manifest["sample_count"] == 12
    provenance = json.loads((RESEARCH / "darkir-source.json").read_text())
    weights = RESEARCH / "models/DarkIR_384.pt"
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == provenance["weights_sha256"]
    torch.set_num_threads(4)
    torch.manual_seed(0)
    # CPU supports the upstream complex FFT operations without an architecture port.
    device = torch.device("cpu")
    model = DarkIR()
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True)["params"], strict=True)
    model.eval().requires_grad_(False).to(device)
    rows, cache = [], {}
    with torch.inference_mode():
        for item in manifest["samples"]:
            for method, sigma, path in [
                ("clear", None, ROOT / item["original"]),
                ("gaussian", 2, EVIDENCE / "fixtures" / (item["id"] + "-gaussian-2_0.png")),
                ("gaussian", 3, EVIDENCE / "fixtures" / (item["id"] + "-gaussian-3_0.png")),
                ("secure", None, EVIDENCE / "fixtures" / (item["id"] + "-secure.png")),
            ]:
                arr = np.asarray(Image.open(path).convert("RGB"))
                key = hashlib.sha256(arr.tobytes()).hexdigest()
                reused = key in cache
                if not reused:
                    tensor = torch.from_numpy(arr.astype(np.float32) / 255).permute(2, 0, 1)[None].to(device)
                    restored = model(tensor)[0].permute(1, 2, 0).cpu().numpy()
                    cache[key] = np.clip(np.round(restored * 255), 0, 255).astype(np.uint8)
                output = OUT / "outputs" / f"{item['id']}-{method}-{sigma or 0}-darkir.png"
                Image.fromarray(cache[key]).save(output)
                rows.append({"id": item["id"], "secret": item["secret"], "method": method,
                             "gaussian_sigma": sigma, "input": path.relative_to(ROOT).as_posix(),
                             "output": output.relative_to(ROOT).as_posix(),
                             "inference_reused_identical_input": reused})
    paths = sorted({r[k] for r in rows for k in ("input", "output")})
    proc = subprocess.run([str(RESEARCH / "vision-ocr"), *[str(ROOT / p) for p in paths]],
                          check=True, capture_output=True, text=True)
    ocr = json.loads(proc.stdout)
    for r in ocr:
        r["file"] = Path(r["file"]).relative_to(ROOT).as_posix()
    assert all("error" not in r for r in ocr)
    by_path = {r["file"]: r for r in ocr}
    for row in rows:
        for stage in ("input", "output"):
            texts = [i["text"] for i in by_path[row[stage]]["observations"]]
            row[stage + "_ocr_text"] = texts
            row[stage + "_exact_secret_match"] = row["secret"] in ["".join(t.split()) for t in texts]
    summary = []
    for method, sigma in [("clear", None), ("gaussian", 2), ("gaussian", 3), ("secure", None)]:
        subset = [r for r in rows if r["method"] == method and r["gaussian_sigma"] == sigma]
        summary.append({"method": method, "gaussian_sigma": sigma, "samples": len(subset),
                        "exact_ocr_before": sum(r["input_exact_secret_match"] for r in subset),
                        "exact_ocr_after": sum(r["output_exact_secret_match"] for r in subset),
                        "new_exact_recoveries": sum(not r["input_exact_secret_match"] and r["output_exact_secret_match"] for r in subset),
                        "lost_exact_recoveries": sum(r["input_exact_secret_match"] and not r["output_exact_secret_match"] for r in subset)})
    result = {"schema_version": 1, "status": "run", "synthetic_only": True,
              "run_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "model": {"name": "DarkIR-m / DarkIR_384", "conference": "CVPR 2025", "year": 2025,
                        "training_domain": "Low-light photographic restoration, LOLBlur configuration",
                        "distribution_mismatch": "White-background synthetic Gaussian-blurred text is outside its advertised low-light photographic domain.",
                        "parameters": sum(p.numel() for p in model.parameters()), "provenance": provenance,
                        "configuration": {"width": 32, "middle_blk_num_enc": 2, "middle_blk_num_dec": 2,
                                          "enc_blk_nums": [1, 2, 3], "dec_blk_nums": [3, 1, 1], "dilations": [1, 4, 9], "extra_depth_wise": True},
                        "architecture_modified": False, "kernel_supplied": False},
              "environment": {"platform": platform.platform(), "python": platform.python_version(),
                              "torch": torch.__version__, "numpy": np.__version__, "device": str(device),
                              "ocr": "Apple Vision accurate en-US, language correction off",
                              "ocr_revision": sorted({r["revision"] for r in ocr})},
              "fixture_manifest_sha256": hashlib.sha256((EVIDENCE / "fixtures/manifest.json").read_bytes()).hexdigest(),
              "wall_seconds": round(time.monotonic() - started, 3), "unique_inference_inputs": len(cache),
              "summary": summary, "rows": rows,
              "limitations": ["This is a recent released model, not an established strongest/current-frontier ranking.",
                              "A model that fails to improve blur controls on these out-of-distribution screenshots cannot substantiate broad resistance claims.",
                              "Twelve synthetic strings, one font, fixed geometry; no people, private images, low-light photo scenes, inpainting or contextual inference.",
                              "All secure images are identical. Only one secure model inference is performed and openly reused.",
                              "OCR exact-match failure does not establish absence of recoverable information for other readers or models."]}
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "ocr-results.json").write_text(json.dumps(ocr, indent=2) + "\n")
    (OUT / "status.json").write_text(json.dumps({"status": "run", "model": result["model"]["name"], "year": 2025, "summary": summary}, indent=2) + "\n")
    print(json.dumps({"seconds": result["wall_seconds"], "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
