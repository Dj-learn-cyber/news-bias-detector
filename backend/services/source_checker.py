import json
import os
from typing import Optional

_DB: Optional[dict] = None


def _load_db() -> dict:
    global _DB
    if _DB is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "sources.json")
        with open(path, encoding="utf-8") as f:
            _DB = json.load(f)
    return _DB


def check_source_credibility(domain: Optional[str]) -> dict:
    if not domain:
        return _unknown()

    db = _load_db()
    entry = db.get(domain)

    # Try stripping one subdomain level (e.g. "news.bbc.co.uk" → "bbc.co.uk")
    if not entry and "." in domain:
        stripped = domain.split(".", 1)[1]
        entry = db.get(stripped)

    if not entry:
        return {**_unknown(), "outlet": domain}

    return {
        "outlet": entry["name"],
        "score": entry["credibility_score"],
        "bias_label": entry["bias"],
        "factual_reporting": entry["factual_reporting"],
        "found": True,
    }


def _unknown() -> dict:
    return {
        "outlet": None,
        "score": None,
        "bias_label": None,
        "factual_reporting": None,
        "found": False,
    }
