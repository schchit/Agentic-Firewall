"""JEP-style audit packets for Agentic Firewall decisions.

This is intentionally dependency-light: canonical JSON + SHA-256 + optional HMAC.
It is not a replacement for an Ed25519 JEP SDK, but gives upload-ready audit records.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def hmac_sha256_hex(obj: Any, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), canonical_json(obj).encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class AuditPacket:
    packet_type: str
    packet_id: str
    created_at_ms: int
    payload_hash: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    signature_alg: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def make_audit_packet(payload: Dict[str, Any], packet_type: str = "agentic_firewall.decision", secret: str | None = None) -> AuditPacket:
    base_payload = dict(payload)
    ph = sha256_hex(base_payload)
    sig = hmac_sha256_hex({"payload_hash": ph, "payload": base_payload}, secret) if secret else None
    return AuditPacket(
        packet_type=packet_type,
        packet_id=str(uuid.uuid4()),
        created_at_ms=int(time.time() * 1000),
        payload_hash=ph,
        payload=base_payload,
        signature=sig,
        signature_alg="HMAC-SHA256" if sig else None,
    )
