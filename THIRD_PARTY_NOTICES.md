# Third-party code, fonts, and artwork

A project-wide license for BlueMask has not yet been selected. The entries below
record the notices already supplied with bundled third-party material; they do
not grant a license to Bluethroat's trademarks or other first-party assets.

| Material | Location | License / provenance |
| --- | --- | --- |
| Instrument Serif | `assets/fonts/` | [SIL OFL 1.1](assets/fonts/Instrument-Serif-OFL.txt) |
| Geist Mono | `assets/fonts/` | [SIL OFL 1.1](assets/fonts/Geist-Mono-OFL.txt) |
| DPIR architecture, helpers, reference driver | `research/dpir/` | [MIT](research/dpir/LICENSE); commit in [source record](research/dpir-source.json) |
| DarkIR architecture and configuration | `research/darkir/` | [MIT](research/darkir/LICENSE); commit in [source record](research/darkir-source.json) |
| Concertormer candidate source and configurations | `research/concertormer/` | Preserve the complete [upstream license file](research/concertormer/LICENSE), including its MIT and BasicSR Apache notices; candidate was not run |
| Bluethroat bird, wordmark, engraving | `assets/` | First-party brand assets; [source record](docs/brand-sources.md) and [wordmark record](assets/bluethroat-wordmark-provenance.md) |
| Monochrome parchment | `assets/privacy-scroll.png` | [Generation provenance](assets/privacy-scroll-provenance.md) |

The browser application does not run the research models. Model weights and
Python dependencies are downloaded separately for research and are not committed
or included in the web page. DarkIR's checkpoint license is recorded separately
from its code license in `research/darkir-source.json`. Check the upstream model
terms before redistributing weights.

Both complete font notices are embedded in the single-file HTML. Retain the
upstream notices when redistributing the research source or its evidence bundle.
