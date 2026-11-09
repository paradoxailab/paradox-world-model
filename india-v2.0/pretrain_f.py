"""Pretrain PWM-F (pw/fenc.py, ~10M parameters) on the all-India ISD corpus (tools/fetch_india.py).

Objective: 10/50/90% quantile (pinball) loss on the next 24 h of temperature, humidity and wind, in each window's own
normalised units, plus 0.1 x reconstruction of 15% hidden days. Windows: a random station and a random forecast
start; kept if >= 30% of the 21-day history and >= 25% of the next 24 h have a temperature. Model selection: the
last 60 days before the corpus cutoff (all stations) are held out and only used to pick the checkpoint.

  python pretrain_f.py --steps 40000 --batch 512 --hours 2.5      # -> $PW_OUT/fenc.pt
"""
import argparse, math, os, time

import numpy as np
import torch

from pw.fenc import PWMF, K, P, SPD, H

RAW = os.environ.get("PW_RAW", "data/raw")
OUT = os.environ.get("PW_OUT", "out")
LC = P * SPD
QS = torch.tensor([0.1, 0.5, 0.9])


def solar(lat, lon, hours):
    """sine of solar elevation; hours: datetime64[h] array [B, H]; lat, lon: [B]."""
    days = hours.astype("datetime64[D]")
    doy = (days - days.astype("datetime64[Y]")).astype(np.int64)
    hh = (hours.astype(np.int64) % 24).astype(np.float64)
    dec = np.deg2rad(23.44) * np.sin(2 * math.pi * (284 + doy) / 365.0)
    ha = np.deg2rad(15.0 * (hh + lon[:, None] / 15.0 - 12.0))
    la = np.deg2rad(lat)[:, None]
    return (np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)).astype(np.float32)


class Corpus:
    def __init__(self, path, dev):
        z = np.load(path)
        names = [str(v) for v in z["vars"]]
        X = z["X"][..., [names.index(v) for v in ("AT", "RH", "WS")]].astype(np.float32)   # [T, N, 3]
        self.T, self.N = X.shape[:2]
        self.start = np.datetime64(str(z["start"]), "h")
        self.lat, self.lon = z["lat"].astype(np.float64), z["lon"].astype(np.float64)
        obs = np.isfinite(X)
        self.X = torch.from_numpy(np.nan_to_num(X)).half().to(dev)
        self.O = torch.from_numpy(obs).to(dev)
        c = np.concatenate([np.zeros((1, self.N)), np.cumsum(obs[..., 0], 0)], 0)   # temperature coverage
        self.cum = c
        self.val_from = self.T - 60 * 24
        self.dev = dev
        print(f"corpus: {self.T} hours x {self.N} stations, {int(obs[..., 0].sum()):,} observed temperature hours; "
              f"held-out model-selection period = last 60 days", flush=True)

    def sample(self, B, rng, split):
        lo, hi = (LC, self.val_from - H) if split == "train" else (self.val_from, self.T - H)
        s_all, t_all = [], []
        while sum(len(s) for s in s_all) < B:
            s = rng.integers(0, self.N, 4 * B)
            t = rng.integers(lo, hi, 4 * B)
            hist = (self.cum[t, s] - self.cum[t - LC, s]) / LC
            fut = (self.cum[t + H, s] - self.cum[t, s]) / H
            ok = (hist >= 0.3) & (fut >= 0.25)
            s_all.append(s[ok]); t_all.append(t[ok])
        s, t = np.concatenate(s_all)[:B], np.concatenate(t_all)[:B]
        return self.batch(s, t)

    def batch(self, s, t):
        dev = self.dev
        idx = torch.from_numpy(t[:, None] + np.arange(-LC, H)).to(dev)              # [B, LC+H]
        st = torch.from_numpy(s).to(dev)
        x = self.X[idx, st[:, None]].float()                                       # [B, LC+H, 3]
        o = self.O[idx, st[:, None]].float()
        v = x[:, :LC].permute(0, 2, 1).reshape(-1, K, P, SPD)
        m = o[:, :LC].permute(0, 2, 1).reshape(-1, K, P, SPD)
        y, yo = x[:, LC:].permute(0, 2, 1), o[:, LC:].permute(0, 2, 1)            # [B, K, H]
        hours = self.start + t[:, None] + np.arange(H)
        sun = torch.from_numpy(solar(self.lat[s], self.lon[s], hours)).to(dev)
        days = (self.start + t).astype("datetime64[D]")
        doy = (days - days.astype("datetime64[Y]")).astype(np.int64)
        doy = torch.from_numpy(np.stack([np.sin(2 * math.pi * doy / 365.25), np.cos(2 * math.pi * doy / 365.25)],
                                        -1).astype(np.float32)).to(dev)
        return v, m, sun, doy, y, yo


