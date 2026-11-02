"""ParadoxBench-1.1 - Paradox Physical-Dynamics Benchmark. Frozen definitions.

1.1 (2026-11-03) adds four traffic tasks (PEMS03, PEMS07, METR-LA, PEMS-BAY). The four ParadoxBench-1 tasks,
their windows, tracks and metrics are unchanged, so every ParadoxBench-1 result stays valid. The new tasks
use every 6th test window (every 30 minutes) so that zero-shot foundation models can be run on all of them
within a free-GPU budget; every model on a task is scored on that task's same windows.

Everything a submission is scored against is fixed here: tasks, splits, official test windows,
context budgets per track, the hidden-sensor set of the robustness track, and the metrics.
Change nothing in this file without bumping the benchmark version.
"""
import numpy as np

VERSION = "ParadoxBench-1.1"
STRIDE = 2            # official windows = every 2nd test window (ParadoxBench-1 tasks)
STRIDE_BY_LOADER = {"PEMS03": 6, "PEMS07": 6, "METR-LA": 6, "PEMS-BAY": 6}   # 1.1 tasks
HIDDEN_SEED = 2026    # robustness track: sensors withheld at test time
HIDDEN_SHARE = 0.30
LEVEL = 0.80          # prediction-interval level scored (q10..q90)

# task id -> (loader name, description, units, horizon steps, standard context, open context)
TASKS = {
    "PEMS08":  ("PEMS08", "Caltrans District 8 highway flow, 170 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "PEMS04":  ("PEMS04", "Caltrans District 4 highway flow, 307 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "IMD-CI":  ("IMD_central_india", "IMD 0.25 deg daily rainfall, central India (MP)", "mm / day", 7, 30, 365),
    "IMD-WC":  ("IMD_west_coast", "IMD 0.25 deg daily rainfall, Konkan / Western Ghats", "mm / day", 7, 30, 365),
    # ParadoxBench-1.1
    "PEMS03":  ("PEMS03", "Caltrans District 3 highway flow, 358 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "PEMS07":  ("PEMS07", "Caltrans District 7 highway flow, 883 sensors, 5-min", "vehicles / 5 min", 12, 12, 512),
    "METR-LA": ("METR-LA", "Los Angeles loop-detector speed, 207 sensors, 5-min", "mph", 12, 12, 512),
    "PEMS-BAY": ("PEMS-BAY", "Bay Area loop-detector speed, 325 sensors, 5-min", "mph", 12, 12, 512),
}
NEW_IN_1_1 = ("PEMS03", "PEMS07", "METR-LA", "PEMS-BAY")


def stride_for(ds):
    return STRIDE_BY_LOADER.get(ds.name, STRIDE)

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
    return np.arange(a + ds.in_len, b - ds.out_len + 1)[::stride_for(ds)]


def validation_windows(ds):
    a, b = ds.bounds["val"]
    return np.arange(a + ds.in_len, b - ds.out_len + 1)[::stride_for(ds)]


def hidden_sensors(n):
    k = int(round(HIDDEN_SHARE * n))
    return np.sort(np.random.default_rng(HIDDEN_SEED).permutation(n)[:k])
