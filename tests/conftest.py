"""Shared test helpers: synthetic jobs and a resume profile (all offline)."""

from datetime import datetime, timedelta, timezone

import pytest

from jobfinder.config import Settings
from jobfinder.models import Job
from jobfinder.resume import profile_from_text
from jobfinder.skills import vocabulary

RESUME = """Engineering Manager. Nov 2013 - Present. Led a team of 8 engineers, hired 6,
performance reviews, mentoring. Java, Python, Spring, microservices, distributed systems,
REST APIs, SQL, roadmap, stakeholders, Agile Scrum."""


def make_job(title="Engineering Manager, Platform", desc="", days_old=1, remote=False, loc="San Jose, CA", cid="1"):
    """Build a Job posted ``days_old`` days ago."""
    return Job("greenhouse", "acme", cid, title, loc, f"https://x/{cid}", desc,
               datetime.now(timezone.utc) - timedelta(days=days_old), remote)


@pytest.fixture
def settings():
    """Default settings with resume path unused (profiles are built directly)."""
    return Settings()


@pytest.fixture
def profile():
    """Profile of the sample resume above."""
    return profile_from_text(RESUME, vocabulary())
