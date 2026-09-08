# BlueMask release candidate

Owner: Bluethroat Labs. Product direction recorded 2026-09-06.

BlueMask is the first intended public release in the lab's product line. It makes
selected parts of photos and screenshots safe to share through local processing.

## Accepted decisions

- Secure masking is the default. Cosmetic blur remains available and is labelled
  "Appearance only".
- Choosing cosmetic blur opens an explicit explanation. The primary action is
  "Use secure masking", recommended by Bluethroat Labs for sensitive data.
- Cosmetic blur requires a deliberate secondary confirmation. The choice is not
  remembered across new images or sessions.
- The editor and Privacy Scroll follow bluethroatlabs.com's monochrome, ruled,
  Instrument Serif and Geist Mono visual family.
- Processing needs no accounts, uploads, analytics, models, or runtime third-party
  dependencies. The offline edition contains its scripts, styles, and artwork.

## Privacy boundaries

A webpage cannot turn off the device's internet. Paranoia mode guides the user to
disconnect before choosing a sensitive image, and keeps editing and export working
offline. Browser connectivity indicators are hints, not proof of isolation.

No claim of complete anonymity: page hosting sees ordinary connection metadata;
uncovered context in an image can identify people or subjects. Masking removes the
selected source pixels from the export, not clues left elsewhere in the image.

Offline operation demonstrates that processing does not require a server. Source,
artifact hashes, reproducible builds, and independently recorded runtime tests are
separate evidence about what the implementation does. Hashes alone do not prove
that the code is honest. No signed-release claim until signatures actually exist.

## Evidence requirement

The historical prototype has dictionary-recovery and pixel non-interference tests.
Those are not results against advanced AI deblurring models. Publish only recorded
runs with model/version, known synthetic originals, controls, sample counts,
recovery metrics and downloadable outputs. Inference is not ground-truth recovery.
Never describe an unrun model as defeated or turn a finite test into "AI-proof".

## Production work

1. Accessible branded editor and explicit cosmetic-blur warning.
2. Local processing, flattened PNG export, generic filenames and predictable masks.
3. Self-contained offline artifact, Paranoia workflow and Privacy Scroll.
4. Executable regression evidence for masking, export, offline operation and UI.
5. Honest benchmark publication and desktop/mobile checks before release approval.

## Reference

Rahul supplied https://kycwatermark.com/. The site was inspected in isolated Chrome:
its useful product pattern is a simple local image workflow and a plain-language
about section. BlueMask implements a self-contained downloadable edition and an
explicit user-controlled disconnection workflow.

The secure mask uses a constant opaque fill. Every secure region is removed before
any cosmetic processing; secure masks take precedence when regions overlap. Region
geometry stays fixed across repeated exports. This removes the prototype's random
padding and multi-export composition mechanism without pretending that box geometry
or visible context has become secret.

## Sources of prior decisions

- Codex: 01a05755-35a4-7a51-b02f-209d3c628d1a, August 31 to September 3, 2026.
- Claude Code: 0b4794eb-3d66-4263-9f5e-5a4888485e52, same period.
- Original prototype: ../redactor/.
