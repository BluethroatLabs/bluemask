"""Package explicit public synthetic receipts, excluding environments and weights."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evidence/ai"
result = json.loads((OUT / "results.json").read_text())
assert result["status"] == "run" and result["synthetic_only"]
paths = []
for path in OUT.rglob("*"):
    if path.is_file() and path.suffix in {".png", ".json", ".md", ".log"} and path.name != "bundle.json":
        paths.append(path)
for name in ["README.md", "MODEL_SELECTION.md", "requirements.txt", "environment-lock.txt",
             "generate_fixtures.py", "render_fixtures.mjs", "run_dpir.py", "ocr.swift",
             "package_evidence.py", "dpir-source.json", "run_darkir.py", "darkir-source.json"]:
    paths.append(ROOT / "research" / name)
for source_dir in ("dpir", "darkir"):
    paths.extend(p for p in (ROOT / "research" / source_dir).rglob("*")
                 if p.is_file() and (p.suffix in (".py", ".yml") or p.name == "LICENSE"))
paths += [ROOT / "engine.js", ROOT / "scripts/browser.mjs"]
paths = sorted(set(paths))
assert json.loads((OUT / "render-provenance.json").read_text())["engine_sha256"] == hashlib.sha256((ROOT / "engine.js").read_bytes()).hexdigest(), "Renderer changed; refresh fixtures before packaging"
checksums = "".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(ROOT).as_posix() + "\n" for p in paths)
(OUT / "SHA256SUMS").write_text(checksums)
archive = OUT / "bluemask-model-evidence.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in [*paths, OUT / "SHA256SUMS"]:
        info = zipfile.ZipInfo(p.relative_to(ROOT).as_posix(), (2026, 9, 6, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, p.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
(OUT / "bundle.json").write_text(json.dumps({
    "file": archive.name, "bytes": archive.stat().st_size,
    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": len(paths) + 1,
    "synthetic_only": True, "model_weights_included": False,
    "environment_included": False, "reproduction_entrypoint": "research/README.md"
}, indent=2) + "\n")
print((OUT / "bundle.json").read_text())
