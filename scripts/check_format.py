#!/usr/bin/env python3
"""Check repository-owned text files for whitespace formatting errors."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".bicep",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".svg",
    ".txt",
    ".yaml",
    ".yml",
}
EXCLUDED_PREFIXES = (
    "evidence/",
    "research/concertormer/",
    "research/darkir/",
    "research/dpir/",
)
EXCLUDED_PATHS = {
    "assets/favicon/favicon.svg",
    "assets/fonts/Geist-Mono-OFL.txt",
    "assets/fonts/Instrument-Serif-OFL.txt",
    "research/dpir-source.json",
}


def tracked_text_files():
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=False,
    )
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode()
        if relative in EXCLUDED_PATHS or relative.startswith(EXCLUDED_PREFIXES):
            continue
        path = ROOT / relative
        if path.suffix in TEXT_SUFFIXES:
            yield relative, path


def main():
    errors = []
    for relative, path in tracked_text_files():
        data = path.read_bytes()
        if b"\r\n" in data:
            errors.append(f"{relative}: contains CRLF line endings")
        if data and not data.endswith(b"\n"):
            errors.append(f"{relative}: missing final newline")
        for line_number, line in enumerate(data.splitlines(), start=1):
            if line.rstrip(b" \t") != line:
                errors.append(f"{relative}:{line_number}: trailing whitespace")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("Text formatting is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
