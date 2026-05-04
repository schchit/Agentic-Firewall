"""FastAPI gateway for Agentic Firewall.

Run:
    uvicorn gateway:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    from fastapi import FastAPI, Header, HTTPException, Request, Response
    from pydantic import BaseModel
except Exception:  # Allow core modules/tests to run without FastAPI installed.
    FastAPI = None
    Header = None
    HTTPException = Exception
    Request = object
    Response = object
    BaseModel = object

from audit import make_audit_packet
from firewall import evaluate_firewall

API_VERSION = "v4.0-determinability"

STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and", "or", "in", "on", "for", "with"}


def _sentences(text: str) -> List[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?。！？])\s+", text.strip()) if x.strip()]


def _extract(text: str, keys: List[str]) -> List[str]:
    return [s for s in _sentences(text) if any(k in s.lower() for k in keys)][:6]


def _kw(text: str, k: int = 8) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:k]]


def token_count(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


@dataclass
class CompressedMessage:
    intent: str
    facts: List[str]
    action_items: List[str]
    blockers: List[str]
    target_relevant_facts: List[str]
    confidence: float
    strategy: str
    fallback_used: bool = False


if BaseModel is object:
    class TransformRequest:  # type: ignore
        def __init__(self, target="general_decision", message="", strategy="heuristic", min_confidence=0.65, redaction_level="standard"):
            self.target = target; self.message = message; self.strategy = strategy; self.min_confidence = min_confidence; self.redaction_level = redaction_level
else:
    class TransformRequest(BaseModel):
        target: str = "general_decision"
        message: str
        strategy: str = "heuristic"
        min_confidence: float = 0.65
        redaction_level: str = "standard"


def redact_sensitive(text: str, level: str = "standard") -> str:
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD]", text)
    if level == "strict":
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_ID]", text)
    return text


def compress_heuristic(text: str, target: str) -> CompressedMessage:
    s = _sentences(text)
    facts = _extract(text, ["fact", "data", "result", "observed", "evidence", "发现", "证据", "结果"])
    actions = _extract(text, ["need", "should", "must", "next", "deploy", "pause", "rollback", "需要", "下一步", "执行"])
    blockers = _extract(text, ["risk", "issue", "error", "fail", "unsafe", "block", "风险", "问题", "失败"])
    target_words = [w for w in re.findall(r"[A-Za-z0-9_\-]{3,}", target.lower()) if w not in STOPWORDS]
    target_relevant = [sent for sent in s if any(w in sent.lower() for w in target_words)][:6]
    if not facts:
        facts = [f"keywords:{','.join(_kw(text))}"] if text.strip() else []
    evidence_count = len(facts) + len(actions) + len(target_relevant)
    conf = min(0.99, round(0.45 + 0.45 * (evidence_count / max(1, len(s) + 1)), 2))
    return CompressedMessage(
        intent=s[0] if s else "",
        facts=facts,
        action_items=actions,
        blockers=blockers,
        target_relevant_facts=target_relevant,
        confidence=conf,
        strategy="heuristic",
    )


def transform_impl(payload: TransformRequest, tenant: str = "public") -> Dict[str, Any]:
    text = redact_sensitive(payload.message, payload.redaction_level)
    c = compress_heuristic(text, payload.target)
    if c.confidence < payload.min_confidence:
        c.facts = list(dict.fromkeys(c.facts + _sentences(text)[:2]))[:6]
        c.fallback_used = True
        c.confidence = min(0.99, round(c.confidence + 0.15, 2))
    before = token_count(text)
    after = token_count(json.dumps(asdict(c), ensure_ascii=False))
    ratio = round(max(0, before - after) / max(1, before), 4)
    payload_out = {
        "version": API_VERSION,
        "tenant": tenant,
        "target": payload.target,
        "compressed": asdict(c),
        "metrics": {"tokens_before": before, "tokens_after": after, "saving_ratio": ratio},
    }
    payload_out["audit_packet"] = make_audit_packet(payload_out).to_dict()
    return payload_out


if FastAPI is not None:
    app = FastAPI(title="Agentic Firewall Gateway", version=API_VERSION)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": API_VERSION}

    @app.post("/transform")
    def transform(req: TransformRequest, request: Request, x_request_id: Optional[str] = Header(default=None)):
        out = transform_impl(req, "public")
        out["request_id"] = x_request_id or str(uuid.uuid4())
        return out

    class FirewallRequest(BaseModel):
        agents: List[str]
        edges: List[Tuple[str, str, float]]
        residual_conflict_count: int = 0
        high_stakes: bool = False
        threshold: float = 1.0

    @app.post("/firewall/evaluate")
    def firewall_eval(req: FirewallRequest):
        return evaluate_firewall(
            req.agents,
            req.edges,
            residual_conflict_count=req.residual_conflict_count,
            high_stakes=req.high_stakes,
            threshold=req.threshold,
        ).to_dict()
else:
    app = None
