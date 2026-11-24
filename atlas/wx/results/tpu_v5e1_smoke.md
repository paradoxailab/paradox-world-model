# Atlas-WX on a Colab TPU v5e-1 (native TorchTPU), 24-25 Nov 2026

Synthetic data (`make_synth_wx.py`, 300 stations; 97.6M: the first 40), `tpu_smoke.sh` / `tpu_debug.sh`, Colab Pro.
torch 2.14.1, torch_tpu 0.2.0, libtpu 0.0.50. Usage rate shown by Colab: about 3.26 compute units per hour.

| Model | Parameters | Batch 256 in | s/step (after compile) | Note |
|---|---|---|---|---|
| 10M | 9,942,032 | 1 part | 0.108-0.110 | two runs, identical losses (0.0451 / 0.0304 at steps 30 / 60) |
| 97.6M (grown 2,6,6 from the 10M) | 97,621,300 | 4 parts | 0.435 | step-0 validation 0.0480 vs the 10M's 0.0478 (G0 on the TPU) |

What had to change (all in `run_atlas_wx.py`):
1. Device `tpu` (PyTorch/XLA does not exist for PyTorch 2.14; torch_xla stops at 2.9).
2. bf16 autocast off: torch_tpu 0.2.0 fails on layer_norm under autocast ("failed to inline functions in MLIR module").
3. Wait for each part, optimiser step and validation batch: execution is asynchronous, and without a wait Python queued
   steps ahead until the 16 GB of TPU memory were full, whatever the batch split.
4. TORCH_TPU_DEFER_AND_FUSE (experimental) off: with it, memory filled during validation.
