# DarkIR (CVPR 2025): blur control failed on these inputs

**This recent model run does not support a strong masking-resistance claim.**
DarkIR-m is designed for low-light photographic restoration. On this experiment's
white-background Gaussian-blurred synthetic text, it made exact OCR recovery worse.

| Input | Exact tokens before DarkIR | Exact tokens after DarkIR |
|---|---:|---:|
| Unredacted control | 12 / 12 | 12 / 12 |
| Gaussian blur, sigma 2 | 12 / 12 | 6 / 12 |
| Gaussian blur, sigma 3 | 9 / 12 | 0 / 12 |
| BlueMask secure mask | 0 / 12 | 0 / 12 |

The secure-mask row cannot be presented as defeating an effective deblurring
attacker when that model did not succeed on the relevant blur controls. We retain
the result so readers can see which models were tried and how they performed.
Publication year alone does not establish suitability or attack strength.

We used the unchanged [official DarkIR architecture](https://github.com/cidautai/DarkIR)
and the authors' [released DarkIR_384 checkpoint](https://huggingface.co/Cidaut/DarkIR),
with the LOLBlur configuration. Source and weights commits, SHA-256, exact model
parameters and execution provenance are beside this file. The checkpoint is
13,397,397 bytes; its hash matches the author's Hugging Face LFS object.

The same twelve synthetic original, Gaussian and actual BlueMask secure PNGs from
the DPIR experiment were used. OCR uses the same exact-match rule. All secure
inputs are identical and were run once with disclosed reuse; the total was 37
unique model inputs. Inference plus local OCR took 8.56 seconds on CPU, under a
macOS process sandbox denying network operations. No image was sent to a hosted
model or API.

This is a recorded out-of-distribution check, not a claim that DarkIR generally
fails at its intended task. The study has not established performance against
the strongest current models, inpainting, private photo scenes or contextual
inference. Detailed transcriptions and output PNGs are available here.

DarkIR is by Daniel Feijoo, Juan C. Benito, Alvaro Garcia and Marcos V. Conde,
published at CVPR 2025. Upstream code is MIT licensed; the official checkpoint
model card lists CC-BY-4.0. The model code and weights were not changed.
