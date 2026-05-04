"""Agentic Firewall governance layer.

Combines four checks:
1. target-relevant compression preservation
2. observation -> target partition refinement
3. graph-topology uncertainty cascade detection
4. verifier placement for residual conflicts and spectral risk contraction
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Sequence, Tuple

from audit import make_audit_packet
from cascade import analyze_cascade, apply_verifiers, greedy_verifier_placement, matrix_from_edges, spectral_radius
from determinability import DeterminabilityReport, check_determinability

Edge = Tuple[str, str, float]


@dataclass
class FirewallDecision:
    timestamp_ms: int
    spectral_radius: float
    threshold: float
    status: str  # STABLE | CRITICAL | VERIFY | BLOCK | TERMINATE
    action: str  # ALLOW | REQUIRE_VERIFIER | BLOCK | TERMINATE
    reasons: List[str]
    cut_agents: List[str]
    verifier_nodes: List[str]
    residual_conflict_count: int = 0
    audit_packet: Dict[str, Any] | None = None

    @property
    def termination_command(self) -> str | None:
        return "$TERMINATION" if self.action == "TERMINATE" else None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def rank_risky_agents(agents: Sequence[str], m: List[List[float]]) -> List[str]:
    n = len(agents)
    scores: Dict[str, float] = {}
    for i, a in enumerate(agents):
        outgoing = sum(m[j][i] for j in range(n))
        incoming = sum(m[i][j] for j in range(n))
        scores[a] = outgoing * 1.2 + incoming
    return [k for k, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


def evaluate_firewall(
    agents: Sequence[str],
    edges: Sequence[Edge],
    threshold: float = 1.0,
    critical_margin: float = 0.9,
    residual_conflict_count: int = 0,
    high_stakes: bool = False,
    verifier_budget: int = 1,
    audit_secret: str | None = None,
) -> FirewallDecision:
    m = matrix_from_edges(agents, edges)
    rho = round(spectral_radius(m), 6)
    reasons: List[str] = []
    cut_agents: List[str] = []
    verifier_nodes: List[str] = []

    if residual_conflict_count > 0:
        reasons.append(f"residual_conflicts={residual_conflict_count}: observation does not determine target")

    if rho > threshold:
        reasons.append(f"spectral_radius={rho} exceeds threshold={threshold}")
        cut_agents = rank_risky_agents(agents, m)[: max(1, len(agents) // 5)]
        status, action = "TERMINATE", "TERMINATE"
    elif residual_conflict_count > 0 and high_stakes:
        reasons.append("high_stakes target with unresolved conflicts requires blocking or verifier")
        status, action = "BLOCK", "BLOCK"
    elif residual_conflict_count > 0 or rho >= critical_margin * threshold:
        if rho >= critical_margin * threshold:
            reasons.append(f"spectral_radius={rho} is near threshold={threshold}")
        budget = min(max(0, verifier_budget), len(agents))
        bbar = [0.01] * len(agents)
        idxs = greedy_verifier_placement(m, bbar, budget)
        verifier_nodes = [agents[i] for i in idxs]
        status, action = "VERIFY", "REQUIRE_VERIFIER"
    else:
        reasons.append("cascade stable and no residual conflicts")
        status, action = "STABLE", "ALLOW"

    decision = FirewallDecision(
        timestamp_ms=int(time.time() * 1000),
        spectral_radius=rho,
        threshold=threshold,
        status=status,
        action=action,
        reasons=reasons,
        cut_agents=cut_agents,
        verifier_nodes=verifier_nodes,
        residual_conflict_count=residual_conflict_count,
    )
    packet = make_audit_packet(decision.to_dict() | {"agents": list(agents), "edge_count": len(edges)}, secret=audit_secret)
    decision.audit_packet = packet.to_dict()
    return decision


def evaluate_governance(
    agents: Sequence[str],
    edges: Sequence[Edge],
    configs: Sequence[Any] | None = None,
    observation_fn: Callable[[Any], Any] | None = None,
    target_fn: Callable[[Any], Any] | None = None,
    target_name: str = "target",
    high_stakes: bool = False,
    threshold: float = 1.0,
) -> Dict[str, Any]:
    det: DeterminabilityReport | None = None
    residual = 0
    if configs is not None and observation_fn is not None and target_fn is not None:
        det = check_determinability(configs, observation_fn, target_fn, target_name=target_name)
        residual = det.residual_conflict_count
    decision = evaluate_firewall(
        agents=agents,
        edges=edges,
        threshold=threshold,
        residual_conflict_count=residual,
        high_stakes=high_stakes,
    )
    return {
        "target": target_name,
        "determinability": det.to_dict() if det else None,
        "firewall": decision.to_dict(),
    }


def dashboard_snapshot(agents: Sequence[str], edges: Sequence[Edge]) -> str:
    decision = evaluate_firewall(agents, edges)
    payload = {"topology": {"agents": list(agents), "edge_count": len(edges)}, "firewall": decision.to_dict()}
    return json.dumps(payload, ensure_ascii=False)
