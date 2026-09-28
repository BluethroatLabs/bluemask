#!/usr/bin/env python3
"""Deterministic, dependency-free hosted and offline builds for BlueMask."""
import base64
import hashlib
import json
import mimetypes
import re
import shutil
import struct
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
ORIGIN = 'https://bluemask.bluethroatlabs.com'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def data_uri(path):
    p = ROOT / path
    mime = {
        '.woff2': 'font/woff2',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }.get(p.suffix, mimetypes.guess_type(p)[0] or 'application/octet-stream')
    return 'data:' + mime + ';base64,' + base64.b64encode(p.read_bytes()).decode()


def csp_hash(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def render(template, replacements):
    page = template
    placeholder = re.compile(r'\{\{([A-Z0-9_]+)\}\}')
    while placeholder.search(page):
        missing = sorted({m.group(1) for m in placeholder.finditer(page)} - replacements.keys())
        if missing:
            raise SystemExit('Unresolved build placeholder: ' + ', '.join(missing))
        page = placeholder.sub(lambda match: replacements[match.group(1)], page)
    return page


def fingerprinted_name(relative, data):
    path = Path(relative)
    return f'assets/{path.stem}.{digest(data)[:12]}{path.suffix}'


def write_fingerprinted(relative, data):
    name = fingerprinted_name(relative, data)
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return '/' + name


def png_chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)


def social_image():
    """Generate a small, deterministic 1200×630 monochrome social card."""
    width, height = 1200, 630
    paper = (222, 222, 218)
    ink = (18, 18, 18)
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            color = paper
            if x in (72, 73, width - 74, width - 73) or y in (72, 73, height - 74, height - 73):
                color = ink
            if 270 <= x <= 930 and 205 <= y <= 425 and (x <= 276 or x >= 924 or y <= 211 or y >= 419):
                color = ink
            if 326 <= x <= 612 and 252 <= y <= 302:
                color = ink
            if 590 <= x <= 874 and 332 <= y <= 382:
                color = ink
            row.extend(color)
        rows.append(bytes(row))
    raw = b''.join(rows)
    return (
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
        + png_chunk(b'IDAT', zlib.compress(raw, 9))
        + png_chunk(b'IEND', b'')
    )


def input_digest(paths):
    payload = bytearray()
    for path in sorted(paths):
        payload.extend(path.relative_to(ROOT).as_posix().encode())
        payload.extend(b'\0')
        payload.extend(path.read_bytes())
        payload.extend(b'\0')
    return digest(bytes(payload))[:12]


