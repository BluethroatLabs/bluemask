# BlueMask brand assets and source record

Retrieved 2026-09-06 from Bluethroat Labs and the official Google Fonts repository.

These assets are bundled locally so the editor does not fetch fonts or artwork at runtime.
The emblem and engraving are first-party brand assets reused for BlueMask at Rahul Saxena's direction.
They are not offered as a separate public-domain asset collection. Font licensing is separate.

## Brand reference

Live site: https://bluethroatlabs.com/

CSS: https://bluethroatlabs.com/_next/static/chunks/707b28cbb84e491c.css

- Instrument Serif: regular 400 for display headlines.
- Geist Mono: variable 100–900 for body text and controls.
- Dark: background `#0a0a0a`, foreground `#fafafa`, borders `#2e2e2e`.
- Light: background `#fafafa`, foreground `#0a0a0a`, borders `#a9a9a9`.
- Hero panel `#191919`; zero-radius corners; fine ruled grid.
- Desktop navigation 72px high, mobile 48px; content container 1280px at a 1440px viewport.
- Monochrome engraving and vertical scanlines; serif editorial headlines with mono text.

The website HTML and CSS did not expose a literal rolled-parchment component.
BlueMask's Privacy Scroll is a new article treatment within this visual family.

## Files

| File | Bytes | SHA-256 | Source |
| --- | ---: | --- | --- |
| `assets/footer-bg-dark.webp` | 78,996 | `098f0bd790b955d234ad1603a94fb1a5eff22a0bc5112df965185ce0bd17a329` | https://bluethroatlabs.com/_next/image?url=%2Flanding%2Ffooter-bg-dark.png&w=1200&q=75 |
| `assets/fonts/instrument-serif-latin.woff2` | 15,040 | `60c06664b5a95c7de6cc3e00d1f9034d78bd1e40b564016b241674449a067d4d` | https://bluethroatlabs.com/_next/static/media/e41d5df559864f9e-s.p.380d09ea.woff2 |
| `assets/fonts/geist-mono-latin.woff2` | 23,108 | `5f3d6ad60f29d6cb708414ec6887163d63bf197377ef5417d2483ff31ace6c3b` | https://bluethroatlabs.com/_next/static/media/797e433ab948586e-s.p.29207c2f.woff2 |
| `assets/fonts/Instrument-Serif-OFL.txt` | 4,405 | `129ed7618959716959f2941fdd5b49e0ad6e6c1d78726761786a00253d865521` | https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/OFL.txt |
| `assets/fonts/Geist-Mono-OFL.txt` | 4,387 | `1781d2806a07d91c4edf4740b88449fab7d0eadad53f7c351b94cd4d4eb8c00f` | https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/OFL.txt |
| `assets/bluethroat-emblem.svg` | 1,815 | `e507336b08d2c0d5c8319e26fabb47c34382319181122e8c6bedbc480a84f435` | https://bluethroatlabs.com/ (second SVG inside navigation) |

## Asset handling

`footer-bg-dark.webp` is the live site's own optimized 1200px rendition of
`/landing/footer-bg-dark.png`, requested with `Accept: image/webp`. It is not
locally redrawn or recompressed. The original PNG is 1,281,212 bytes; the bundled
rendition is 78,996 bytes. Treat this strip as decoration, with an empty alt string
when rendered as an image. Do not place dense article text directly over it.

`bluethroat-emblem.svg` contains the live navigation's 32×32 bird path. Only the
framework class was removed, and explicit SVG namespace / `fill="currentColor"`
were added. Use inline or as a CSS mask to inherit text color; an external `img`
does not inherit its parent's `currentColor`.

Both WOFF2 files are the site's unmodified Latin subsets, matching its deployed
CSS. Instrument Serif is normal style, weight 400. Geist Mono is normal style,
variable weight 100–900. Provide system fallbacks for characters outside the subset.

Rechecked the live CSS and browser-rendered fonts on 2026-09-07. The homepage uses
InstrumentSerif-Regular for display headings and GeistMono-Medium/SemiBold for
body and section labels. Bai Jamjuree is also declared in the shared stylesheet
but was not used by the inspected homepage text. BlueMask uses the two active
families, including in its sample document, and now matches the live site's
Instrument Serif / Geist Mono fallback metrics. Scroll emphasis uses weight 600.

## Font notices

- Instrument Serif: Copyright 2022 The Instrument Serif Project Authors
  (https://github.com/Instrument/instrument-serif).
- Geist Mono: Copyright 2024 The Geist Project Authors
  (https://github.com/vercel/geist-font.git).
- Each font is licensed under SIL Open Font License 1.1. Preserve the corresponding
  `assets/fonts/*-OFL.txt` file in distributed bundles. For a single-file HTML edition,
  embed both full notices in an accessible license document or the HTML itself;
  base64-embedding font data alone does not carry these downloaded notice files.
- The downloaded files and hashes are recorded above. The source branches and the
  deployed asset hashes are independent provenance, not an assertion about a
  common repository commit.

## Privacy Scroll sources

The fragment describes the locally tested implementation. The release remains a
candidate; the scope and limits of model evidence are stated with the results.
Rahul’s 2026-09-07 design correction replaces rhetorical copy with direct wording
and the editorial dialog with a literal monochrome parchment scroll.

- Gaussian filter definition: https://drafts.csswg.org/filter-effects/#feGaussianBlurElement
- Restormer, CVPR 2022: https://arxiv.org/abs/2111.09881
- NAFNet / Simple Baselines for Image Restoration, ECCV 2022: https://arxiv.org/abs/2204.04676
- Perceptual plausibility versus reconstruction error: https://arxiv.org/abs/1711.06077
- Browser connectivity indicators: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine
- Bitmap serialization: https://html.spec.whatwg.org/multipage/canvas.html#serialising-bitmaps-to-a-file

Model references establish the existence and purpose of restoration methods. They
are not BlueMask benchmark receipts and are not labelled as the most advanced models.
