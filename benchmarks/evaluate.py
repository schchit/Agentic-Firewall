from gateway import TransformRequest, transform_impl

cases = [
    {"target": "deploy_decision", "message": "Fact: tests passed. Risk: rollout window is short. Next step: deploy canary."},
    {"target": "rollback_decision", "message": "Error rate increased. Need rollback. Evidence: p95 latency doubled."},
]
for c in cases:
    print(transform_impl(TransformRequest(**c)))
