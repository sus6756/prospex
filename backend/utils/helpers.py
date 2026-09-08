import json
import re
from typing import Any, Optional


def dumps_json(value: Any) -> str:
    if value is None:
        return "[]"
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str)


def loads_json(value: Optional[str], fallback=None):
    if not value:
        return fallback if fallback is not None else []
    try:
        return json.loads(value)
    except Exception:
        return fallback if fallback is not None else []


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text or "").lower().strip()
    return "-".join(text.split())


def normalize_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/")[0].split("?")[0]
    return domain


def clamp_score(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))
