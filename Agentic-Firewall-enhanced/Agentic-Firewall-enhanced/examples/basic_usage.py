from determinability import check_determinability
from semantic_loss import check_semantic_compression
from firewall import evaluate_firewall

configs = [
    {"id": 1, "obs": "same", "target": "allow"},
    {"id": 2, "obs": "same", "target": "block"},
    {"id": 3, "obs": "clear", "target": "allow"},
]

report = check_determinability(configs, lambda c: c["obs"], lambda c: c["target"], "deploy_decision")
print("determinability:", report.to_dict())

agents = ["planner", "coder", "reviewer", "deployer"]
edges = [("planner", "coder", 0.7), ("coder", "reviewer", 0.8), ("reviewer", "deployer", 0.9), ("deployer", "coder", 0.6)]
print("firewall:", evaluate_firewall(agents, edges, residual_conflict_count=report.residual_conflict_count).to_dict())
