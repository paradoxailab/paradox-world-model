"""PWM reasoning layer: gpt-oss explains PWM's numbers. It never produces them.

  # explain PWM's forecast for location 12 at test window 500
  python reason/gptoss_layer.py explain --data PEMS08 --window 500 --node 12

  # what-if: sensors 12 and 13 report a closure (zero flow) in the last hour
  python reason/gptoss_layer.py whatif --data PEMS08 --window 500 --nodes 12 13 --scenario closure

  # what-if: rainfall over the last 30 days 1.5x heavier in three grid cells
  python reason/gptoss_layer.py whatif --data IMD_central_india --window 40 --nodes 3 4 5 --scenario scale --factor 1.5

LLM endpoint (any OpenAI-compatible server running gpt-oss):
  Groq (default):  export GROQ_API_KEY=...            model openai/gpt-oss-120b
  Local gpt-oss-20b (vLLM / Ollama): --base_url http://localhost:8000/v1 --model openai/gpt-oss-20b
  No key: --dry_run prints the exact facts + prompt that would be sent.

Every output separates:
  pwm_facts    numbers computed by PWM-Dyn (Paradox-trained)
  explanation  text written by gpt-oss FROM those facts (external language model)
What-if results are the model's simulated response, not validated against reality.
"""
import argparse, json, os, sys, urllib.request
import numpy as np
import torch

ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOTDIR)
from pwm.data import load, ROOT
from evaluate_pwm import load_member
from train import DEV

SYSTEM = """You are the language interface of Paradox World Model (PWM).
All numbers come from PWM-Dyn, a forecasting model trained by Paradox on real observations.
Rules:
- Use ONLY the numbers in the provided facts. Never invent measurements, causes or events.
- Always state the uncertainty (the 10th-90th percentile range) with any forecast.
- Separate clearly: what was OBSERVED, what PWM PREDICTS, and what is only a POSSIBLE explanation.
- For what-if scenarios, say plainly that this is the model's simulated response, not observed reality,
  and that PWM's what-if behaviour has not been validated against real interventions.
- Mention PWM's measured track record when judging how much to trust a forecast.
- If the facts do not support an answer, say you do not know.
Be concise: under 220 words."""


class Ensemble:
    def __init__(self, ds, versions=None):
        d = os.path.join(ROOT, "models", ds.name)
        versions = versions or sorted(v for v in os.listdir(d) if os.path.exists(f"{d}/{v}/weights.pt"))
        self.members = [load_member(ds, v)[0] for v in versions]
        self.versions, self.ds = versions, ds

    @torch.no_grad()
    def __call__(self, x, obs, p, d):
        A = self.ds.A.to(DEV)
        qs = [self.ds.inv(m(x, p, d, A, obs)) for m in self.members]
        return torch.sort(torch.stack(qs).mean(0), -1).values[0].cpu().numpy()   # [H, N, 3]


def window_inputs(ds, window):
    idx = ds.indices("test")[window: window + 1]
    x, obs, y, p, d = ds.batch(idx, DEV)
    return idx[0], x, obs, y[0].cpu().numpy(), p, d


def neighbours(ds, node, k=3):
    w = ds.A[node].numpy().copy()
    w[node] = 0
    order = np.argsort(-w)
    return [int(j) for j in order[:k] if w[j] > 0]


def track_record(ds):
    p = os.path.join(ROOT, "results", f"{ds.name}__PWM-Dyn.json")
    if not os.path.exists(p):
        return "not yet measured - run evaluate_pwm.py"
    r = json.load(open(p))["ensemble_test"]
    return {"test_MAE": round(r["MAE"], 2), "test_RMSE": round(r["RMSE"], 2),
            "share_of_outcomes_inside_80pct_interval": round(r["interval_80_coverage"], 3),
            "MAE_by_step_ahead": [round(v, 2) for v in r["per_horizon_MAE"]]}


def step_label(ds, h):
    return f"+{(h + 1) * 5} min" if ds.period == 288 else f"+{h + 1} day"


def fmt_forecast(ds, q, node):
    return [{"ahead": step_label(ds, h), "median": round(float(q[h, node, 1]), 1),
             "p10": round(float(q[h, node, 0]), 1), "p90": round(float(q[h, node, 2]), 1)}
            for h in range(q.shape[0])]


