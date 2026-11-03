# PWM provenance — what is Paradox's, and what is not

| Component | Role | Origin | Inside PWM's weights? |
|---|---|---|---|
| **PWM-Dyn** (`pwm/`, `train.py`) | Physical dynamics model: learns how states evolve and propagate on real road and geographic graphs, with uncertainty | **Paradox-trained from random initialisation** on real observations | — it *is* the weights |
| Caltrans PeMS (PEMS08, PEMS04) | Training and test data | Public research dataset | Data only |
| IMD gridded rainfall | Training and test data | India Meteorological Department, via `imdlib` | Data only |
| Google TimesFM 2.5 / 3.0 (`opponents/`) | **Opponent** — run zero-shot on the same test windows for comparison | Google, external. 2.5 = Apache-2.0; 3.0 = non-commercial research only | **No.** Separate environment; never loaded, distilled or trained into PWM |
| gpt-oss-120b / 20b (`reason/`) | **Language interface** — explains PWM's numbers in words | OpenAI open-weight model, external, served via Groq or locally | **No.** Receives PWM's numbers as text; its output is labelled as gpt-oss's |

## Rules the code enforces

1. PWM-Dyn starts from random weights. No pretrained checkpoint is ever loaded into it.
2. PWM's code may not import any external model library. `check_provenance.py` parses the imports and fails if it finds `timesfm`, `transformers`, `huggingface_hub`, `openai`, etc.
3. Every saved PWM checkpoint must contain exactly PWM-Dyn's own parameter names and shapes. A single foreign tensor makes the check fail (tested).
4. Opponents run in a separate Python environment that PWM's environment cannot import from.
5. Every reasoning output has two labelled parts: `pwm_facts` (PWM's numbers) and `explanation` (gpt-oss's text, written only from those facts).
6. Synthetic test data and stub opponents exist only to test the pipeline. `compare.py` refuses to report them.

## Standard techniques PWM uses

PWM-Dyn's architecture is written for Paradox, but like every model in the field it uses published, general-purpose building blocks: graph diffusion over an adjacency matrix, learned time-of-day/day-of-year embeddings, residual MLP blocks, and quantile (pinball) loss. These are methods, not anyone's model; no code or weights from STAEformer, STID, TimesFM or any other model are included.
