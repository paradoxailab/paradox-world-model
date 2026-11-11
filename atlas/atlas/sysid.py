"""In-context system identification: work out a system's dynamics from the one window being forecast.

The only assumptions are (1) the dynamics do not change during the window and the forecast, and (2) one step is a
linear combination of fixed geometric operators B_k applied to the last p states and forcings:

    x[t+1] = sum_{l<p} sum_k ( thA[l,k] B_k x[t-l] + thB[l,k] B_k u[t-l] )

Nothing about which equation it is, or its parameter values, is given. Three pieces:
  identify   ridge least squares for theta on the window (one-step equation error), with an optional prior
  smooth     given theta, the whole window is linear in its first p states: solve least squares for them against
             the observed (noisy, possibly missing) values. Gives a noise-free trajectory consistent with theta.
  refine     repeat: smooth, then re-identify with regressors taken from the smoothed trajectory and targets from
             the observations. Noise in the regressors biases plain least squares; this removes most of that bias.
All steps are batched linear solves and differentiable.
"""
import torch


def lag_features(x, u, basis, p):
    """x [B, N, T, C], u [B, N, T, U] -> [B, N, T-p, p*K*(C+U)]; basis [K, N, N], basis[0] = identity."""
    T = x.shape[2]; out = []
    for l in range(p):
        for a in (x, u):
            out.append(torch.einsum("knm,bmtc->bntkc", basis, a[:, :, p - 1 - l:T - 1 - l]).flatten(3))
    return torch.cat(out, -1)


def identify(x, u, basis, p, lam, theta0=None, target=None, w=None):
    """theta [B, F, C]. lam [F]: precision of the prior theta0 [B, F, C] (zero prior if None).
    target [B, N, T, C] (default x) and w [B, N, T, C] row weights (default 1) allow noisy/missing targets."""
    dt0 = x.dtype; x, u, basis, lam = x.double(), u.double(), basis.double(), lam.double()   # small solves: use float64
    theta0 = None if theta0 is None else theta0.double()
    target = None if target is None else target.double(); w = None if w is None else w.double()
    X = lag_features(x, u, basis, p).flatten(1, 2)                        # [B, R, F]
    Y = (x if target is None else target)[:, :, p:].flatten(1, 2)         # [B, R, C]
    Lam = torch.diag_embed(lam.expand(X.shape[0], -1))
    if w is None:
        G = (X.transpose(1, 2) @ X + Lam)[:, None]; rhs = (X.transpose(1, 2) @ Y).transpose(1, 2)[..., None]
    else:
        W = w[:, :, p:].flatten(1, 2)                                     # [B, R, C]
        Xw = X[:, None] * W.transpose(1, 2)[..., None]                    # [B, C, R, F]
        G = Xw.transpose(2, 3) @ X[:, None] + Lam[:, None]
        rhs = Xw.transpose(2, 3) @ Y.transpose(1, 2)[..., None]           # [B, C, F, 1]
    if theta0 is not None:
        rhs = rhs + (lam[None, :, None] * theta0).transpose(1, 2)[..., None]
    return torch.linalg.solve(G, rhs)[..., 0].transpose(1, 2).to(dt0)     # [B, F, C]


def operators(theta, basis, p, C, U):
    """theta -> A [B, p, NC, NC] acting on stacked states, G [B, p, NC, NU] acting on forcings."""
    B = theta.shape[0]; K, N = basis.shape[:2]
    th = theta.reshape(B, p, K * (C + U), C)
    tx = th[:, :, :K * C].reshape(B, p, K, C, C)                          # [.., k, c_in, c_out]
    tu = th[:, :, K * C:].reshape(B, p, K, U, C)
    A = torch.einsum("knm,blkic->blncmi", basis, tx).reshape(B, p, N * C, N * C)
    G = torch.einsum("knm,blkic->blncmi", basis, tu).reshape(B, p, N * C, N * U)
    return A, G


