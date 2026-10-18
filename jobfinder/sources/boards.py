"""Greenhouse, Lever and Ashby public job-board sources.

Each takes a board token (the company slug in its careers URL, e.g.
``boards.greenhouse.io/<token>``) and maps the board's JSON to ``Job``.
One request per company returns every open role with full descriptions, so a
40-company scan is ~40 requests — well within polite limits.
"""

from __future__ import annotations

import logging
from typing import List

from ..models import Job
from ..text import strip_html
from .base import JobSource, from_epoch_ms, looks_remote, parse_iso
from .http import HttpClient

log = logging.getLogger(__name__)


class GreenhouseSource(JobSource):
    """``boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true``."""

    name = "greenhouse"
    URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

    def __init__(self, token: str, http: HttpClient):
        """Bind to one company's board."""
        self.token, self.http = token, http

    def fetch(self) -> List[Job]:
        """Map ``jobs[]``; prefers ``first_published`` over ``updated_at`` (edits bump the latter)."""
        data = self.http.get_json(self.URL.format(token=self.token), params={"content": "true"})
        jobs = []
        for j in (data or {}).get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            jobs.append(Job(
                source=self.name, company=self.token, job_id=str(j.get("id")),
                title=j.get("title", ""), location=loc, url=j.get("absolute_url", ""),
                description=strip_html(j.get("content", "")),
                posted_at=parse_iso(j.get("first_published") or j.get("updated_at")),
                remote=looks_remote(loc),
            ))
        return jobs


class LeverSource(JobSource):
    """``api.lever.co/v0/postings/<token>?mode=json``."""

    name = "lever"
    URL = "https://api.lever.co/v0/postings/{token}"

    def __init__(self, token: str, http: HttpClient):
        """Bind to one company's board."""
        self.token, self.http = token, http

    def fetch(self) -> List[Job]:
        """Map the postings list; description = intro + every ``lists[]`` section + closing."""
        data = self.http.get_json(self.URL.format(token=self.token), params={"mode": "json"})
        jobs = []
        for j in data if isinstance(data, list) else []:
            cats = j.get("categories") or {}
            loc = cats.get("location", "") or ""
            sections = [
                f"{lst.get('text', '')}\n{strip_html(lst.get('content', ''))}"
                for lst in j.get("lists", []) or []
            ]
            desc = "\n".join(
                [j.get("descriptionPlain") or strip_html(j.get("description", ""))]
                + sections + [j.get("additionalPlain", "") or ""]
            )
            jobs.append(Job(
                source=self.name, company=self.token, job_id=str(j.get("id")),
                title=j.get("text", ""), location=loc, url=j.get("hostedUrl", ""),
                description=desc.strip(), posted_at=from_epoch_ms(j.get("createdAt")),
                remote=looks_remote(loc, j.get("workplaceType")),
            ))
        return jobs


class AshbySource(JobSource):
    """``api.ashbyhq.com/posting-api/job-board/<token>``."""

    name = "ashby"
    URL = "https://api.ashbyhq.com/posting-api/job-board/{token}"

    def __init__(self, token: str, http: HttpClient):
        """Bind to one company's board."""
        self.token, self.http = token, http

    def fetch(self) -> List[Job]:
        """Map ``jobs[]``, skipping unlisted postings."""
        data = self.http.get_json(self.URL.format(token=self.token))
        jobs = []
        for j in (data or {}).get("jobs", []):
            if j.get("isListed") is False:
                continue
            loc = j.get("location", "") or ""
            jobs.append(Job(
                source=self.name, company=self.token, job_id=str(j.get("id")),
                title=j.get("title", ""), location=loc,
                url=j.get("jobUrl") or j.get("applyUrl", ""),
                description=j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", "")),
                posted_at=parse_iso(j.get("publishedAt")),
                remote=bool(j.get("isRemote")) or looks_remote(loc, j.get("workplaceType")),
            ))
        return jobs
