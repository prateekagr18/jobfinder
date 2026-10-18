"""Import jobs from a JSON file — the bridge for connector-sourced postings.

The nightly Claude routine searches Indeed/Dice through its connectors and
writes what it finds here, so those jobs get the exact same filtering and
scoring as board jobs. Format: a JSON list of objects with keys
``title, company, location, url, description`` (required) and optional
``source, job_id, posted_at`` (ISO date), ``remote`` (bool).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import List

from ..models import Job
from ..text import strip_html
from .base import JobSource, looks_remote, parse_iso

log = logging.getLogger(__name__)


class FileSource(JobSource):
    """Reads a JSON list of job dicts from ``path``."""

    name = "file"

    def __init__(self, path: str):
        """Bind to the JSON file."""
        self.path = path

    def fetch(self) -> List[Job]:
        """Parse each entry; entries missing a title or url are skipped with a warning."""
        p = Path(self.path)
        if not p.exists():
            log.warning("Jobs file %s not found; skipping", self.path)
            return []
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            log.warning("Jobs file %s is not valid JSON (%s); skipping", self.path, exc)
            return []
        jobs = []
        for r in rows if isinstance(rows, list) else []:
            if not r.get("title") or not r.get("url"):
                log.warning("Skipping entry without title/url: %r", r)
                continue
            loc = r.get("location", "") or ""
            job_id = r.get("job_id") or hashlib.sha1(r["url"].encode()).hexdigest()[:12]
            jobs.append(Job(
                source=r.get("source", self.name), company=r.get("company", "") or "",
                job_id=str(job_id), title=r["title"], location=loc, url=r["url"],
                description=strip_html(r.get("description", "") or ""),
                posted_at=parse_iso(r.get("posted_at")),
                remote=bool(r.get("remote")) or looks_remote(loc),
            ))
        return jobs
