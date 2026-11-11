"""Physical systems with known equations, simulated exactly (no numerical-integration error).

Every system here is linear in its state once its parameters are fixed, so one step is

    s[t+1] = A(theta) s[t] + B(theta) u[t]          observation  y[t] = Cobs s[t] + noise

with u piecewise constant over a step (the "intervention" input: a force or an emission source).
A and B come from the exact solution of the differential equation over one step.

  harmonic   x'' = -w^2 x + u                         theta = (w)        state (x, v), observe x
  damped     x'' = -w^2 x - 2 z w x' + u              theta = (w, z)     state (x, v), observe x
  diffusion  c_t = D c_xx + u      (ring of M nodes)  theta = (D)        state = c at every node
  advdiff    c_t = -a c_x + D c_xx + u  (ring)        theta = (D, a)     state = c at every node

Each trajectory draws its own theta, initial state and forcing, so a model cannot do well by remembering one
trajectory: it has to work out the dynamics from the 16 observed steps.
"""
import numpy as np
from scipy.linalg import expm

L, H = 16, 16          # observed steps, predicted steps
DT = 0.3
M = 8                  # ring nodes for the transport systems

SYSTEMS = {
    # name: (parameter names, in-distribution ranges, out-of-distribution ranges)
    "harmonic": (("w",), ((0.5, 2.0),), ((2.0, 2.5),)),
    "damped": (("w", "z"), ((0.5, 2.0), (0.0, 0.3)), ((2.0, 2.5), (0.0, 0.3))),
    "diffusion": (("D",), ((0.05, 0.8),), ((0.8, 1.2),)),
    "advdiff": (("D", "a"), ((0.05, 0.8), (-1.5, 1.5)), ((0.05, 0.8), (1.5, 2.2))),
}


def is_ring(name):
    return name in ("diffusion", "advdiff")


def step_matrices(name, theta):
    """Exact one-step matrices A [S, S], B [S, U] and observation matrix Cobs for one parameter vector."""
    if name in ("harmonic", "damped"):
        w = theta[0]
        z = theta[1] if name == "damped" else 0.0
        Mx = np.array([[0.0, 1.0], [-w * w, -2 * z * w]])
        A = expm(Mx * DT)
        B = np.linalg.solve(Mx, (A - np.eye(2)) @ np.array([[0.0], [1.0]]))
        return A, B, np.array([[1.0, 0.0]])
    D = theta[0]
    a = theta[1] if name == "advdiff" else 0.0
    k = 2 * np.pi * np.fft.fftfreq(M, d=1.0)              # node spacing 1
    lam = D * k * k + 1j * a * k
    e = np.exp(-lam * DT)
    g = np.where(np.abs(lam) > 1e-12, (1 - e) / np.where(np.abs(lam) > 1e-12, lam, 1), DT)
    F = np.fft.fft(np.eye(M), axis=0)
    A = np.real(np.fft.ifft(e[:, None] * F, axis=0))
    B = np.real(np.fft.ifft(g[:, None] * F, axis=0))
    return A, B, np.eye(M)


def sample_theta(name, n, rng, ood=False, width=1.0):
    """width < 1 shrinks the in-distribution range about its centre (the diversity experiment)."""
    _, rin, rout = SYSTEMS[name]
    out = []
    for (lo, hi), (olo, ohi) in zip(rin, rout):
        if ood:
            out.append(rng.uniform(olo, ohi, n))
        else:
            c, h = 0.5 * (lo + hi), 0.5 * (hi - lo) * width
            out.append(rng.uniform(c - h, c + h, n))
    return np.stack(out, -1)


def sample_init(name, n, rng):
    if not is_ring(name):
        return rng.normal(0, 1, (n, 2))
    x = np.arange(M)
    s = 1.0 + 0.3 * rng.normal(0, 1, (n, 1)) + sum(
        rng.normal(0, 0.6 / m, (n, 1)) * np.cos(2 * np.pi * m * x / M + rng.uniform(0, 2 * np.pi, (n, 1)))
        for m in (1, 2, 3))
    return s


def sample_forcing(name, n, rng, T=L + H, p_on=0.6):
    """Piecewise-constant forcing. 40% of trajectories are unforced; the rest switch a constant forcing on at a
    random step (anywhere in the window) and may switch it off again. Ring systems: a source at one node."""
    U = M if is_ring(name) else 1
    u = np.zeros((n, T, U))
    on = rng.random(n) < p_on
    t0 = rng.integers(0, T, n)
    t1 = np.where(rng.random(n) < 0.5, T, rng.integers(0, T, n) + t0)
    amp = rng.normal(0, 1.0, n) if not is_ring(name) else rng.uniform(0.2, 1.5, n)
    node = rng.integers(0, U, n)
    tt = np.arange(T)[None]
    act = on[:, None] & (tt >= t0[:, None]) & (tt < t1[:, None])
    u[np.arange(n)[:, None], tt, node[:, None]] = act * amp[:, None]
    return u


def simulate(name, theta, s0, u):
    """theta [n, p], s0 [n, S], u [n, T, U] -> clean observations [n, T, C] (y[t] is the state BEFORE step t)."""
    n, T = u.shape[:2]
    ys = []
    for i in range(n):
        A, B, Cobs = step_matrices(name, theta[i])
        s = s0[i]
        y = np.empty((T, Cobs.shape[0]))
        for t in range(T):
            y[t] = Cobs @ s
            s = A @ s + B @ u[i, t]
        ys.append(y)
    return np.stack(ys)


