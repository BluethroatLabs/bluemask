#!/usr/bin/env python3
"""Serve only the built public artifacts, with production-equivalent headers."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LEGACY_REDIRECTS = {
    '/privacy.html': '/privacy',
    '/terms.html': '/terms',
    '/support.html': '/support',
}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / 'dist'), **kwargs)

    def send_legacy_redirect(self):
        target = LEGACY_REDIRECTS.get(self.path.split('?', 1)[0])
        if not target:
            return False
        self.send_response(301)
        self.send_header('Location', target)
        self.end_headers()
        return True

    def do_GET(self):
        if self.send_legacy_redirect():
            return
        super().do_GET()

    def do_HEAD(self):
        if self.send_legacy_redirect():
            return
        super().do_HEAD()

    def guess_type(self, path):
        target = Path(path)
        if target.name in ['llms.txt', 'robots.txt', 'SHA256SUMS']:
            return 'text/plain; charset=utf-8'
        if target.name == 'sitemap.xml':
            return 'application/xml; charset=utf-8'
        if not target.suffix and target.name not in ['_headers']:
            return 'text/html; charset=utf-8'
        return super().guess_type(path)

    def end_headers(self):
        request_path = self.path.split('?', 1)[0]
        if request_path.startswith('/assets/') or request_path.startswith('/og/'):
            self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
        else:
            self.send_header('Cache-Control', 'public, max-age=0, must-revalidate')
        if request_path == '/BlueMask.html':
            self.send_header('Content-Disposition', 'attachment; filename="BlueMask.html"')
            self.send_header('X-Robots-Tag', 'noindex')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "frame-ancestors 'none'")
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        super().end_headers()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8791)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'BlueMask: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
