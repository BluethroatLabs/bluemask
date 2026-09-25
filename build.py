#!/usr/bin/env python3
"""Deterministic, dependency-free build of the hosted and offline BlueMask page."""
import base64
import hashlib
import html
import json
import mimetypes
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'

def data_uri(path):
    p = ROOT / path
    mime = {'.woff2': 'font/woff2', '.svg': 'image/svg+xml'}.get(p.suffix, mimetypes.guess_type(p)[0] or 'application/octet-stream')
    return 'data:' + mime + ';base64,' + base64.b64encode(p.read_bytes()).decode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def csp_hash(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"

def evidence():
    p = ROOT / 'evidence/ai/results.json'
    if not p.exists():
        return '<p>Model measurements are being prepared. No AI resistance result is claimed for this edition.</p>'
    result = json.loads(p.read_text())
    if result.get('status') != 'run':
        return '<p>No completed model evaluation is available for this edition.</p>'
    gaussian = next(r for r in result['summary'] if r['method'] == 'gaussian' and r['assumed_gaussian_sigma'] == 3)
    secure = next(r for r in result['summary'] if r['method'] == 'secure' and r['assumed_gaussian_sigma'] == 3)
    n = gaussian['samples']
    body = f'''<p class="evidence-kicker">{n} synthetic codes · Tested {html.escape(result['run_at_utc'][:10])}</p>
    <div class="table-scroll"><table class="evidence-table"><caption>DPIR / DRUNet (2021) · Exact codes read by OCR</caption><thead><tr><th>Method</th><th>Before recovery</th><th>After recovery</th></tr></thead><tbody>
    <tr><th>Gaussian blur</th><td>{gaussian['exact_ocr_before']} / {n}</td><td><strong>{gaussian['exact_ocr_after']} / {n}</strong></td></tr>
    <tr><th>BlueMask secure masking</th><td>{secure['exact_ocr_before']} / {n}</td><td><strong>{secure['exact_ocr_after']} / {n}</strong></td></tr>
    </tbody></table></div><p class="control-hint">All twelve secure inputs were identical. This small test does not establish protection against every image or AI model.</p>'''
    details = '''<details class="evidence-details"><summary>Test setup and limitations</summary><ul>
    <li>Twelve synthetic eight-digit codes, one font and fixed mask positions. Exact matches were measured with Apple Vision OCR.</li>
    <li>DPIR is an established 2021 baseline. The Gaussian control uses σ = 3 and a known kernel; it differs from BlueMask’s cosmetic blur.</li>
    <li>The twelve secure exports collapse to one identical input. They are not twelve independent model challenges. OCR failure alone does not prove that no information remains.</li>'''
    recent = ROOT / 'evidence/ai/darkir/results.json'
    if recent.exists():
        newer = json.loads(recent.read_text())
        row = next(r for r in newer['summary'] if r['method'] == 'gaussian' and r['gaussian_sigma'] == 3)
        details += f'''<li>DarkIR (CVPR 2025), a low-light photo model, failed the blur control: exact matches fell from {row['exact_ocr_before']}/{row['samples']} to {row['exact_ocr_after']}/{row['samples']}. Its failure on secure masks does not demonstrate resistance to a capable recovery attempt.</li>'''
    details += '</ul></details>'
    images = [
        ('Original', 'evidence/ai/fixtures/05-original.png', 'Synthetic code: 30008867.'),
        ('Blur → recovery', 'evidence/ai/outputs/05-gaussian-3_0-dpir.png', 'Exact code recovered.'),
        ('Secure mask → recovery', 'evidence/ai/outputs/05-secure-3_0-dpir.png', 'Code not recovered in this test.')
    ]
    body += '<div class="comparison-grid">'
    for title, path, caption in images:
        body += f'<figure class="comparison"><p class="eyebrow">{html.escape(title)}</p><img src="{data_uri(path)}" width="256" height="96" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>'
    body += '</div><p class="file-note">Example 05. All inputs and outputs are included in the download.</p>' + details
    body += '<p><a id="evidence-download" href="bluemask-model-evidence.zip" download>Download tests & outputs ↓</a></p>'
    return body

def build():
    OUT.mkdir(exist_ok=True)
    css = (ROOT / 'styles.css').read_text()
    css = re.sub(r'url\([\'\"]?(assets/[^\)\'\"]+)[\'\"]?\)', lambda m: 'url("' + data_uri(m[1]) + '")', css)
    engine = (ROOT / 'engine.js').read_text()
    app = (ROOT / 'app.js').read_text()
    theme_boot = (ROOT / 'theme-boot.js').read_text()
    theme = (ROOT / 'theme.js').read_text()
    scroll = (ROOT / 'privacy-scroll.html').read_text()
    licenses = '\n\n'.join(p.read_text() for p in sorted((ROOT / 'assets/fonts').glob('*OFL.txt'))).replace('--', '—')
    wordmark = (ROOT / 'assets/bluethroat-wordmark.svg').read_text()
    bluemask_full = (ROOT / 'assets/bluemask-full.svg').read_text()
    bluemask_small = (ROOT / 'assets/bluemask-small.svg').read_text()
    bluemask_full = re.sub(r'\sstyle="[^"]*"', '', bluemask_full)
    bluemask_small = re.sub(r'\sstyle="[^"]*"', '', bluemask_small)
    evidence_html = evidence()
    layout = (ROOT / 'layout.html').read_text()
    source = (ROOT / 'app.html').read_text()
    app_content, app_extras = source.split('<!-- APP_EXTRAS -->', 1)
    legal_template = (ROOT / 'legal-page.html').read_text()
    legal_pages = {
        'privacy': ('Privacy', 'How BlueMask handles images, exports, network access, and privacy limits.', (ROOT / 'legal/privacy.html').read_text()),
        'terms': ('Terms', 'Terms of use and important limitations for BlueMask.', (ROOT / 'legal/terms.html').read_text()),
        'support': ('Support', 'How to report BlueMask issues and security or privacy concerns.', (ROOT / 'legal/support.html').read_text()),
    }
    legal_source = ''.join(title + description + body for title, description, body in legal_pages.values())
    build_id = digest((''.join([layout, source, legal_template, legal_source, engine, app, theme_boot, theme, css, scroll, evidence_html, wordmark, bluemask_full, bluemask_small, licenses])).encode())[:12]
    csp = "; ".join(["default-src 'none'", 'script-src ' + ' '.join(map(csp_hash, [engine, app, theme_boot, theme])), 'style-src ' + csp_hash(css), "style-src-attr 'none'", "img-src 'self' data: blob:", 'font-src data:', "manifest-src 'self'", "connect-src 'none'", "object-src 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'none'"])
    values = {'CSP': csp, 'CSS': css, 'WORDMARK': wordmark, 'BLUEMASK_FULL': bluemask_full, 'BLUEMASK_SMALL': bluemask_small, 'EVIDENCE': evidence_html, 'BUILD_ID': build_id, 'PRIVACY_SCROLL': scroll, 'FONT_LICENSES': licenses, 'ENGINE': engine, 'THEME_BOOT': theme_boot, 'THEME': theme, 'APP': app}
    def render(template, replacements):
        page = template
        placeholder = re.compile(r'\{\{([A-Z_]+)\}\}')
        while match := placeholder.search(page):
            missing = sorted({m.group(1) for m in placeholder.finditer(page)} - replacements.keys())
            if missing:
                raise SystemExit('Unresolved build placeholder: ' + ', '.join(missing))
            page = placeholder.sub(lambda m: replacements[m.group(1)], page)
        return page
    page = render(layout, {
        **values,
        'PAGE_TITLE': 'BlueMask — Bluethroat Labs',
        'PAGE_DESCRIPTION': 'Mask private details in photos and screenshots. BlueMask by Bluethroat Labs works locally, with a downloadable offline edition.',
        'PAGE_CONTENT': app_content.strip(),
        'PAGE_EXTRAS': app_extras.strip(),
        'PAGE_SCRIPTS': '<script>{{ENGINE}}</script>\n<script>{{APP}}</script>',
    })
    encoded = page.encode()
    for name in ['index.html', 'BlueMask.html']:
        (OUT / name).write_bytes(encoded)
    for slug, (title, description, body) in legal_pages.items():
        legal_values = {
            **values,
            'LEGAL_TITLE': title,
            'LEGAL_BODY': body,
            'PAGE_TITLE': f'{title} — BlueMask',
            'PAGE_DESCRIPTION': description,
            'PAGE_CONTENT': legal_template,
            'PAGE_EXTRAS': '',
            'PAGE_SCRIPTS': '',
        }
        (OUT / f'{slug}.html').write_text(render(layout, legal_values))
    for favicon in (ROOT / 'assets/favicon').iterdir():
        if favicon.is_file(): shutil.copyfile(favicon, OUT / favicon.name)
    archive = ROOT / 'evidence/ai/bluemask-model-evidence.zip'
    if archive.exists(): shutil.copyfile(archive, OUT / archive.name)
    source_files = [ROOT / name for name in ['README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md', '.gitignore', '.gitattributes', 'layout.html', 'app.html', 'legal-page.html', 'app.js', 'theme-boot.js', 'theme.js', 'engine.js', 'styles.css', 'privacy-scroll.html', 'build.py', 'serve.py']]
    source_files += [p for p in (ROOT / 'legal').glob('*.html')]
    source_files += [p for p in (ROOT / 'scripts').iterdir() if p.is_file() and p.suffix in ['.mjs', '.py']]
    source_files += [p for p in (ROOT / 'docs').rglob('*.md')]
    source_files += [p for p in (ROOT / '.github').rglob('*.yml')]
    source_files += [p for p in (ROOT / 'research').iterdir() if p.is_file() and (p.suffix in ['.py', '.mjs', '.swift', '.md', '.json', '.txt'] or p.name == '.gitignore')]
    for directory in ['dpir', 'darkir', 'concertormer']:
        source_files += [p for p in (ROOT / 'research' / directory).rglob('*') if p.is_file() and (p.suffix in ['.py', '.yml'] or p.name == 'LICENSE')]
    source_files += [p for p in (ROOT / 'assets').rglob('*') if p.is_file()]
    # Include the exact inputs needed by the builder, not the development venv or weights.
    source_files += [p for p in (ROOT / 'evidence/ai').rglob('*') if p.is_file() and (p.suffix in ['.json', '.png', '.md', '.log'] or p.name == 'SHA256SUMS')]
    if archive.exists(): source_files.append(archive)
    with zipfile.ZipFile(OUT / 'bluemask-source.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source_files):
            entry = zipfile.ZipInfo(p.relative_to(ROOT).as_posix(), date_time=(2026, 9, 6, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            z.writestr(entry, p.read_bytes())
    (OUT / '_headers').write_text('/*\n  Referrer-Policy: no-referrer\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Content-Security-Policy: frame-ancestors \'none\'\n/*.html\n  Cache-Control: no-store\n')
    manifest_names = ['index.html', 'BlueMask.html', 'privacy.html', 'terms.html', 'support.html', '_headers', 'bluemask-source.zip']
    manifest = {'build_id': build_id, 'engine_sha256': digest(engine.encode()), 'artifacts': {name: digest((OUT / name).read_bytes()) for name in manifest_names}}
    if archive.exists(): manifest['artifacts'][archive.name] = digest(archive.read_bytes())
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(manifest['artifacts'].items())))
    print(json.dumps({'build_id': build_id, 'page_bytes': len(encoded), 'html_sha256': digest(encoded)}, indent=2))

if __name__ == '__main__': build()
