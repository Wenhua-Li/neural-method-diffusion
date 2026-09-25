"""Frozen historical response parser; no model client or I/O on import."""
import json
import re

LABELS = ['dl_native', 'neuroevolution', 'hybrid', 'other']

def _extract_json(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```$", "", t)
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def _validate(parsed: dict) -> dict:
    if not isinstance(parsed, dict):
        raise ValueError("not a dict")
    label = parsed.get("label")
    if label not in LABELS:
        raise ValueError(f"bad label: {label!r}")
    reason = str(parsed.get("reason", "")).strip()[:200]
    return {"label": label, "reason": reason}
