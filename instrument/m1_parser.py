"""Frozen historical response parser; no model client or I/O on import."""
import json
import re

VOCAB = ['propose_new', 'improve', 'apply', 'hybrid', 'theory', 'benchmark', 'review', 'other']

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
    """规范化解析结果；值不合法则抛 ValueError 记为失败。"""
    if not isinstance(parsed, dict):
        raise ValueError("not a dict")
    prim = parsed.get("contribution_primary")
    sec = parsed.get("contribution_secondary")
    if prim not in VOCAB:
        raise ValueError(f"bad primary: {prim!r}")
    if sec is not None and sec not in VOCAB:
        sec = None
    def _ents(key):
        out = []
        for e in parsed.get(key) or []:
            if isinstance(e, dict) and e.get("norm"):
                out.append({"raw": str(e.get("raw", "")), "norm": str(e["norm"]).strip().lower()})
        return out
    return {
        "contribution_primary": prim,
        "contribution_secondary": sec,
        "algorithms": _ents("algorithms"),
        "problems": _ents("problems"),
        "llm_related": bool(parsed.get("llm_related")),
    }
