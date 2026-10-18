"""Seen-jobs state so each report can flag postings that are NEW since the last run.

Stored as ``{uid: first_seen_iso_date}`` JSON. In the cloud routine the container
is fresh every night, so state lives only as long as the output directory does;
when it's missing every job is "new", which is harmless (the freshness score
still uses the board's real posting date).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict


def load_seen(path: Path) -> Dict[str, str]:
    """Load the seen map, or ``{}`` if absent/corrupt."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save_seen(path: Path, seen: Dict[str, str]) -> None:
    """Persist the seen map, creating the directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, indent=1, sort_keys=True))


def mark(seen: Dict[str, str], uid: str, today: date) -> bool:
    """Record ``uid``; return True if this is its first sighting."""
    if uid in seen:
        return False
    seen[uid] = today.isoformat()
    return True
