# arXiv submission metadata

**Title:** PWM-Dyn and ParadoxBench: A Provenance-Audited Physical Dynamics Model, Benchmarked Against Zero-Shot Foundation Models on US Traffic and Indian Rainfall

**Authors:** Aditya Kumar, Anupam Singh (ParadoxAI Lab, India)

**Primary category:** cs.LG (Machine Learning). **Cross-lists:** stat.ML; physics.ao-ph

**Comments:** 16 pages, 1 figure. Code, benchmark and run logs: https://github.com/paradoxailab/paradox-world-model

**Licence:** CC BY 4.0

**Source:** upload `main.tex`, `main.bbl`, `refs.bib`, `fig_architecture.tex` as one flat archive (compiles with pdflatex; `main.bbl` is included because arXiv does not run BibTeX).

**Abstract** (1,882 characters, inside arXiv's 1,920 limit):

We present PWM-Dyn, the first trained component of the Paradox World Model (PWM): a 0.3M-parameter spatiotemporal dynamics model that forecasts how physical conditions evolve and propagate over real networks — highway-sensor graphs and gridded rainfall — with calibrated quantile uncertainty and robustness to dead sensors. It is trained from random initialisation on public observations only (Caltrans PeMS traffic; India Meteorological Department 0.25° daily rainfall), and a provenance audit verifies that no external model code or weights are inside it. We also release ParadoxBench-1, an open benchmark of four tasks (PEMS08, PEMS04, central-India and Konkan rainfall) and four tracks — standard context, open context, 30% dark sensors and zero-shot transfer to an unseen network — scored by one function for point error, pinball loss and interval (Winkler) score. On the open-context track, where Google's TimesFM 2.5 and 3.0 compete zero-shot with up to 512 steps or 365 days of history, PWM-Dyn has lower MAE, pinball loss and interval score than both on all four tasks: MAE 14.15 vs 14.55 (TimesFM 3.0) on PEMS08, 19.02 vs 19.13 on PEMS04, 2.84 vs 2.92 and 3.41 vs 3.62 on the two rainfall regions; TimesFM 3.0 keeps a 2.5% lower RMSE on PEMS04. Split-conformal calibration lifts PWM's 80% rainfall-interval coverage from 55% to 83–85% without changing the median. With 30% of sensors dark, PWM beats per-sensor climatology by 9–14% MAE on traffic. The margins are narrow where it matters: PEMS04 is a near-tie, PWM's edge over median climatology on rainfall is 2–7%, a PEMS04-trained PWM transferred to PEMS08 (MAE 16.36) trails zero-shot TimesFM 3.0, and under the standard 12-step context PWM-Dyn v0.4 does not recover our earlier v0.3 result (PEMS08 MAE 14.18). Every PWM win is a specialist-vs-zero-shot result: PWM trained on each network's history; TimesFM did not.
