# Contributing to BlueMask

Start with the [development guide](docs/DEVELOPMENT.md) and
[architecture](docs/ARCHITECTURE.md). Use a branch and a pull request for changes.

Keep the editor small and readable. Use the existing Bluethroat assets, Instrument
Serif headings, Geist Mono controls, and shared type sizes. About and Tests belong
in their scroll dialogs; the main editor should remain focused on masking.

Changes must preserve these behaviors:

- Secure masking is the default for a new image. Cosmetic blur requires explicit
  consent and remains labelled **Appearance only**.
- Secure regions are removed before cosmetic processing and painted again last.
- All processing stays in the browser. Do not introduce telemetry, remote fonts,
  third-party scripts, storage of private images, or an upload endpoint.
- Both the hosted page and the standalone offline HTML must work.
- A download contains a flattened PNG with a generic filename and no copied
  metadata. Original-preview, unfinished gestures, and in-flight exports retain
  their guards.
- Keep keyboard controls, focus management, touch editing, and readable mobile
  layouts working.

Use synthetic images and invented details for fixtures and screenshots. Never
attach a private document or a user's image to an issue, pull request, or test run.

Before opening a pull request, run the build check and the browser suites described
in the development guide. Explain the user-visible change, relevant validation,
and any remaining limitations. Include desktop/mobile screenshots for UI changes.
Changes to the rendering engine require renewed fixture provenance and evaluation
before claiming that historical model results apply to the new renderer.

For potential privacy or security failures, use [SECURITY.md](SECURITY.md).
