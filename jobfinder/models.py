"""Plain data models shared by sources, scoring and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Job:
    """One job posting, normalized from whichever ATS board it came from.

    ``posted_at`` is timezone-aware UTC when the board exposes it, else ``None``
    (freshness then scores as "unknown" rather than "stale").
    """

    source: str
    company: str
    job_id: str
    title: str
    location: str
    url: str
    description: str
    posted_at: Optional[datetime] = None
    remote: bool = False

    @property
    def uid(self) -> str:
        """Stable identity across runs, used to flag postings as NEW."""
        return f"{self.source}:{self.company}:{self.job_id}"


@dataclass
class Score:
    """Scoring breakdown for one job — everything the report needs to explain a rank.

    ``ats`` and ``callback`` are 0-100. ``components`` holds the 0-1 inputs to the
    callback score so the report can say *why* a job ranked where it did.
    """

    track: str
    ats: float
    callback: float
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    required_years: Optional[int] = None
    components: dict = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class ScoredJob:
    """A job paired with its score and whether this is the first run that saw it."""

    job: Job
    score: Score
    is_new: bool = True
