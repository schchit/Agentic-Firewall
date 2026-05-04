# Agentic Firewall + Determinability Governance Layer

Agentic Firewall is a graph-theoretic communication firewall for multi-agent systems. It detects whether compressed agent messages preserve target-relevant facts, whether observations are sufficient for target determination, whether the agent topology causes uncertainty cascades, and where verifiers should be placed to reduce residual conflicts and spectral risk.

This enhanced version keeps the original project shape (`gateway.py`, `cascade.py`, `firewall.py`) and adds the missing determinability layer so it can be used directly as a practical runtime component.

## Core Checks

1. **Target-Relevant Compression**  
   Does message compression preserve the facts needed to determine the target?

2. **Observation-Target Refinement**  
   Does the available observation refine the target partition? Can the current observation distinguish configurations that require different target decisions?

3. **Uncertainty Cascade Detection**  
   Does the communication topology amplify uncertainty across the agent graph? The system estimates spectral radius and classifies the graph as convergent, critical, or unstable.

4. **Verifier Placement and Risk Contraction**  
   Do verifier nodes cover residual conflicts and reduce spectral risk? The firewall recommends verifier nodes when conflicts or critical cascade risk appear.

## What Was Added

- `determinability.py` — finite `(F, Ω, D)` checker with decision table or residual conflict certificate.
- `semantic_loss.py` — target-relative compression checker with semantic-loss certificates.
- `cascade.py` — cleaned uncertainty cascade engine with spectral-radius analysis.
- `firewall.py` — integrated governance decision combining residual conflicts and cascade risk.
- `audit.py` — JEP-style canonical JSON, SHA-256 hash, and optional HMAC audit packet.
- `gateway.py` — usable FastAPI gateway with `/transform` and `/firewall/evaluate`.
- `tests/` — minimal unit tests for determinability, semantic loss, cascade, and firewall behavior.

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python examples/basic_usage.py
```

## Run API

```bash
uvicorn gateway:app --host 0.0.0.0 --port 8080
```

Transform a message:

```bash
curl -X POST http://127.0.0.1:8080/transform \
  -H "Content-Type: application/json" \
  -d '{"target":"deploy_decision","message":"Fact: tests passed. Risk: rollout window is short. Next step: deploy canary."}'
```

Evaluate firewall risk:

```bash
curl -X POST http://127.0.0.1:8080/firewall/evaluate \
  -H "Content-Type: application/json" \
  -d '{"agents":["planner","coder","reviewer"],"edges":[["planner","coder",0.8],["coder","reviewer",0.9]],"residual_conflict_count":1}'
```

## Python Usage

```python
from determinability import check_determinability
from firewall import evaluate_firewall

configs = [
    {"obs": "same", "target": "allow"},
    {"obs": "same", "target": "block"},
]

report = check_determinability(configs, lambda c: c["obs"], lambda c: c["target"])
print(report.determinable)          # False
print(report.conflicts[0])          # same-observation / different-target certificate

agents = ["planner", "coder", "reviewer"]
edges = [("planner", "coder", 0.8), ("coder", "reviewer", 0.9)]
decision = evaluate_firewall(agents, edges, residual_conflict_count=report.residual_conflict_count)
print(decision.action)              # REQUIRE_VERIFIER / TERMINATE / ALLOW
```

## GitHub Description

Risk-aware communication firewall for multi-agent systems: target-relevant compression, observation refinement, uncertainty cascade detection, verifier placement, and audit packets.

## Topics

```text
agentic-firewall
multi-agent-systems
agent-communication
uncertainty-cascade
target-determinability
semantic-compression
verifier-placement
graph-theory
risk-propagation
ai-governance
agent-safety
llm-agents
agentic-ai
observability
auditability
```

## Notes

This is a practical engineering implementation of the determinability-governance direction. The audit packet uses canonical JSON + SHA-256 + optional HMAC. For full cryptographic JEP compatibility, replace or extend `audit.py` with the dedicated JEP signing SDK.