def _companion(A):
    B, p, S, _ = A.shape
    M = torch.zeros(B, p * S, p * S, dtype=A.dtype, device=A.device)
    M[:, :S] = A.transpose(1, 2).reshape(B, S, p * S)
    if p > 1:
        M[:, S:, :-S] = torch.eye((p - 1) * S, dtype=A.dtype, device=A.device)
    return M


def _flat(a):                                                             # [B, N, T, C] -> [B, T, N*C]
    return a.permute(0, 2, 1, 3).flatten(2)


def smooth_forecast(theta, y, w, u_all, basis, p, H, eps=1e-4, bound=50.0):
    """Fit the first p states of the window to the observations y [B, N, L, C] (weights w), given theta, then run
    the same dynamics H steps past the window. Returns the smoothed window [B, N, L, C] and forecast [B, N, H, C]."""
    dt0 = y.dtype; theta, y, w, u_all, basis = theta.double(), y.double(), w.double(), u_all.double(), basis.double()
    B, N, L, C = y.shape; U = u_all.shape[-1]; S = N * C
    A, G = operators(theta, basis, p, C, U)
    M = _companion(A)                                                     # [B, pS, pS]
    yf, wf, uf = _flat(y), _flat(w), _flat(u_all)                         # [B, T, S]
    T = L + H
    # history vector h_t = (x_t, x_{t-1}, ..), t = p-1 .. T-1.  h_{t+1} = M h_t + (sum_l G_l u_{t-l}, 0)
    P = torch.eye(p * S, dtype=y.dtype, device=y.device).expand(B, -1, -1)
    g = torch.zeros(B, p * S, dtype=y.dtype, device=y.device)
    Phi = [P[:, (p - 1 - j) * S:(p - j) * S] for j in range(p)]           # rows for x_0 .. x_{p-1}
    f = [g[:, :S]] * p
    for t in range(p - 1, T - 1):
        inj = sum(torch.einsum("bsu,bu->bs", G[:, l], uf[:, t - l]) for l in range(p))
        P = (M @ P).clamp(-bound, bound)
        g = torch.einsum("bij,bj->bi", M, g)
        g = torch.cat([g[:, :S] + inj, g[:, S:]], 1).clamp(-bound, bound)
        Phi.append(P[:, :S]); f.append(g[:, :S])
    Phi, f = torch.stack(Phi, 1), torch.stack(f, 1)                       # [B, T, S, pS], [B, T, S]
    Pw = Phi[:, :L] * wf[..., None]
    Gm = torch.einsum("btsi,btsj->bij", Pw, Phi[:, :L]) + eps * torch.eye(p * S, dtype=y.dtype, device=y.device)
    h0 = torch.linalg.solve(Gm, torch.einsum("btsi,bts->bi", Pw, yf - f[:, :L])[..., None])[..., 0]
    full = (torch.einsum("btsi,bi->bts", Phi, h0) + f).clamp(-bound, bound)
    full = full.reshape(B, T, N, C).permute(0, 2, 1, 3)
    return full[:, :, :L].to(dt0), full[:, :, L:].to(dt0)


def refine(x0, y, w, u_all, basis, p, H, lam, theta0=None, iters=2):
    """identify on x0 (a filled-in window), then alternate smooth / re-identify. Returns theta, smoothed, forecast."""
    L = y.shape[2]
    theta = identify(x0, u_all[:, :, :L], basis, p, lam, theta0)
    for _ in range(iters):
        xs, _ = smooth_forecast(theta, y, w, u_all, basis, p, 0)
        theta = identify(xs, u_all[:, :, :L], basis, p, lam, theta0, target=y, w=w)
    xs, fc = smooth_forecast(theta, y, w, u_all, basis, p, H)
    return theta, xs, fc


def ring_basis(M):
    """Shift operators on a ring of M nodes (B_0 = identity)."""
    i = torch.arange(M)
    return torch.stack([(i[None] == (i[:, None] + k) % M).float() for k in range(M)])
