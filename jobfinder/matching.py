"""Hard filters applied before scoring: role track, location, freshness, de-duplication.

Cheap checks run first so we only score (and report) jobs you'd actually apply to.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from .config import Settings
from .models import Job


def _any(patterns: Iterable[str], text: str) -> bool:
    """True if any regex in ``patterns`` matches ``text`` (case-insensitive)."""
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_track(title: str, s: Settings) -> Optional[str]:
    """``"manager"`` / ``"senior_ic"`` / ``None`` for a posting title.

    Exclusions win (e.g. "Senior Solutions Engineer" is a pre-sales role, not a
    senior SWE). Manager is checked before IC so "Engineering Manager, Staff" lands
    on the manager track.
    """
    if _any(s.exclude_titles, title):
        return None
    if _any(s.manager_titles, title):
        return "manager"
    if _any(s.ic_titles, title):
        return "senior_ic"
    return None


def location_ok(job: Job, s: Settings) -> bool:
    """True if remote (and ``remote_ok``) or the location contains a preferred place.

    An empty ``locations`` list means "anywhere".
    """
    if job.remote and s.remote_ok:
        return True
    if not s.locations:
        return True
    loc = job.location.lower()
    return any(place.lower() in loc for place in s.locations)


def age_days(job: Job, now: Optional[datetime] = None) -> Optional[float]:
    """Days since the posting went live, or ``None`` when the board doesn't say."""
    if not job.posted_at:
        return None
    now = now or datetime.now(timezone.utc)
    return max(0.0, (now - job.posted_at).total_seconds() / 86400)


def dedupe(jobs: List[Job]) -> List[Job]:
    """Drop repeats by uid and by (company, title, location) — the same role is often
    posted per-location or re-posted on an aggregator. First occurrence wins, so
    pass board jobs before aggregator jobs to keep the direct-apply link.
    """
    seen_uid, seen_key, out = set(), set(), []
    for j in jobs:
        key = (j.company.lower().strip(), j.title.lower().strip(), j.location.lower().strip())
        if j.uid in seen_uid or (j.company and key in seen_key):
            continue
        seen_uid.add(j.uid)
        seen_key.add(key)
        out.append(j)
    return out
