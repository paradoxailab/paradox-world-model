# Running Atlas-WX Stage 1 on a rented A100

Colab has no GPU for the lab's account, so Stage 1 (10M, 28.5M, 97.6M and 251.9M) runs on a rented GPU. The machine
fetches the public station data itself and checks it against the pre-registered SHA-256; Google Drive is not needed.

## What to rent (the lab owner does this; it costs money)

- **GPU:** one NVIDIA A100 (80 GB preferred; 40 GB works). Providers: RunPod, Lambda, Vast.ai or similar.
- **Image:** a PyTorch template (PyTorch 2.x, CUDA 12).
- **Disk:** at least **250 GB** of persistent volume (the raw station files need ~150 GB during the fetch).
- **Time and cost (estimate):** about 2 h of data fetch, then roughly 70–90 GPU-hours for the four models (about half
  for 251.9M). At about $1.2–1.9 per A100-hour that is roughly **$90–170**. Stop the machine when the log says
  "Stage 1 complete", or earlier if you decide not to train the largest model.

## Start (paste into the machine's terminal)

```bash
apt-get update -qq && apt-get install -y -qq tmux git >/dev/null
git clone -q -b atlas-v0.1 https://github.com/paradoxailab/paradox-world-model /workspace/atlas-wx/pwm
tmux new -d -s atlas 'bash /workspace/atlas-wx/pwm/atlas/wx/cloud_stage1.sh'
tail -f /workspace/atlas-wx/pipeline.log
```

Closing the terminal does not stop it (tmux). If the machine restarts, run the `tmux new …` line again: the fetch and
every model resume where they stopped.

Optional, to have results copied off the machine after each model: before the `tmux` line, set your own Hugging Face
write token in that terminal (`export HF_TOKEN=…` and `export HF_REPO=PARADOXAIlabs/atlas-wx-runs`). The script reads
it from the environment only and never writes it to a file.

## What to send back

`/workspace/atlas-wx/pipeline.log` and the files `runs/wx_s1_*_s600.json` (small). Model weights are
`runs/wx_s1_*_s600.pt`. The selection rule and predictions W1, W2, W11 are scored from the JSON files.
