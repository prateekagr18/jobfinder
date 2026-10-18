# jobfinder

A daily scanner that finds **Engineering Manager** and **Senior Engineer** roles,
scores each against your resume, and ranks them by **ATS match** and **likelihood of
a recruiter callback**. Personal-use tool.

## How it works

```
company ATS boards (Greenhouse/Lever/Ashby) ┐
Indeed / Dice results (via Claude connectors)┴→ dedupe → role filter → freshness/location
  → score (ATS keywords + title, callback heuristic) → ranked report (MD + CSV + digest)
```

- **ATS score** — share of the JD's recognized keywords that appear in your resume
  (repeated and "required" terms weigh more, "nice to have" less) blended with title match.
- **Callback score** — heuristic blend of ATS match, experience fit, **posting freshness**
  (early applicants get the calls), track fit (EM needs visible people-management), location.
  It ranks; it is not a probability.
- **Missing keywords** per job — add to your resume *only if true*.

## Use

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp config.example.yaml config.yaml          # edit companies / locations
# put your resume in resume.md (gitignored)
.venv/bin/jobfinder resume                  # see what the scorer extracted
.venv/bin/jobfinder run [--jobs-file jobs.json]
.venv/bin/pytest -q
```

Output lands in `output/`: `matches-<date>.md`, `.csv`, `digest.txt`, `seen.json`.
Every threshold is in `jobfinder/config.py` and overridable in `config.yaml`.

## Daily in the cloud
See `docs/ROUTINE.md` (1:00am US Pacific scheduled Claude Code routine).

## Caveats
- Board APIs are public and unauthenticated; requests are throttled (1/s) with
  retry/backoff and a per-host circuit breaker.
- The keyword vocabulary (`jobfinder/skills.py`) only recognizes listed terms; extend
  it via `extra_keywords`.
- Not a guarantee of interviews. Never claim skills you don't have.
