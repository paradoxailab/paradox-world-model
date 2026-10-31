"""ParadoxBench-1 - Paradox Physical-Dynamics Benchmark, version 1. Frozen definitions.

Everything a submission is scored against is fixed here: tasks, splits, official test windows,
context budgets per track, the hidden-sensor set of the robustness track, and the metrics.
Change nothing in this file without bumping the benchmark version.
"""
import numpy as np

VERSION = "ParadoxBench-1"
STRIDE = 2            # official windows = every 2nd test window (all models, all tracks)
HIDDEN_SEED = 2026    # robustness track: sensors withheld at test time
HIDDEN_SHARE = 0.30
LEVEL = 0.80          # prediction-interval level scored (q10..q90)

# task id -> (loader name, description, units, horizon steps, standard context, open context)
TASKS = {
    "PEMS08":  ("PEMS08", "Caltrans District 8 highway flow, 170 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "PEMS04":  ("PEMS04", "Caltrans District 4 highway flow, 307 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "IMD-CI":  ("IMD_central_india", "IMD 0.25 deg daily rainfall, central India (MP)", "mm / day", 7, 30, 365),
    "IMD-WC":  ("IMD_west_coast", "IMD 0.25 deg daily rainfall, Konkan / Western Ghats", "mm / day", 7, 30, 365),
}

TRACKS = {
    "A": "Standard: look-back limited to the standard context (12 steps / 30 days); any training "
         "on the task's TRAIN split; pretrained models allowed if they respect the context limit.",
    "B": "Open context: look-back up to 512 steps (traffic) / 365 days (rainfall); pretrained "
         "foundation models compete here zero-shot.",
    "R": "Robustness: 30% of locations (fixed by HIDDEN_SEED) have NO observations in the test "
         "period; models must still forecast them. Scored on the hidden locations only.",
    "Z": "Zero-shot transfer: forecast PEMS08 with a model that has never seen any PEMS08 data "
         "(not even its normalisation statistics). Context as Track B.",
}


def official_windows(ds):
    """Indices of the official test windows. ds must be loaded WITHOUT a seasonal lag."""
    a, b = ds.bounds["test"]
    return np.arange(a + ds.in_len, b - ds.out_len + 1)[::STRIDE]


def validation_windows(ds):
    a, b = ds.bounds["val"]
    return np.arange(a + ds.in_len, b - ds.out_len + 1)[::STRIDE]


def hidden_sensors(n):
    k = int(round(HIDDEN_SHARE * n))
    return np.sort(np.random.default_rng(HIDDEN_SEED).permutation(n)[:k])