def make(name, n, seed, noise=0.05, ood=False, width=1.0, u=None, theta=None, s0=None):
    """A dataset of n independent trajectories.
    Returns dict: yc [n, N, L, 1] noisy context, yf [n, N, H, 1] CLEAN future, yfn noisy future (training target),
    uc, uf [n, N, L|H, 1] forcing, theta, s0, u. N = 1 node for oscillators, M for ring systems."""
    rng = np.random.default_rng(seed)
    theta = sample_theta(name, n, rng, ood, width) if theta is None else theta
    s0 = sample_init(name, n, rng) if s0 is None else s0
    u = sample_forcing(name, n, rng) if u is None else u
    y = simulate(name, theta, s0, u)                              # [n, T, C]
    yn = y + noise * rng.normal(0, 1, y.shape)
    f = lambda a: np.ascontiguousarray(a.transpose(0, 2, 1)[..., None]).astype(np.float32)   # [n, N, T, 1]
    Y, Yn, Uu = f(y), f(yn), f(u)
    return dict(yc=Yn[:, :, :L], yf=Y[:, :, L:], yfn=Yn[:, :, L:], uc=Uu[:, :, :L], uf=Uu[:, :, L:],
                theta=theta, s0=s0, u=u, clean_ctx=Y[:, :, :L])


def grid(name, k=24, ood=False):
    _, rin, rout = SYSTEMS[name]
    rr = rout if ood else rin
    axes = [np.linspace(lo, hi, k) for lo, hi in rr]
    return np.stack([g.ravel() for g in np.meshgrid(*axes, indexing="ij")], -1)


def oracle(name, d, k=24, ood=False):
    """Equation-aware reference forecast: knows the equation form and the forcing, not the parameters or the state.
    For every parameter value on a k-per-axis grid it solves least squares for the initial state from the noisy
    context, keeps the best-fitting parameter for each trajectory, and forecasts with the exact equations.
    Returns predictions [n, N, H, 1]. This is the error floor a perfect learner of the equations could reach."""
    yc = d["yc"][..., 0].transpose(0, 2, 1).astype(np.float64)        # [n, L, C]
    u = d["u"]
    n = len(yc)
    best = np.full(n, np.inf)
    pred = np.zeros((n, H, yc.shape[2]))
    for th in grid(name, k, ood):
        A, B, Cobs = step_matrices(name, th)
        S, C = A.shape[0], Cobs.shape[0]
        O = np.empty((L, C, S)); P = Cobs.copy()
        for t in range(L):
            O[t] = P; P = P @ A
        # forced response with zero initial state
        s = np.zeros((n, S)); fr = np.empty((n, L + H, C))
        for t in range(L + H):
            fr[:, t] = s @ Cobs.T
            s = s @ A.T + u[:, t] @ B.T
        Om = O.reshape(L * C, S)
        r = (yc - fr[:, :L]).reshape(n, L * C)
        s0 = r @ np.linalg.pinv(Om).T                                   # [n, S]
        res = ((r - s0 @ Om.T) ** 2).sum(1)
        s = s0.copy(); full = np.empty((n, L + H, C))
        for t in range(L + H):
            full[:, t] = s @ Cobs.T
            s = s @ A.T
        full += fr
        upd = res < best
        best[upd] = res[upd]; pred[upd] = full[upd, L:]
    return pred.transpose(0, 2, 1)[..., None].astype(np.float32)


def persistence(d):
    return np.repeat(d["yc"][:, :, -1:], H, 2)


def nmse(pred, d):
    """Mean squared error of the forecast against the CLEAN future, divided by the variance of the clean future."""
    y = d["yf"]
    return float(((pred - y) ** 2).mean() / y.var())


def complexity_bits(name, target, n=400, seed=7):
    """Rate-distortion view of the system: how many bits are needed to state its parameters precisely enough that
    the H-step forecast error (normalised MSE, perfect knowledge of the state) stays under `target`.
    For each parameter: delta = largest perturbation keeping the error under target (median over trajectories,
    found by bisection); bits = log2(range / (2 * delta)). Returns (total bits, per-parameter bits)."""
    rng = np.random.default_rng(seed)
    names, rin, _ = SYSTEMS[name]
    th = sample_theta(name, n, rng); s0 = sample_init(name, n, rng); u = sample_forcing(name, n, rng)
    y = simulate(name, th, s0, u)
    var = y[:, L:].var()
    # state at the forecast start is known exactly: compare futures only
    bits = []
    for i, (lo, hi) in enumerate(rin):
        a, b = 1e-6, (hi - lo)
        for _ in range(30):
            mid = np.sqrt(a * b)
            t2 = th.copy(); t2[:, i] += mid
            # re-anchor: same state at the forecast start, so only the dynamics differ
            e = _anchored_err(name, th, t2, s0, u, y) / var
            if e < target: a = mid
            else: b = mid
        bits.append(max(0.0, float(np.log2((hi - lo) / (2 * a)))))
    return float(sum(bits)), dict(zip(names, bits))


def _anchored_err(name, th, th2, s0, u, y):
    n = len(th); err = 0.0; cnt = 0
    for i in range(n):
        A, B, Cobs = step_matrices(name, th[i])
        s = s0[i]
        for t in range(L):
            s = A @ s + B @ u[i, t]
        A2, B2, _ = step_matrices(name, th2[i])
        for t in range(L, L + H):
            err += ((Cobs @ s - y[i, t]) ** 2).sum(); cnt += Cobs.shape[0]
            s = A2 @ s + B2 @ u[i, t]
    return err / cnt
