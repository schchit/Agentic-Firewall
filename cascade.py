"""Graph-theoretic uncertainty cascade model for multi-agent systems.

Core recurrence:
    r[t+1] <= A_G r[t] + b[t]

The spectral radius rho(A_G) is used as a finite runtime signal:
- rho < 1: convergent / contracting risk
- rho ~= 1: critical
- rho > 1: unstable / possible uncertainty cascade
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Sequence, Tuple

Vector = List[float]
Matrix = List[List[float]]
Edge = Tuple[str, str, float]


def matvec(a: Matrix, x: Vector) -> Vector:
    if not a:
        return []
    return [sum(a[i][j] * x[j] for j in range(len(x))) for i in range(len(a))]


def addv(x: Vector, y: Vector) -> Vector:
    return [x[i] + y[i] for i in range(len(x))]


def max_abs(x: Vector) -> float:
    return max((abs(v) for v in x), default=0.0)


def matrix_from_edges(agents: Sequence[str], edges: Sequence[Edge]) -> Matrix:
    """Build A_G where edge src -> dst contributes to row dst, column src."""
    idx = {a: i for i, a in enumerate(agents)}
    n = len(agents)
    m = [[0.0 for _ in range(n)] for _ in range(n)]
    for src, dst, w in edges:
        if src in idx and dst in idx:
            m[idx[dst]][idx[src]] += max(0.0, float(w))
    return m


def spectral_radius(a: Matrix, iters: int = 120) -> float:
    """Power-iteration estimate for nonnegative matrices."""
    n = len(a)
    if n == 0:
        return 0.0
    v = [1.0 / math.sqrt(n)] * n
    lam = 0.0
    for _ in range(iters):
        av = matvec(a, v)
        norm = math.sqrt(sum(z * z for z in av))
        if norm == 0:
            return 0.0
        v = [z / norm for z in av]
        av2 = matvec(a, v)
        lam = sum(v[i] * av2[i] for i in range(n))
    return max(0.0, float(lam))


@dataclass
class CascadeReport:
    rho: float
    regime: str  # convergent | critical | unstable
    fixed_point_bound: Vector
    trajectory: List[Vector]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def propagate(a: Matrix, r0: Vector, b: Sequence[Vector], steps: int) -> List[Vector]:
    traj = [r0[:]]
    r = r0[:]
    if not b:
        b = [[0.0] * len(r0)]
    for t in range(max(0, steps)):
        bt = b[t] if t < len(b) else b[-1]
        r = addv(matvec(a, r), list(bt))
        traj.append(r)
    return traj


def fixed_point_bound(a: Matrix, bbar: Vector, eps: float = 1e-8, max_iter: int = 2000) -> Vector:
    """Monotone iteration for r = A r + bbar.

    For rho(A)<1 this converges to (I-A)^-1 bbar. For rho>=1 it returns the
    last iterate, useful as a warning-scale bound rather than a proof of convergence.
    """
    r = [0.0] * len(bbar)
    for _ in range(max_iter):
        nr = addv(matvec(a, r), bbar)
        if max_abs([nr[i] - r[i] for i in range(len(r))]) < eps:
            return nr
        r = nr
    return r


def analyze_cascade(a: Matrix, r0: Vector | None = None, bbar: Vector | None = None, steps: int = 20) -> CascadeReport:
    n = len(a)
    r0 = r0 if r0 is not None else [0.1] * n
    bbar = bbar if bbar is not None else [0.0] * n
    rho = spectral_radius(a)
    if rho < 0.999:
        regime = "convergent"
    elif rho <= 1.001:
        regime = "critical"
    else:
        regime = "unstable"
    traj = propagate(a, r0, [bbar], steps)
    fp = fixed_point_bound(a, bbar)
    return CascadeReport(rho=round(rho, 6), regime=regime, fixed_point_bound=fp, trajectory=traj)


def false_consensus(trajectory_msgs: List[Vector], trajectory_risk: List[Vector], eta: float, eps: float) -> List[int]:
    """Return rounds where disagreement is low but mean target risk is high."""
    hits: List[int] = []
    for t, msgs in enumerate(trajectory_msgs):
        if not msgs or t >= len(trajectory_risk) or not trajectory_risk[t]:
            continue
        dispersion = max(msgs) - min(msgs)
        mean_risk = sum(trajectory_risk[t]) / len(trajectory_risk[t])
        if dispersion <= eta and mean_risk >= eps:
            hits.append(t)
    return hits


def apply_verifiers(
    a: Matrix,
    bbar: Vector,
    verifier_nodes: Sequence[int],
    edge_decay: float = 0.5,
    noise_decay: float = 0.5,
) -> Tuple[Matrix, Vector]:
    """Return modified A,b after verifier nodes damp local edge influence/noise."""
    n = len(a)
    na = [row[:] for row in a]
    nb = bbar[:]
    for v in verifier_nodes:
        if 0 <= v < n:
            for j in range(n):
                na[v][j] *= edge_decay
                na[j][v] *= edge_decay
            nb[v] *= noise_decay
    return na, nb


def greedy_verifier_placement(a: Matrix, bbar: Vector, budget: int) -> List[int]:
    """Greedily choose verifier nodes that most reduce spectral radius."""
    n = len(a)
    chosen: List[int] = []
    remaining = set(range(n))
    cur_a, cur_b = [row[:] for row in a], bbar[:]
    for _ in range(max(0, budget)):
        best = None
        best_rho = spectral_radius(cur_a)
        for cand in list(remaining):
            ta, _ = apply_verifiers(cur_a, cur_b, [cand])
            rho = spectral_radius(ta)
            if rho < best_rho:
                best_rho = rho
                best = cand
        if best is None:
            break
        chosen.append(best)
        remaining.remove(best)
        cur_a, cur_b = apply_verifiers(cur_a, cur_b, [best])
    return chosen
