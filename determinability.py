"""Finite target determinability checker.

A target D is zero-error determinable from observation Ω iff D is constant on
each observational equivalence class. If not, a same-observation / different-target
pair is returned as a concrete residual conflict certificate.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, Hashable, Iterable, List, Mapping, Sequence, Tuple


def stable_key(value: Any) -> Hashable:
    """Make arbitrary JSON-like values usable as deterministic grouping keys."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return repr(value)


@dataclass
class ConflictPair:
    observation: Any
    left: Any
    right: Any
    left_target: Any
    right_target: Any


@dataclass
class DeterminabilityReport:
    determinable: bool
    target: str
    observation_classes: int
    residual_conflict_count: int
    decision_table: Dict[str, Any]
    conflicts: List[ConflictPair]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def check_determinability(
    configs: Sequence[Any],
    observation_fn: Callable[[Any], Any],
    target_fn: Callable[[Any], Any],
    target_name: str = "target",
    max_conflicts: int = 10,
) -> DeterminabilityReport:
    """Check whether target_fn factors through observation_fn on finite configs."""
    groups: Dict[Hashable, List[Tuple[Any, Any, Any]]] = defaultdict(list)
    observations: Dict[Hashable, Any] = {}
    for c in configs:
        obs = observation_fn(c)
        key = stable_key(obs)
        observations[key] = obs
        groups[key].append((c, obs, target_fn(c)))

    conflicts: List[ConflictPair] = []
    decision_table: Dict[str, Any] = {}
    residual_count = 0
    for key, rows in groups.items():
        targets = {}
        for c, obs, tgt in rows:
            targets.setdefault(stable_key(tgt), (tgt, c, obs))
        if len(targets) == 1:
            only = next(iter(targets.values()))[0]
            decision_table[str(key)] = only
            continue
        values = list(targets.values())
        residual_count += len(values) - 1
        for i in range(min(len(values) - 1, max(0, max_conflicts - len(conflicts)))):
            t1, c1, obs1 = values[0]
            t2, c2, _ = values[i + 1]
            conflicts.append(ConflictPair(observation=obs1, left=c1, right=c2, left_target=t1, right_target=t2))
        decision_table[str(key)] = "__UNDETERMINED__"

    return DeterminabilityReport(
        determinable=(residual_count == 0),
        target=target_name,
        observation_classes=len(groups),
        residual_conflict_count=residual_count,
        decision_table=decision_table,
        conflicts=conflicts,
    )


def observation_refines_target(
    configs: Sequence[Any],
    observation_fn: Callable[[Any], Any],
    target_fn: Callable[[Any], Any],
) -> bool:
    return check_determinability(configs, observation_fn, target_fn).determinable
