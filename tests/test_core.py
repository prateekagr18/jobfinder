"""Offline tests: title tracks, resume inference, ATS/callback scoring, dedupe, sources."""

import json
from datetime import date

from jobfinder.matching import classify_track, dedupe, location_ok
from jobfinder.resume import infer_years
from jobfinder.scoring import (experience_fit, freshness, jd_keyword_weights, required_years,
                               score_job, title_alignment)
from jobfinder.skills import vocabulary
from jobfinder.sources.base import parse_iso
from jobfinder.sources.boards import GreenhouseSource, LeverSource
from jobfinder.sources.file import FileSource
from jobfinder.text import contains, strip_html
from conftest import make_job


def test_tracks(settings):
    """EM and senior IC titles classify; pre-sales, junior and director do not."""
    assert classify_track("Engineering Manager, Payments", settings) == "manager"
    assert classify_track("Manager, Software Development Engineering", settings) == "manager"
    assert classify_track("Senior Software Engineer", settings) == "senior_ic"
    assert classify_track("Staff Backend Engineer", settings) == "senior_ic"
    assert classify_track("Senior Solutions Engineer", settings) is None
    assert classify_track("Director of Engineering", settings) is None
    assert classify_track("Software Engineer Intern", settings) is None


def test_keyword_boundaries():
    """java must not match javascript; c++ and k8s forms match."""
    assert contains("we use javascript", r"java") == 0
    assert contains("we use java.", r"java") == 1
    assert contains("c++ and k8s", r"c\+\+") == 1


def test_years_inference():
    """Span of date ranges, 'Present' = today; overlap not double counted."""
    t = "Nov 2013 - Present\nAug 2010 – Nov 2013"
    assert infer_years(t, date(2026, 10, 18)) == 16


def test_required_years():
    """Largest N+ years figure is the bar."""
    assert required_years("3+ years Java and 8+ years engineering experience") == 8
    assert required_years("no numbers here") is None


def test_preferred_section_weighs_less():
    """Keyword only under 'nice to have' counts half."""
    w = jd_keyword_weights("Requires Java.\nNice to have: Kafka", vocabulary(), 0.5)
    assert w["Java"] == 1.0 and w["Kafka"] == 0.5


def test_fit_curves():
    """Experience and freshness behave monotonically."""
    assert experience_fit(16, 8) == 1.0 and experience_fit(4, 8) == 0.2 and experience_fit(None, 8) == 0.7
    assert freshness(1) > freshness(10) > freshness(40) and freshness(None) == 0.5


def test_title_alignment():
    """Team suffix ignored; role words checked against resume."""
    assert title_alignment("Engineering Manager, Payments", "engineering manager at x") == 1.0


def test_matching_job_outscores_mismatch(settings, profile):
    """A JD built from resume terms beats an unrelated stack, and fresh beats stale."""
    v = vocabulary()
    good = make_job(desc="Lead engineers. Java, Spring, microservices, hiring, mentoring, roadmap. 8+ years.")
    bad = make_job(desc="Rust, Kubernetes, Terraform, GCP, Kafka, Go services.", cid="2")
    stale = make_job(desc=good.description, days_old=40, cid="3")
    g, b, s = (score_job(j, "manager", profile, v, settings) for j in (good, bad, stale))
    assert g.ats > b.ats and g.callback > b.callback and g.callback > s.callback
    assert "Kubernetes" in b.missing_keywords


def test_location_and_dedupe(settings):
    """Remote passes; same role twice collapses."""
    settings.locations = ["california"]
    assert location_ok(make_job(loc="Austin, TX", remote=True), settings)
    assert not location_ok(make_job(loc="Austin, TX"), settings)
    assert len(dedupe([make_job(cid="1"), make_job(cid="2")])) == 1


def test_strip_html_double_escaped():
    """Greenhouse content arrives double-escaped."""
    assert "Hello" in strip_html("&lt;p&gt;Hello&lt;/p&gt;")


def test_greenhouse_and_lever_mapping():
    """Board JSON maps onto Job fields."""
    class H:
        def get_json(self, url, params=None):
            if "greenhouse" in url:
                return {"jobs": [{"id": 5, "title": "Engineering Manager", "location": {"name": "Remote - US"},
                                  "absolute_url": "u", "content": "&lt;p&gt;Java&lt;/p&gt;",
                                  "first_published": "2026-10-10T00:00:00Z"}]}
            return [{"id": "a", "text": "Senior Engineer", "categories": {"location": "SF"},
                     "hostedUrl": "u2", "descriptionPlain": "Go", "createdAt": 1760000000000}]
    g = GreenhouseSource("acme", H()).fetch()[0]
    assert g.remote and g.description == "Java" and g.posted_at.year == 2026
    lv = LeverSource("acme", H()).fetch()[0]
    assert lv.title == "Senior Engineer" and lv.posted_at is not None
    assert parse_iso("bad") is None


def test_file_source(tmp_path):
    """Connector-sourced JSON loads; bad rows are skipped."""
    p = tmp_path / "j.json"
    p.write_text(json.dumps([{"title": "Engineering Manager", "company": "X", "url": "http://a",
                              "description": "<b>Java</b>"}, {"title": "no url"}]))
    jobs = FileSource(str(p)).fetch()
    assert len(jobs) == 1 and jobs[0].description == "Java"
    assert FileSource(str(tmp_path / "missing.json")).fetch() == []
