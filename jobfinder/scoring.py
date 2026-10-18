"""ATS match score and recruiter-callback likelihood.

**ATS score (0-100)** approximates what keyword-matching ATSs (Workday, Greenhouse,
Taleo, iCIMS…) and recruiter searches do: which of the JD's recognized keywords
appear in your resume. Terms repeated in the JD weigh more (they're what the
recruiter will search for); terms only under "nice to have" weigh less. Blended
with job-title alignment, because recruiters filter on title first.

**Callback likelihood (0-100)** is a heuristic — not a probability — combining the
factors that most move recruiter response rates:

- ATS match (does the resume survive the filter and the 6-second skim)
- Experience fit (inside the JD's years band; under-qualified is worse than over)
- Freshness (most callbacks go to applicants in the first ~72h of a posting)
- Track fit (EM roles need visible people-management evidence)
- Location fit (local/remote-eligible candidates get screened first)

Each component is 0-1 and kept in ``Score.components`` so the report explains ranks.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Optional, Tuple

from .config import Settings
from .matching import age_days, location_ok
from .models import Job, Score
from .resume import ResumeProfile
from .skills import find_keywords
from .text import contains, normalize, split_preferred

_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:-|–|to)?\s*(?:\d{1,2}\s*)?\+?\s*years", re.IGNORECASE)
_TITLE_STOP = {"of", "the", "and", "a", "an", "i", "ii", "iii", "iv", "-", "&", "remote", "us", "usa"}


def jd_keyword_weights(description: str, vocab: Dict[str, str], preferred_weight: float) -> Dict[str, float]:
    """Weight each vocabulary term found in the JD.

    weight = repeat factor (1 + 0.5 per extra mention, capped at 2) × 1 for core
    terms or ``preferred_weight`` for terms that appear only in the nice-to-have
    section.
    """
    core, preferred = split_preferred(description)
    core_hits = find_keywords(core, vocab)
    pref_hits = find_keywords(preferred, vocab)
    weights = {}
    for name in set(core_hits) | set(pref_hits):
        count = core_hits.get(name, 0) + pref_hits.get(name, 0)
        repeat = min(1 + 0.5 * (count - 1), 2.0)
        weights[name] = repeat * (1.0 if name in core_hits else preferred_weight)
    return weights


def required_years(description: str) -> Optional[int]:
    """Largest "N+ years" figure in the JD (the overall bar; smaller ones are sub-skills)."""
    vals = [int(n) for n in _YEARS_RE.findall(description) if 0 < int(n) <= 25]
    return max(vals) if vals else None


def title_alignment(title: str, resume_text: str) -> float:
    """Fraction of meaningful job-title words that appear in the resume.

    Text after a comma/dash/paren is the team name ("…, Payments") and is ignored
    — recruiters match on the role, not the team. Exception: "Manager, Software
    Engineering" style titles, where the part before the comma is a single word.
    """
    def words_of(text: str) -> list:
        """Lower-cased title words minus filler/level noise."""
        return [w for w in re.findall(r"[a-z+#.]+", text.lower()) if w not in _TITLE_STOP]

    words = words_of(re.split(r"[,(\-–|/]", title)[0])
    if len(words) <= 1:
        words = words_of(re.sub(r"\(.*?\)", " ", title))
    if not words:
        return 0.0
    found = sum(1 for w in words if contains(resume_text, re.escape(w)))
    return found / len(words)


def ats_score(job: Job, profile: ResumeProfile, vocab: Dict[str, str], s: Settings) -> Tuple[float, list, list]:
    """Return (score 0-100, matched keywords, missing keywords by importance)."""
    weights = jd_keyword_weights(job.description, vocab, s.preferred_keyword_weight)
    if weights:
        total = sum(weights.values())
        got = sum(w for k, w in weights.items() if k in profile.keywords)
        coverage = got / total
    else:
        coverage = 0.5  # JD has no recognizable keywords — neutral, not zero
    ordered = sorted(weights, key=lambda k: -weights[k])
    matched = [k for k in ordered if k in profile.keywords]
    missing = [k for k in ordered if k not in profile.keywords]
    t = title_alignment(job.title, profile.text)
    score = 100 * ((1 - s.ats_title_weight) * coverage + s.ats_title_weight * t)
    return round(score, 1), matched, missing


def experience_fit(have: Optional[int], need: Optional[int]) -> float:
    """1.0 inside [need, need+10]; under-qualified falls fast; far over-qualified dips mildly."""
    if have is None or need is None:
        return 0.7
    gap = have - need
    if gap < -2:
        return 0.2
    if gap < 0:
        return 0.6 if gap == -1 else 0.4
    if gap <= 10:
        return 1.0
    return 0.75


def freshness(age: Optional[float]) -> float:
    """Step-down by posting age; unknown age is treated as middling."""
    if age is None:
        return 0.5
    for limit, value in ((3, 1.0), (7, 0.8), (14, 0.55), (30, 0.3)):
        if age <= limit:
            return value
    return 0.1


def track_fit(track: str, profile: ResumeProfile) -> float:
    """EM roles need people-management evidence; senior IC roles need ~5+ years."""
    if track == "manager":
        return 1.0 if profile.has_management else 0.3
    years = profile.years_experience or 0
    return 1.0 if years >= 5 else 0.5


def score_job(
    job: Job, track: str, profile: ResumeProfile, vocab: Dict[str, str], s: Settings,
    now: Optional[datetime] = None,
) -> Score:
    """Compute the full ``Score`` for one already-filtered job."""
    ats, matched, missing = ats_score(job, profile, vocab, s)
    need = required_years(job.description)
    age = age_days(job, now)
    comps = {
        "ats": ats / 100,
        "experience": experience_fit(profile.years_experience, need),
        "freshness": freshness(age),
        "track": track_fit(track, profile),
        "location": 1.0 if location_ok(job, s) else 0.3,
    }
    weights = {
        "ats": s.weight_ats, "experience": s.weight_experience, "freshness": s.weight_freshness,
        "track": s.weight_track, "location": s.weight_location,
    }
    wsum = sum(weights.values()) or 1.0
    callback = 100 * sum(comps[k] * weights[k] for k in comps) / wsum

    notes = []
    if age is not None and age <= 3:
        notes.append("Posted in the last 3 days — apply today.")
    if comps["experience"] < 1 and need and profile.years_experience is not None:
        if profile.years_experience < need:
            notes.append(f"Asks {need}+ yrs; you show {profile.years_experience}.")
        else:
            notes.append(f"Asks {need}+ yrs; you may read as over-qualified — lead with recent scope.")
    if track == "manager" and not profile.has_management:
        notes.append("EM role: add explicit people-management bullets (team size, hires, reviews).")
    return Score(
        track=track, ats=ats, callback=round(callback, 1), matched_keywords=matched,
        missing_keywords=missing, required_years=need,
        components={k: round(v, 2) for k, v in comps.items()}, notes=notes,
    )
