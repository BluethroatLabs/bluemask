"""Generate only artificial, non-personal benchmark originals. No user-image input."""
from pathlib import Path
import hashlib
import json
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evidence/ai/fixtures"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("/System/Library/Fonts/Menlo.ttc")
font = ImageFont.truetype(str(FONT), 28)
label = ImageFont.truetype(str(FONT), 11)
rng = random.Random(20260906)
entries = []
for index in range(12):
    secret = "".join(str(rng.randrange(10)) for _ in range(8))
    original = Image.new("RGB", (256, 96), (247, 247, 247))
    draw = ImageDraw.Draw(original)
    draw.text((16, 10), "SYNTHETIC BENCHMARK", font=label, fill=(90, 90, 90))
    draw.text((32, 41), secret, font=font, fill=(20, 20, 20))
    file = OUT / f"{index:02d}-original.png"
    original.save(file)
    entries.append({"id": f"{index:02d}", "secret": secret,
                    "original": file.relative_to(ROOT).as_posix(),
                    "region": {"x": 24, "y": 36, "w": 208, "h": 48, "method": "secure"}})
manifest = {"synthetic_only": True, "seed": 20260906, "sample_count": len(entries),
            "font_path": str(FONT), "font_sha256": hashlib.sha256(FONT.read_bytes()).hexdigest(),
            "font_size": 28, "image_size": [256, 96], "samples": entries}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"generated": len(entries), "manifest": str(OUT / "manifest.json")}))
