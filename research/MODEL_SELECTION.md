# Released-model evaluation scope

Reviewed 6 September 2026. This records a bounded selection exercise, not a
comprehensive ranking of the latest deblurring models.

| Candidate | Primary release | Match to this test | Decision |
|---|---|---|---|
| DPIR with DRUNet, TPAMI 2021 | [Author repository](https://github.com/cszn/DPIR), [official weight downloader](https://github.com/cszn/DPIR/blob/15bca3fcc1f3cc51a1f99ccf027691e278c19354/main_download_pretrained_models.py) | Its learned denoiser can be used with an explicitly supplied Gaussian blur kernel. Architecture runs in local PyTorch. | Execute a small synthetic benchmark. Established baseline only. |
| NAFNet, ECCV 2022 | [Author repository](https://github.com/megvii-research/NAFNet) | Released GoPro/REDS models target motion blur. That differs from deliberate Gaussian screenshot blur. | Not run in this pass. |
| Restormer, CVPR 2022 | [Author repository](https://github.com/swz30/Restormer) | Released motion/defocus checkpoints are useful candidates for later photo tests. Gaussian denoising is a different task from Gaussian deblurring. | Not run in this pass. |
| EVSSM, CVPR 2025 | [Author repository](https://github.com/kkkls/EVSSM), [release environment](https://github.com/kkkls/EVSSM/blob/master/environment.yml) | Recent single-image motion-deblurring release; the provided environment specifies Linux, CUDA PyTorch, causal-conv1d and mamba-ssm. This machine is macOS arm64 with no CUDA. | Not run; validate a compatible implementation or use separate approved compute before comparing. |
| EMP, CVPR 2026 | [Author repository](https://github.com/Chohoonhee/EMP) | Uses paired image and event-camera measurements at inference. An ordinary screenshot does not provide those event measurements. | Excluded from this screenshot test on input comparability grounds. No defeat claim. |
| Concertormer, ICCV 2025 | [Author repository](https://github.com/setsunil/Concertormer), [official weight archive](https://drive.google.com/file/d/1NvbGroZm4vVgvWJtmgW-6Fwd97PiukiL/view) | Pure-PyTorch single-image motion-deblurring architecture is promising. Google Drive reports the bundled checkpoint archive as 1.2G, exceeding this pass's remaining download allowance. | Source/configuration inspected at commit `94269c556277805051644343e3a2cc76c4cd7aaf`; weights and inference not run. |
| DarkIR-m, CVPR 2025 | [Author repository](https://github.com/cidautai/DarkIR), [official checkpoint](https://huggingface.co/Cidaut/DarkIR) | A compact recent model for low-light photographic restoration. White-background Gaussian screenshots are outside its advertised domain. | Executed on all the same fixtures. Blur-control exact OCR became worse, so its secure-mask failure does not substantiate resistance to a strong suitable attacker. |

The DPIR results cannot satisfy the proposed marketing phrase “against the most
advanced deblurring AI.” That remains an open publication requirement. A dated,
released baseline with controls is useful evidence and must be named as such.

## What constitutes recovery

The original token is known because this test generated it. The score checks
whether local OCR reports that full eight-digit token exactly, before and after
restoration. It does not count sharpened edges, plausible-looking marks, inferred
words or lower pixel error as recovery. All OCR transcriptions and restored
images are retained so a human can inspect failures.

PSNR is a secondary pixel-similarity metric for the selected region. It is not a
privacy score. OCR can miss text that a person or another model could read.
Different modalities, layouts, priors and visible context remain outside this
small experiment.

## A stronger property with a narrower claim

For the fixed geometry in this test, every synthetic original differs only
inside the marked region. If the product renders all of them to the same image,
the published pixels do not distinguish which tested token was under that
region. The deblurring model then necessarily receives the same image. This
checks pixel dependence for the particular rendered fixtures; it does not
prove that a user selected every sensitive pixel or concealed contextual clues.