def pinball(q, y, yo, sc):
    """q: [B, K, H, 3] real units; loss in each window's normalised units."""
    e = (y[..., None] - q) / sc[..., 0, :, None]
    qs = QS.to(q.device)
    l = torch.maximum(qs * e, (qs - 1) * e)
    return (l * yo[..., None]).sum() / (yo.sum() * 3).clamp(min=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=40000)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--hours", type=float, default=2.5, help="wall-clock cap")
    ap.add_argument("--corpus", default=next((os.path.join(RAW, f) for f in ("PRE_INDIA.npz", "WX_INDIA.npz")
                                                if os.path.exists(os.path.join(RAW, f))), os.path.join(RAW, "PRE_INDIA.npz")))
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(0)
    rng = np.random.default_rng(0)
    C = Corpus(a.corpus, dev)
    vb = [C.sample(a.batch, np.random.default_rng(1000 + i), "val") for i in range(8)]   # fixed validation batches
    m = PWMF().to(dev)
    print(f"PWM-F: {m.n_params():,} parameters; device {dev}", flush=True)
    opt = torch.optim.AdamW(m.parameters(), lr=a.lr, weight_decay=0.05, betas=(0.9, 0.95))
    warm = 1000
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1, s / a.steps)))))
    use_amp = dev == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    best, t0, step = float("inf"), time.time(), 0

    def evaluate():
        m.eval()
        tot = n = 0.0
        mae = torch.zeros(K)
        with torch.no_grad(), torch.autocast("cuda", enabled=use_amp):
            for v, mk, sun, doy, y, yo in vb:
                q, _, (mu, sc) = m(v, mk, sun, doy)
                tot += pinball(q.float(), y, yo, sc.float()).item(); n += 1
                mae += ((q[..., 1].float() - y).abs() * yo).sum((0, 2)).cpu() / yo.sum((0, 2)).cpu().clamp(min=1)
        m.train()
        return tot / n, (mae / n).tolist()

    for step in range(a.steps):
        v, mk, sun, doy, y, yo = C.sample(a.batch, rng, "train")
        with torch.autocast("cuda", enabled=use_amp):
            q, rec, (mu, sc) = m(v, mk, sun, doy, hide_frac=0.15)
            loss = pinball(q.float(), y, yo, sc.float()) + 0.1 * rec
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step()
        if (step + 1) % 1000 == 0 or step == a.steps - 1:
            vl, vm = evaluate()
            tag = ""
            if vl < best:
                best = vl
                torch.save({"cfg": m.cfg, "state": m.state_dict(), "step": step + 1, "val": vl},
                           os.path.join(OUT, "fenc.pt"))
                tag = " (saved)"
            loads = [round(float(x), 3) for x in m.layers[0].moe.load]
            print(f"  step {step + 1}/{a.steps} loss {loss.item():.4f} held-out pinball {vl:.4f} "
                  f"MAE [C, %, m/s] {[round(x, 3) for x in vm]} expert load (layer 1) {loads} "
                  f"{time.time() - t0:.0f}s{tag}", flush=True)
        if time.time() - t0 > a.hours * 3600:
            print(f"  wall-clock cap reached at step {step + 1}", flush=True)
            break
    print(f"PRETRAIN-RESULT PWM-F {m.n_params():,} params, best held-out pinball {best:.4f}, "
          f"{time.time() - t0:.0f}s, saved {os.path.join(OUT, 'fenc.pt')}", flush=True)


if __name__ == "__main__":
    main()