def explain(ds, ens, a):
    t, x, obs, y, p, d = window_inputs(ds, a.window)
    q = ens(x, obs, p, d)
    hist = ds.raw[t - ds.in_len: t, a.node]
    facts = {
        "dataset": ds.name, "units": ds.units, "location_index": a.node,
        "observed_last_inputs": [None if np.isnan(v) else round(float(v), 1) for v in hist],
        "missing_inputs": int(np.isnan(hist).sum()),
        "pwm_forecast": fmt_forecast(ds, q, a.node),
        "neighbours_on_physical_graph": {str(j): fmt_forecast(ds, q, j)[:3] for j in neighbours(ds, a.node)},
        "pwm_track_record_on_held_out_test_data": track_record(ds),
        "ensemble_members": ens.versions,
    }
    if a.reveal_truth:      # for checking explanations against what actually happened
        facts["what_actually_happened"] = [None if np.isnan(v) else round(float(v), 1) for v in y[:, a.node]]
    return facts, "Explain PWM's forecast for this location: what was observed, what PWM expects next, how confident it is, and how the neighbouring locations relate."


def whatif(ds, ens, a):
    t, x, obs, y, p, d = window_inputs(ds, a.window)
    base = ens(x, obs, p, d)
    x2, obs2 = x.clone(), obs.clone()
    nodes = list(a.nodes)
    if a.scenario == "offline":
        obs2[..., nodes] = False
        x2 = x2 * obs2
    else:
        real = np.nan_to_num(ds.raw[t - ds.in_len: t][:, nodes])
        new = np.zeros_like(real) if a.scenario == "closure" else real * a.factor
        z = (ds.fwd(new) - ds.mean) / ds.std
        x2[0][:, nodes] = torch.tensor(z, dtype=x2.dtype, device=x2.device)
    alt = ens(x2, obs2, p, d)
    delta = alt[..., 1] - base[..., 1]                                    # [H, N] median change
    others = [j for j in np.argsort(-np.abs(delta).mean(0)) if j not in nodes][:5]
    facts = {
        "dataset": ds.name, "units": ds.units,
        "scenario": {"offline": "these locations stop reporting",
                     "closure": "these locations report zero (closure) for the whole input period",
                     "scale": f"observed inputs at these locations multiplied by {a.factor}"}[a.scenario],
        "changed_locations": nodes,
        "forecast_at_changed_locations": {str(n): {"baseline": fmt_forecast(ds, base, n)[:4],
                                                   "scenario": fmt_forecast(ds, alt, n)[:4]} for n in nodes},
        "most_affected_other_locations": {str(int(j)): round(float(delta[:, j].mean()), 2) for j in others},
        "graph_neighbours_of_changed_locations": {str(n): neighbours(ds, n) for n in nodes},
        "validation_status": "UNVALIDATED - simulated model response, no observed counterfactual exists",
        "pwm_track_record_on_held_out_test_data": track_record(ds),
    }
    return facts, "Explain what PWM's simulation suggests would change under this scenario, which other locations it affects, and how far this simulation can be trusted."


def call_llm(facts, question, a):
    key = os.environ.get(a.key_env)
    body = {"model": a.model, "temperature": 0.2,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": question + "\n\nFACTS (from PWM):\n" + json.dumps(facts, indent=1)}]}
    if a.dry_run or not key:
        return None, body
    req = urllib.request.Request(a.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"], body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["explain", "whatif"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--window", type=int, default=0, help="index into the test windows")
    ap.add_argument("--node", type=int, default=0)
    ap.add_argument("--nodes", type=int, nargs="*", default=[0])
    ap.add_argument("--scenario", default="closure", choices=["closure", "offline", "scale"])
    ap.add_argument("--factor", type=float, default=1.5)
    ap.add_argument("--reveal_truth", action="store_true")
    ap.add_argument("--model", default="openai/gpt-oss-120b")
    ap.add_argument("--base_url", default="https://api.groq.com/openai/v1")
    ap.add_argument("--key_env", default="GROQ_API_KEY")
    ap.add_argument("--dry_run", action="store_true")
    a = ap.parse_args()
    ds = load(a.data)
    ens = Ensemble(ds)
    facts, q = (explain if a.cmd == "explain" else whatif)(ds, ens, a)
    text, body = call_llm(facts, q, a)
    out = {"pwm_facts": {"provenance": "PWM-Dyn (Paradox-trained)", **facts},
           "explanation": {"provenance": f"{a.model} (external language model) - written from pwm_facts only",
                           "text": text or "[dry run / no API key: nothing sent]"}}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    p = os.path.join(ROOT, "results", f"reasoning_{ds.name}_{a.cmd}_w{a.window}.json")
    json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1)[:3000])
    if text is None:
        print("\n(no LLM call made; set", a.key_env, "to get gpt-oss's explanation)")


if __name__ == "__main__":
    main()
