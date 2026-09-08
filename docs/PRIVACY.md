# Privacy model

BlueMask helps remove selected image details from a downloaded PNG. It does not
make the rest of the photograph anonymous or hide a visit to the hosting site.

## Secure masking and cosmetic blur

Secure masking replaces covered source pixels with a fixed opaque patch. The
renderer removes secure regions before cosmetic processing and repaints them
last. Region position, shape, and unmasked context remain visible.

Cosmetic blur softens pixels and may preserve recoverable information. It is an
appearance effect. The interface recommends secure masking, requires consent to
choose blur, and warns again before exporting images containing cosmetic regions.

Use enough coverage to include every letter, edge, reflection, or repeated copy
of a sensitive detail. A correctly implemented mask cannot protect details that
were never selected. Review the downloaded image at full size before sharing it.

## Data handling

Selected files are decoded and edited in browser memory. The original is retained
while editing to support preview and changes. There is no application feature for
uploading, tracking, storing images, or saving editing sessions. Fonts and artwork
are embedded. PNG export uses a fresh canvas, a generic filename, and does not
copy original metadata. The source file on disk is unchanged.

Clearing a session releases the application's canvases and state. It is not a
claim of forensic erasure from browser memory, swap, backups, or the operating
system. Downloads may be copied or synced by software outside BlueMask.

## Paranoia Mode

The trust question is: how can someone check that the page works without sending
their photo or extracted details to Bluethroat's servers?

1. Obtain the standalone `BlueMask.html` before opening a sensitive image.
2. Disconnect the device using its network controls.
3. Open that file, import the image, mask it, and save the PNG.
4. Review the download and close BlueMask before reconnecting.

While the device has no network connection, this page cannot upload its contents.
A webpage cannot turn off Wi-Fi, cellular, or Ethernet itself. `navigator.onLine`
is only a browser hint, so the UI does not treat it as proof of isolation.

Offline functionality proves no server is required for that workflow. It does
not certify arbitrary downloaded code, browser extensions, the browser, or the
device. A compromised environment can still read files or record the screen.

## Hosting and evidence limits

The hosting provider can see ordinary connection metadata when serving the app.
External links and artifact downloads are user-initiated network actions. CSP is
a restriction imposed by the delivered page, not independent proof that the
publisher delivered honest code. Unsigned hashes detect byte differences when
compared with a trusted record; hashes supplied by the same untrusted publisher
do not independently establish trust.

Recorded model experiments concern twelve synthetic codes, one font, and fixed
geometry. All twelve secure inputs are identical. They do not establish protection
against every model, image, inference from visible context, or face identification.
Read the [research methodology](../research/README.md) alongside the results.
