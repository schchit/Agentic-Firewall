from __future__ import annotations
import json, os, re
from typing import Dict, Any


def load_keys(path: str = "security/api_keys.json") -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_scope(record: Dict[str, Any], scope: str) -> bool:
    return scope in record.get("scopes", []) or "admin" in record.get("scopes", [])


def redact_sensitive(text: str, level: str = "standard") -> str:
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    if level == "strict":
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_ID]", text)
    return text