def source_inputs():
    named = [
        'README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md',
        '.gitignore', '.gitattributes', 'layout.html', 'app.html',
        'offline-extras.html', 'content-page.html', 'legal-page.html', 'app.js',
        'theme-boot.js', 'theme.js', 'engine.js', 'styles.css',
        'llms.txt', 'build.py', 'serve.py',
    ]
    files = [ROOT / name for name in named]
    files += [p for p in (ROOT / 'pages').glob('*.html')]
    files += [p for p in (ROOT / 'legal').glob('*.html')]
    files += [p for p in (ROOT / 'scripts').iterdir() if p.is_file() and p.suffix in ['.mjs', '.py']]
    files += [p for p in (ROOT / 'docs').rglob('*.md')]
    files += [p for p in (ROOT / '.github').rglob('*.yml')]
    files += [p for p in (ROOT / 'research').iterdir() if p.is_file() and (p.suffix in ['.py', '.mjs', '.swift', '.md', '.json', '.txt'] or p.name == '.gitignore')]
    for directory in ['dpir', 'darkir', 'concertormer']:
        files += [p for p in (ROOT / 'research' / directory).rglob('*') if p.is_file() and (p.suffix in ['.py', '.yml'] or p.name == 'LICENSE')]
    files += [p for p in (ROOT / 'assets').rglob('*') if p.is_file()]
    files += [p for p in (ROOT / 'evidence/ai').rglob('*') if p.is_file() and (p.suffix in ['.json', '.png', '.md', '.log'] or p.name == 'SHA256SUMS')]
    archive = ROOT / 'evidence/ai/bluemask-model-evidence.zip'
    if archive.exists():
        files.append(archive)
    return sorted(set(files))


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    (OUT / 'og').mkdir(parents=True)

    inputs = source_inputs()
    build_id = input_digest(inputs)
    layout = (ROOT / 'layout.html').read_text()
    content_template = (ROOT / 'content-page.html').read_text()
    legal_template = (ROOT / 'legal-page.html').read_text()
    app_source = (ROOT / 'app.html').read_text()
    app_content, app_extras = app_source.split('<!-- APP_EXTRAS -->', 1)
    offline_extras = (ROOT / 'offline-extras.html').read_text()
    css_source = (ROOT / 'styles.css').read_text()
    engine = (ROOT / 'engine.js').read_text()
    app = (ROOT / 'app.js').read_text()
    theme_boot = (ROOT / 'theme-boot.js').read_text()
    theme = (ROOT / 'theme.js').read_text()
    wordmark = (ROOT / 'assets/bluethroat-wordmark.svg').read_text()
    bluemask_full = re.sub(r'\sstyle="[^"]*"', '', (ROOT / 'assets/bluemask-full.svg').read_text())
    bluemask_small = re.sub(r'\sstyle="[^"]*"', '', (ROOT / 'assets/bluemask-small.svg').read_text())
    licenses = '\n\n'.join(p.read_text() for p in sorted((ROOT / 'assets/fonts').glob('*OFL.txt'))).replace('--', '—')

    # Every reusable hosted asset gets a content-addressed filename.
    css_asset_paths = sorted(set(re.findall(r"url\(['\"]?(assets/[^)'\"]+)", css_source)))
    hosted_css = css_source
    for relative in css_asset_paths:
        hosted_css = hosted_css.replace(relative, write_fingerprinted(relative, (ROOT / relative).read_bytes()))
    css_url = write_fingerprinted('styles.css', hosted_css.encode())
    engine_url = write_fingerprinted('engine.js', engine.encode())
    app_url = write_fingerprinted('app.js', app.encode())
    theme_boot_url = write_fingerprinted('theme-boot.js', theme_boot.encode())
    theme_url = write_fingerprinted('theme.js', theme.encode())
    wordmark_url = write_fingerprinted('bluethroat-wordmark.svg', wordmark.encode())
    bluemask_full_url = write_fingerprinted('bluemask-full.svg', bluemask_full.encode())
    bluemask_small_url = write_fingerprinted('bluemask-small.svg', bluemask_small.encode())

    favicon_urls = {}
    for source in sorted((ROOT / 'assets/favicon').iterdir()):
        if source.is_file() and source.name != 'site.webmanifest':
            favicon_urls[source.name] = write_fingerprinted(source.name, source.read_bytes())
    webmanifest = json.loads((ROOT / 'assets/favicon/site.webmanifest').read_text())
    for icon in webmanifest['icons']:
        icon['src'] = favicon_urls[Path(icon['src']).name]
    manifest_url = write_fingerprinted('site.webmanifest', (json.dumps(webmanifest, separators=(',', ':')) + '\n').encode())
    (OUT / 'og/bluemask.png').write_bytes(social_image())

    hosted_head_icons = (
        f'<link rel="icon" type="image/png" href="{favicon_urls["favicon-96x96.png"]}" sizes="96x96">\n'
        f'<link rel="icon" type="image/svg+xml" href="{favicon_urls["favicon.svg"]}">\n'
        f'<link rel="shortcut icon" href="{favicon_urls["favicon.ico"]}">\n'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{favicon_urls["apple-touch-icon.png"]}">\n'
        '<meta name="apple-mobile-web-app-title" content="BlueMask">\n'
        f'<link rel="manifest" href="{manifest_url}">'
    )
    hosted_head_assets = f'<script src="{theme_boot_url}"></script>\n<link rel="stylesheet" href="{css_url}">'
    hosted_wordmark = f'<img src="{wordmark_url}" width="198" height="32" alt="">'
    hosted_marks = {
        'BLUEMASK_FULL': f'<img src="{bluemask_full_url}" width="88" height="88" alt="">',
        'BLUEMASK_SMALL': f'<img src="{bluemask_small_url}" width="56" height="56" alt="">',
    }
    hosted_csp_base = [
        "default-src 'none'", "script-src 'self'", "style-src 'self'",
        "style-src-attr 'none'", "img-src 'self' data: blob:", "font-src 'self'",
        "manifest-src 'self'", "connect-src 'none'", "object-src 'none'",
        "frame-src 'none'", "base-uri 'none'", "form-action 'none'",
    ]
    hosted_nav = {
        'HOME_HREF': '/', 'ABOUT_HREF': '/about', 'TESTS_HREF': '/tests',
        'OFFLINE_HREF': '/offline', 'GUIDE_HREF': '/guides/redact-sensitive-information-from-screenshots',
        'PRIVACY_HREF': '/privacy', 'TERMS_HREF': '/terms', 'SUPPORT_HREF': '/support',
        'DOWNLOAD_HREF': '/BlueMask.html', 'ABOUT_ATTRIBUTES': '', 'TESTS_ATTRIBUTES': '',
    }

    def hosted_page(*, title, description, canonical, content, scripts='', extras='', og_type='website', structured='', product_heading=False):
        csp = hosted_csp_base.copy()
        if structured:
            csp[1] += ' ' + csp_hash(structured)
        return render(layout, {
            **hosted_nav,
            **hosted_marks,
            'CSP': '; '.join(csp), 'PAGE_DESCRIPTION': description,
            'CANONICAL_URL': canonical, 'OG_TYPE': og_type, 'PAGE_TITLE': title,
            'HEAD_ICONS': hosted_head_icons, 'HEAD_ASSETS': hosted_head_assets,
            'STRUCTURED_DATA': structured, 'ROBOTS_META': '', 'BODY_CLASS': '',
            'PRODUCT_NAME': '<h1 id="product-title" class="productbar-name">BlueMask</h1>' if product_heading else '<p class="productbar-name">BlueMask</p>',
            'WORDMARK': hosted_wordmark, 'PAGE_CONTENT': content.strip(),
            'PAGE_EXTRAS': extras.strip(),
            'PAGE_SCRIPTS': f'<script src="{theme_url}"></script>' + scripts,
        })

    app_values = {
        **hosted_marks, 'FONT_LICENSES': licenses, 'BUILD_ID': build_id,
    }
    home_content = render(app_content, app_values)
    home_extras = render(app_extras, app_values)
    app_json = json.dumps({
        '@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'BlueMask',
        'url': ORIGIN + '/',
        'description': 'A local browser tool for redacting private details in photos and screenshots using solid pixel replacement.',
        'applicationCategory': 'SecurityApplication', 'operatingSystem': 'Any',
        'isAccessibleForFree': True,
        'browserRequirements': 'Requires a modern browser with Canvas and local file support.',
        'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
        'creator': {'@type': 'Organization', 'name': 'Bluethroat Labs', 'url': 'https://bluethroatlabs.com/'},
        'featureList': ['Local image processing', 'Solid pixel masking', 'Cosmetic blur with safety warnings', 'Flattened PNG export', 'Original metadata not copied', 'Downloadable offline edition'],
    }, separators=(',', ':'))
    app_structured = f'<script type="application/ld+json">{app_json}</script>'
    home = hosted_page(
        title='BlueMask: Redact Private Details in Photos and Screenshots',
        description='Redact sensitive details locally in your browser. BlueMask replaces covered pixels with a solid mask, avoids copying original metadata, and exports a flattened PNG.',
        canonical=ORIGIN + '/', content=home_content, extras=home_extras,
        scripts=f'\n<script src="{engine_url}"></script>\n<script src="{app_url}"></script>',
        structured=app_structured, product_heading=True,
    )
    (OUT / 'index.html').write_text(home)

    # The downloadable edition has no subresource URLs and keeps the explanatory dialogs.
    offline_css = css_source
    for relative in css_asset_paths:
        offline_css = offline_css.replace(relative, data_uri(relative))
    offline_about = render((ROOT / 'pages/about.html').read_text(), {'BUILD_ID': build_id})
    offline_tests = render((ROOT / 'pages/tests.html').read_text(), {'BUILD_ID': build_id})
    offline_dialogs = render(offline_extras, {'ABOUT_BODY': offline_about, 'TESTS_BODY': offline_tests})
    offline_content = render(app_content, {
        'BLUEMASK_FULL': bluemask_full, 'BLUEMASK_SMALL': bluemask_small,
        'FONT_LICENSES': licenses, 'BUILD_ID': build_id,
    })
    offline_app_extras = render(app_extras, {
        'BLUEMASK_FULL': bluemask_full, 'BLUEMASK_SMALL': bluemask_small,
        'FONT_LICENSES': licenses, 'BUILD_ID': build_id,
    }) + offline_dialogs
    offline_csp = '; '.join([
        "default-src 'none'",
        'script-src ' + ' '.join(map(csp_hash, [theme_boot, theme, engine, app])),
        'style-src ' + csp_hash(offline_css), "style-src-attr 'none'",
        "img-src data: blob:", "font-src data:", "connect-src 'none'",
        "object-src 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'none'",
    ])
    offline_nav = {
        'HOME_HREF': '#workspace', 'ABOUT_HREF': '#about', 'TESTS_HREF': '#tests',
        'OFFLINE_HREF': '#workspace', 'GUIDE_HREF': '#workspace', 'PRIVACY_HREF': 'privacy',
        'TERMS_HREF': 'terms', 'SUPPORT_HREF': 'support', 'DOWNLOAD_HREF': 'BlueMask.html',
        'ABOUT_ATTRIBUTES': ' aria-haspopup="dialog"', 'TESTS_ATTRIBUTES': ' aria-haspopup="dialog"',
    }
    offline = render(layout, {
        **offline_nav,
        'BLUEMASK_FULL': bluemask_full, 'BLUEMASK_SMALL': bluemask_small,
        'CSP': offline_csp, 'PAGE_DESCRIPTION': 'Downloadable self-contained BlueMask image-redaction editor.',
        'CANONICAL_URL': ORIGIN + '/', 'OG_TYPE': 'website',
        'PAGE_TITLE': 'BlueMask offline edition', 'ROBOTS_META': '<meta name="robots" content="noindex,nofollow">',
        'HEAD_ICONS': f'<link rel="icon" href="{data_uri("assets/favicon/favicon.svg")}">',
        'HEAD_ASSETS': f'<script>{theme_boot}</script>\n<style>{offline_css}</style>',
        'STRUCTURED_DATA': '', 'BODY_CLASS': 'offline-edition', 'WORDMARK': wordmark,
        'PRODUCT_NAME': '<h1 id="product-title" class="productbar-name">BlueMask</h1>',
        'PAGE_CONTENT': offline_content.strip(), 'PAGE_EXTRAS': offline_app_extras.strip(),
        'PAGE_SCRIPTS': f'<script>{theme}</script>\n<script>{engine}</script>\n<script>{app}</script>',
    })
    (OUT / 'BlueMask.html').write_text(offline)

    archive = ROOT / 'evidence/ai/bluemask-model-evidence.zip'
    if archive.exists():
        shutil.copyfile(archive, OUT / archive.name)

    with zipfile.ZipFile(OUT / 'bluemask-source.zip', 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in inputs:
            entry = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 9, 28, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            bundle.writestr(entry, path.read_bytes())

    current_hashes = {
        'HOSTED_SHA256': digest((OUT / 'index.html').read_bytes()),
        'OFFLINE_SHA256': digest((OUT / 'BlueMask.html').read_bytes()),
        'ENGINE_SHA256': digest(engine.encode()),
        'SOURCE_SHA256': digest((OUT / 'bluemask-source.zip').read_bytes()),
        'EVIDENCE_SHA256': digest(archive.read_bytes()) if archive.exists() else 'Not published in this build',
    }
    page_specs = [
        ('about', 'About BlueMask | Local Image Redaction and Privacy', 'Learn how BlueMask masks private details locally, why ordinary blur may leave recoverable information, what the offline edition proves, and where its limits remain.', '/about', 'about.html', 'about-page', 'website', ''),
        ('tests', 'BlueMask Recovery Tests | Evidence and Limitations', "Review BlueMask's synthetic image-recovery tests, model provenance, exact results, failed controls, downloadable evidence, and stated limitations.", '/tests', 'tests.html', 'tests-page', 'website', 'dataset'),
        ('offline', 'Use BlueMask Offline | Private Image Redaction', 'Download BlueMask as a self-contained HTML file and use it while disconnected for sensitive image-redaction work.', '/offline', 'offline.html', 'offline-page', 'website', ''),
        ('guides/redact-sensitive-information-from-screenshots', 'How to Redact Sensitive Information from a Screenshot', 'Learn how to redact names, addresses, account details, private messages, and other sensitive information from screenshots without relying on cosmetic blur.', '/guides/redact-sensitive-information-from-screenshots', 'guide.html', 'guide-page', 'article', ''),
    ]
    for output_name, title, description, canonical_path, source_name, article_class, og_type, structured_kind in page_specs:
        body = render((ROOT / 'pages' / source_name).read_text(), {'BUILD_ID': build_id, **current_hashes})
        content = render(content_template, {'ARTICLE_CLASS': article_class, 'PAGE_BODY': body})
        structured = ''
        if structured_kind == 'dataset':
            dataset = json.dumps({
                '@context': 'https://schema.org', '@type': 'Dataset',
                'name': 'BlueMask synthetic image-recovery experiment',
                'description': 'Twelve synthetic eight-digit codes comparing generated Gaussian blur with fixed opaque secure masking under recorded DPIR/DRUNet and DarkIR runs.',
                'datePublished': '2026-09-06', 'dateModified': '2026-09-28',
                'creator': {'@type': 'Organization', 'name': 'Bluethroat Labs', 'url': 'https://bluethroatlabs.com/'},
                'measurementTechnique': 'Exact-code OCR before and after recorded image-restoration runs; controls, settings, outputs, provenance, and limitations are included.',
                'distribution': {'@type': 'DataDownload', 'encodingFormat': 'application/zip', 'contentUrl': ORIGIN + '/bluemask-model-evidence.zip'},
                'isBasedOn': ['DPIR / DRUNet grayscale (2021)', 'DarkIR (2025)'],
                'url': ORIGIN + '/tests', 'sameAs': 'https://github.com/BluethroatLabs/bluemask',
            }, separators=(',', ':'))
            structured = f'<script type="application/ld+json">{dataset}</script>'
        page = hosted_page(title=title, description=description, canonical=ORIGIN + canonical_path, content=content, og_type=og_type, structured=structured)
        target = OUT / output_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page)

    legal_pages = {
        'privacy': ('Privacy | BlueMask', 'How BlueMask handles images, exports, network access, and privacy limits.', ROOT / 'legal/privacy.html'),
        'terms': ('Terms | BlueMask', 'Terms of use and important limitations for BlueMask.', ROOT / 'legal/terms.html'),
        'support': ('Support | BlueMask', 'How to report BlueMask issues and security or privacy concerns.', ROOT / 'legal/support.html'),
    }
    for slug, (title, description, source) in legal_pages.items():
        content = render(legal_template, {'LEGAL_TITLE': title.split(' | ')[0], 'LEGAL_BODY': source.read_text()})
        (OUT / slug).write_text(hosted_page(title=title, description=description, canonical=f'{ORIGIN}/{slug}', content=content))

    legacy_redirects = {'privacy.html': '/privacy', 'terms.html': '/terms', 'support.html': '/support'}
    for filename, target in legacy_redirects.items():
        (OUT / filename).write_text(
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="robots" content="noindex">\n'
            f'<meta http-equiv="refresh" content="0; url={target}">\n'
            f'<link rel="canonical" href="{ORIGIN}{target}">\n'
            '<title>Moved</title>\n</head>\n<body>\n'
            f'<p><a href="{target}">Continue</a></p>\n</body>\n</html>\n'
        )
    (OUT / '_redirects').write_text(''.join(f'/{filename} {target} 301\n' for filename, target in legacy_redirects.items()))

    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n')
    (OUT / 'llms.txt').write_text((ROOT / 'llms.txt').read_text())
    routes = [
        ('/', '2026-09-28'), ('/about', '2026-09-28'), ('/tests', '2026-09-28'),
        ('/offline', '2026-09-28'), ('/guides/redact-sensitive-information-from-screenshots', '2026-09-28'),
        ('/privacy', '2026-09-25'), ('/terms', '2026-09-25'), ('/support', '2026-09-25'),
    ]
    sitemap_urls = ''.join(f'<url><loc>{ORIGIN}{path}</loc><lastmod>{modified}</lastmod></url>' for path, modified in routes)
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + sitemap_urls + '</urlset>\n')

    (OUT / '_headers').write_text("""/*
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: frame-ancestors 'none'
  Cache-Control: public, max-age=0, must-revalidate
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/og/*
  Cache-Control: public, max-age=31536000, immutable
/BlueMask.html
  Cache-Control: public, max-age=0, must-revalidate
  Content-Disposition: attachment; filename="BlueMask.html"
  X-Robots-Tag: noindex
""")

    manifest_files = [p for p in OUT.rglob('*') if p.is_file() and p.name not in ['manifest.json', 'SHA256SUMS']]
    artifacts = {p.relative_to(OUT).as_posix(): digest(p.read_bytes()) for p in sorted(manifest_files)}
    release_manifest = {'build_id': build_id, 'engine_sha256': current_hashes['ENGINE_SHA256'], 'artifacts': artifacts}
    (OUT / 'manifest.json').write_text(json.dumps(release_manifest, indent=2, sort_keys=True) + '\n')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in sorted(artifacts.items())))
    print(json.dumps({
        'build_id': build_id,
        'hosted_page_bytes': len(home.encode()),
        'offline_page_bytes': len(offline.encode()),
        'hosted_sha256': current_hashes['HOSTED_SHA256'],
        'offline_sha256': current_hashes['OFFLINE_SHA256'],
    }, indent=2))


if __name__ == '__main__':
    build()
