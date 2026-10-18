"""End-to-end run: fetch → role/location/freshness filter → score → rank → report.

Flow: board sources (one request per company, throttled) plus an optional jobs
file → de-dupe (boards first, so the direct-apply link beats an aggregator
re-post) → keep target-role titles → drop stale/wrong-location → score against the
resume → apply thresholds → rank by callback likelihood (ATS as tie-break) →
write Markdown + CSV + digest and update the seen-jobs state.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .config import Settings
from .matching import age_days, classify_track, dedupe, location_ok
from .models import Job, ScoredJob
from .report import digest, write_csv, write_markdown
from .resume import load_resume, profile_from_text
from .scoring import score_job
from .skills import vocabulary
from .sources import BOARD_SOURCES, FileSource
from .sources.http import HttpClient
from .state import load_seen, mark, save_seen

log = logging.getLogger(__name__)


def collect(settings: Settings, jobs_file: Optional[str] = None, http: Optional[HttpClient] = None) -> List[Job]:
    """Fetch from every configured board, then the jobs file (boards first for dedupe)."""
    http = http or HttpClient(
        timeout=settings.request_timeout, delay=settings.request_delay,
        max_retries=settings.max_retries, backoff=settings.retry_backoff,
    )
    jobs: List[Job] = []
    for kind, tokens in settings.companies.items():
        cls = BOARD_SOURCES.get(kind)
        if cls is None:
            log.warning("Unknown board type %r in config; skipping", kind)
            continue
        for token in tokens:
            found = cls(token, http).fetch()
            log.info("%s/%s: %d postings", kind, token, len(found))
            jobs.extend(found)
    if jobs_file:
        jobs.extend(FileSource(jobs_file).fetch())
    return dedupe(jobs)


def rank(jobs: List[Job], settings: Settings, now: Optional[datetime] = None) -> Tuple[List[ScoredJob], dict]:
    """Filter and score ``jobs``; return (ranked results, funnel stats)."""
    now = now or datetime.now(timezone.utc)
    vocab = vocabulary(settings.extra_keywords)
    profile = profile_from_text(
        load_resume(settings.resume_path), vocab,
        settings.years_experience, settings.has_management_experience,
    )
    stats = {"fetched": len(jobs), "role_match": 0}
    scored: List[ScoredJob] = []
    for job in jobs:
        track = classify_track(job.title, settings)
        if not track:
            continue
        stats["role_match"] += 1
        age = age_days(job, now)
        if age is not None and age > settings.max_age_days:
            continue
        if settings.require_location_match and not location_ok(job, settings):
            continue
        sc = score_job(job, track, profile, vocab, settings, now)
        if sc.ats >= settings.min_ats and sc.callback >= settings.min_callback:
            scored.append(ScoredJob(job, sc))
    scored.sort(key=lambda r: (-r.score.callback, -r.score.ats))
    return scored[: settings.top_n], stats


def run(settings: Settings, jobs_file: Optional[str] = None, today: Optional[date] = None) -> List[ScoredJob]:
    """Full run with output files; returns the ranked results."""
    today = today or date.today()
    out = Path(settings.output_dir)
    results, stats = rank(collect(settings, jobs_file), settings)
    seen_path = out / "seen.json"
    seen = load_seen(seen_path)
    for r in results:
        r.is_new = mark(seen, r.job.uid, today)
    write_markdown(results, out / f"matches-{today.isoformat()}.md", today, stats)
    write_csv(results, out / f"matches-{today.isoformat()}.csv")
    (out / "digest.txt").write_text(digest(results), encoding="utf-8")
    save_seen(seen_path, seen)
    return results
