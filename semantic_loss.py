"""Target-relative semantic compression checker.

A compressed message Z with context C is exact for target Q iff Q factors through
(Z,C). This module returns semantic-loss certificates when compression merges
histories requiring different target decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Sequence

from determinability import DeterminabilityReport, check_determinability


@dataclass
class SemanticLossReport:
    exact: bool
    target: str
    tokens_before: int | None
    tokens_after: int | None
    saving_ratio: float | None
    determinability: DeterminabilityReport

    @property
    def semantic_loss_certificates(self):
        return self.determinability.conflicts

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["semantic_loss_certificates"] = [asdict(c) for c in self.semantic_loss_certificates]
        return d


def default_token_count(x: Any) -> int:
    s = str(x)
    return max(1, (len(s) + 3) // 4)


def check_semantic_compression(
    histories: Sequence[Any],
    compressed_observation_fn: Callable[[Any], Any],
    target_fn: Callable[[Any], Any],
    context_fn: Callable[[Any], Any] | None = None,
    raw_observation_fn: Callable[[Any], Any] | None = None,
    target_name: str = "target",
) -> SemanticLossReport:
    def obs(h: Any):
        z = compressed_observation_fn(h)
        c = context_fn(h) if context_fn else None
        return {"compressed": z, "context": c}

    det = check_determinability(histories, obs, target_fn, target_name=target_name)

    tb = ta = ratio = None
    if raw_observation_fn is not None and histories:
        tb = sum(default_token_count(raw_observation_fn(h)) for h in histories)
        ta = sum(default_token_count(obs(h)) for h in histories)
        ratio = round(max(0, tb - ta) / max(1, tb), 4)

    return SemanticLossReport(
        exact=det.determinable,
        target=target_name,
        tokens_before=tb,
        tokens_after=ta,
        saving_ratio=ratio,
        determinability=det,
    )
