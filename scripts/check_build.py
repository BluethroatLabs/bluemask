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
    hosted = (dist / 'index.html').read_text()
    offline = (dist / 'BlueMask.html').read_text()
    if hosted == offline:
        raise RuntimeError('Hosted and offline editions must use separate packaging')
    if len(hosted.encode()) >= 250_000 or 'data:font/' in hosted or 'privacy-scroll.webp' in hosted:
        raise RuntimeError('Hosted editor still contains self-contained offline assets')
    if '/assets/' not in hosted or '<script src="/assets/' not in hosted:
        raise RuntimeError('Hosted editor does not use fingerprinted shared assets')
    if '/assets/' in offline or '<link rel="stylesheet"' in offline:
        raise RuntimeError('Offline edition contains external asset references')
    required_pages = {
        'about': ('<h1', 'About BlueMask', f'<link rel="canonical" href="https://bluemask.bluethroatlabs.com/about">'),
        'tests': ('<h1', 'BlueMask recovery tests and limitations', f'<link rel="canonical" href="https://bluemask.bluethroatlabs.com/tests">'),
        'offline': ('<h1', 'Use BlueMask offline', f'<link rel="canonical" href="https://bluemask.bluethroatlabs.com/offline">'),
        'guides/redact-sensitive-information-from-screenshots': ('<h1', 'How to redact sensitive information from a screenshot', '<meta property="og:type" content="article">'),
    }
    for name, needles in required_pages.items():
        text = (dist / name).read_text()
        if any(needle not in text for needle in needles):
            raise RuntimeError(f'Permanent page is incomplete: {name}')
    branded_pages = ['index.html', 'BlueMask.html', *required_pages, 'privacy', 'terms', 'support']
    for name in branded_pages:
        if '<header class="topbar">' not in (dist / name).read_text() or '<header class="productbar">' not in (dist / name).read_text():
            raise RuntimeError(f'Page is missing shared company or product branding: {name}')
    offline_page = (dist / 'offline').read_text()
    for artifact in ['index.html', 'BlueMask.html', 'bluemask-source.zip', 'bluemask-model-evidence.zip']:
        if manifest['artifacts'][artifact] not in offline_page:
            raise RuntimeError(f'Offline page does not show the generated hash for {artifact}')
    if '{{' in ''.join((dist / name).read_text() for name in required_pages):
        raise RuntimeError('A permanent page contains an unresolved build placeholder')
    if 'SIL Open Font License' not in hosted or 'SIL Open Font License' not in offline:
        raise RuntimeError('Font license notices are missing from an editor package')
    legacy_redirects = {'privacy.html': '/privacy', 'terms.html': '/terms', 'support.html': '/support'}
    redirects_file = (dist / '_redirects').read_text()
    server = (ROOT / 'serve.py').read_text()
    bicep = (ROOT / 'infra' / 'main.bicep').read_text()
    app_source = (ROOT / 'app.js').read_text()
    for filename, target in legacy_redirects.items():
        page = (dist / filename).read_text()
        if f'url={target}' not in page or f'href="https://bluemask.bluethroatlabs.com{target}"' not in page or '<header class="topbar">' in page:
            raise RuntimeError(f'Legacy address is not a redirect: {filename}')
        if f'/{filename} {target} 301' not in redirects_file:
            raise RuntimeError(f'Static redirect file is missing {filename}')
        if f"'/{filename}': '{target}'" not in server:
            raise RuntimeError(f'serve.py does not redirect /{filename}')
        if f"source: '/{filename}'" not in bicep or f"target: '{target}'" not in bicep:
            raise RuntimeError(f'Front Door does not redirect /{filename}')
    if "location.replace('/about')" not in app_source or "location.replace('/tests')" not in app_source:
        raise RuntimeError('Hosted editor does not forward legacy About and Tests hashes')
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
    print('PASS checksums, hosted/offline split, permanent pages, and source archive reproduction')


if __name__ == '__main__':
    check_build()
