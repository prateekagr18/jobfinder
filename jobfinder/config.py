"""Settings: every tunable lives here, overridable from ``config.yaml``.

``load_settings`` reads the YAML, rejects unknown keys (a typo'd threshold that's
silently ignored is worse than an error), and fills everything else with the
defaults below. Functions take ``Settings`` rather than reading globals so tests
can build one inline.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def _default_manager_titles() -> List[str]:
    """Title regexes that put a posting on the Engineering Manager track."""
    return [
        r"engineering manager",
        r"manager,? (?:of )?(?:software )?engineering",
        r"software (?:development|engineering) manager",
        r"manager,? software (?:development|engineering)",
        r"head of engineering",
    ]


def _default_ic_titles() -> List[str]:
    """Title regexes that put a posting on the senior individual-contributor track."""
    return [
        r"(?:senior|sr\.?|staff|lead) (?:\w+ ){0,3}(?:software )?(?:engineer|developer)",
        r"(?:software|backend|frontend|full[- ]?stack|platform|infrastructure) engineer,? (?:senior|staff|iii|iv)",
    ]


def _default_exclude_titles() -> List[str]:
    """Title regexes that disqualify a posting even when a track pattern matched."""
    return [
        r"intern", r"junior", r"new grad", r"associate", r"apprentice",
        r"sales engineer", r"solutions? engineer", r"support engineer",
        r"field engineer", r"customer engineer", r"forward deployed",
        r"director", r"\bvp\b", r"vice president",
    ]


@dataclass
class Settings:
    """All knobs for a run. See ``config.example.yaml`` for the commented version."""

    resume_path: str = "resume.md"
    output_dir: str = "output"

    # Which boards to scan: {"greenhouse": [...board tokens], "lever": [...], "ashby": [...]}
    companies: Dict[str, List[str]] = field(default_factory=dict)

    # Role targeting — tracks: "manager" and "senior_ic". Remove a track's
    # patterns (set to []) to stop searching it.
    manager_titles: List[str] = field(default_factory=_default_manager_titles)
    ic_titles: List[str] = field(default_factory=_default_ic_titles)
    exclude_titles: List[str] = field(default_factory=_default_exclude_titles)

    # Location: substrings matched case-insensitively against the posting location.
    locations: List[str] = field(default_factory=list)
    remote_ok: bool = True
    require_location_match: bool = False

    # Freshness: recruiters work the earliest applicants first.
    max_age_days: int = 30

    # Resume facts the parser may get wrong — set them to override inference.
    years_experience: Optional[int] = None
    has_management_experience: Optional[bool] = None

    # Extra vocabulary {canonical: regex} for your niche.
    extra_keywords: Dict[str, str] = field(default_factory=dict)

    # Filters on the final report.
    min_ats: float = 40.0
    min_callback: float = 50.0
    top_n: int = 30

    # Callback-likelihood weights (normalized at use, so they needn't sum to 1).
    weight_ats: float = 0.35
    weight_experience: float = 0.20
    weight_freshness: float = 0.20
    weight_track: float = 0.15
    weight_location: float = 0.10

    # ATS score = keyword coverage blended with job-title alignment.
    ats_title_weight: float = 0.20
    preferred_keyword_weight: float = 0.5

    # HTTP politeness — these are public endpoints; don't hammer them.
    request_timeout: float = 20.0
    request_delay: float = 1.0
    max_retries: int = 3
    retry_backoff: float = 2.0


def load_settings(path: Optional[str]) -> Settings:
    """Build ``Settings`` from a YAML file (or pure defaults when ``path`` is None/missing)."""
    if not path or not Path(path).exists():
        return Settings()
    data = yaml.safe_load(Path(path).read_text()) or {}
    known = {f.name for f in fields(Settings)}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"Unknown config keys in {path}: {sorted(unknown)}")
    return Settings(**data)
