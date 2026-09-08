#!/usr/bin/env python3
"""Check artifact integrity and rebuilding from the downloadable source archive."""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_build():
    subprocess.run([sys.executable, 'build.py'], cwd=ROOT, check=True)
    dist = ROOT / 'dist'
    manifest = json.loads((dist / 'manifest.json').read_text())
    for name, expected in manifest['artifacts'].items():
        actual = hashlib.sha256((dist / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f'Artifact checksum mismatch: {name}')
    if (dist / 'index.html').read_bytes() != (dist / 'BlueMask.html').read_bytes():
        raise RuntimeError('Hosted and offline editions differ')
    expected_sums = ''.join(f'{v}  {k}\n' for k, v in sorted(manifest['artifacts'].items()))
    if (dist / 'SHA256SUMS').read_text() != expected_sums:
        raise RuntimeError('SHA256SUMS does not match the manifest')

    with tempfile.TemporaryDirectory(prefix='bluemask-rebuild-') as directory:
        target = Path(directory)
        with zipfile.ZipFile(dist / 'bluemask-source.zip') as archive:
            for entry in archive.infolist():
                if not (target / entry.filename).resolve().is_relative_to(target.resolve()):
                    raise RuntimeError('Unexpected source archive path')
            archive.extractall(target)
        subprocess.run([sys.executable, 'build.py'], cwd=target, check=True, capture_output=True)
        for name in [*manifest['artifacts'], 'manifest.json', 'SHA256SUMS']:
            if (dist / name).read_bytes() != (target / 'dist' / name).read_bytes():
                raise RuntimeError(f'Source archive rebuild differs: {name}')
    print('PASS checksums, hosted/offline parity, and source archive reproduction')


if __name__ == '__main__':
    check_build()
