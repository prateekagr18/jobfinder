"""Render results as a Markdown report, a CSV, and a short push-notification digest."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import List

from .matching import age_days
from .models import ScoredJob

_TRACK_LABEL = {"manager": "EM", "senior_ic": "Senior IC"}


def _age_label(sj: ScoredJob) -> str:
    """Human posting age, e.g. "2d" or "?"."""
    age = age_days(sj.job)
    return "?" if age is None else f"{int(age)}d"


def write_markdown(results: List[ScoredJob], path: Path, run_date: date, stats: dict) -> None:
    """Ranked table plus a per-job card with why-it-ranked and resume-tailoring tips."""
    lines = [
        f"# Job matches — {run_date.isoformat()}",
        "",
        f"Scanned {stats.get('fetched', 0)} postings → {stats.get('role_match', 0)} target roles → "
        f"**{len(results)} recommended** ({sum(r.is_new for r in results)} new).",
        "",
        "Callback = heuristic likelihood of a recruiter call (not a probability). "
        "ATS = resume keyword/title match vs the JD.",
        "",
        "| # | Callback | ATS | Track | Role | Company | Location | Age | |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        j = r.job
        lines.append(
            f"| {i} | {r.score.callback:.0f} | {r.score.ats:.0f} | {_TRACK_LABEL.get(r.score.track, r.score.track)} "
            f"| [{j.title}]({j.url}) | {j.company} | {j.location or '—'} | {_age_label(r)} "
            f"| {'🆕' if r.is_new else ''} |"
        )
    lines.append("")
    for i, r in enumerate(results, 1):
        j, s = r.job, r.score
        lines += [
            f"## {i}. {j.title} — {j.company}",
            f"[Apply]({j.url}) · {j.location or '—'} · posted {_age_label(r)} ago · source: {j.source}",
            "",
            f"- **Callback {s.callback:.0f}** — " + ", ".join(f"{k} {v:.2f}" for k, v in s.components.items()),
            f"- **ATS {s.ats:.0f}** — matched: {', '.join(s.matched_keywords[:12]) or '—'}",
            f"- **Missing keywords** (add only if true): {', '.join(s.missing_keywords[:10]) or 'none'}",
        ]
        if s.required_years:
            lines.append(f"- Asks for {s.required_years}+ years")
        lines += [f"- {n}" for n in s.notes] + [""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(results: List[ScoredJob], path: Path) -> None:
    """One row per job — handy for a spreadsheet application tracker."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["callback", "ats", "track", "title", "company", "location", "age_days",
                    "new", "url", "missing_keywords"])
        for r in results:
            age = age_days(r.job)
            w.writerow([r.score.callback, r.score.ats, r.score.track, r.job.title, r.job.company,
                        r.job.location, "" if age is None else round(age, 1), r.is_new, r.job.url,
                        "; ".join(r.score.missing_keywords[:10])])


def digest(results: List[ScoredJob], limit: int = 5) -> str:
    """Short plain-text summary sized for a phone push notification."""
    if not results:
        return "Job scan: no new matches above your thresholds today."
    new = [r for r in results if r.is_new] or results
    head = f"Job scan: {len(results)} matches ({sum(r.is_new for r in results)} new). Top:"
    rows = [
        f"{r.score.callback:.0f}/{r.score.ats:.0f} {r.job.title} @ {r.job.company}"
        for r in new[:limit]
    ]
    return "\n".join([head] + rows)
