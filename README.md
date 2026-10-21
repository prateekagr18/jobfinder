# jobfinder

A daily scanner that finds **Engineering Manager** and **Senior Engineer** roles, scores each against
your resume, and ranks them by **ATS match** and **likelihood of a recruiter callback**.
Personal-use tool; not a guarantee of interviews.

```
company career pages (Greenhouse / Lever / Ashby, free APIs) ┐
jobs an AI tool or you gather (Indeed, Dice, LinkedIn…)      ┴→ dedupe → role filter → freshness/location
   → score (ATS keywords + title, callback heuristic) → ranked report (Markdown + CSV + short digest)
```

**The scoring engine is plain Python. It makes no AI/LLM calls and needs no API keys.** An AI tool is
optional: it is only useful for *finding* jobs on sites that have no free public API.

- **ATS score (0-100)**: share of the job description's recognized keywords that appear in your resume
  (repeated and "required" terms weigh more, "nice to have" less), blended with job-title match.
- **Callback score (0-100)**: heuristic blend of ATS match, experience fit, **posting freshness**
  (early applicants get the calls), track fit (EM roles need visible people-management), and location.
  It ranks jobs; it is not a probability.
- **Missing keywords** per job: add them to your resume *only if they are true*.

---

## Option A: run it yourself on a laptop (no AI needed)

Requirements: Python 3.9+, internet access.

```bash
git clone https://github.com/prateekagr18/jobfinder && cd jobfinder
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"            # add ".[pdf,dev]" if your resume is a PDF

cp config.example.yaml config.yaml           # then edit: companies, locations, thresholds
cp resume.example.md resume.md 2>/dev/null || true   # or just create resume.md with your resume text

.venv/bin/jobfinder resume                   # sanity check: years, management flag, keywords it found
.venv/bin/jobfinder run                      # fetch + score + write report
```

Output goes to `output/`: `matches-<date>.md` (ranked table + per-job tips), `matches-<date>.csv`,
`digest.txt` (short summary), `seen.json` (so the next run can mark postings NEW).

**What it scans in this mode:** the company boards you list under `companies:` in `config.yaml`.
A board token is the slug in the company's careers URL (`boards.greenhouse.io/<token>`,
`jobs.lever.co/<token>`, `jobs.ashbyhq.com/<token>`). Large employers like Workday or Google use
their own systems and are not covered by these three.

**Add jobs from other sites by hand or script:** write them to a JSON file (format below) and run
`.venv/bin/jobfinder run --jobs-file my-jobs.json`. Boards and the file are scored together.

**Run it every night without a server:** use cron on a machine that is on, e.g.
`0 1 * * * cd /path/to/jobfinder && .venv/bin/jobfinder run`, or a scheduled GitHub Actions
workflow (not included yet). The seen-jobs file and your resume need to persist between runs.

### Jobs file format (`--jobs-file`)

A JSON list; see `jobs.example.json`. Required: `title`, `company`, `location`, `url`,
`description` (the **full** job description text; scoring is only as good as this text).
Optional: `source`, `job_id`, `posted_at` (ISO date, used for freshness), `remote` (true/false).

---

## Option B: run it with an AI tool (Claude, ChatGPT, Gemini, DeepSeek, Mistral, …)

The AI's job is to **gather the jobs and hand them to the scorer**. Any assistant works if it can
(1) search or browse job sites and (2) run shell commands, or at least produce a JSON file.
Copy-paste instructions for the AI are in **[docs/AI_AGENT_INSTRUCTIONS.md](docs/AI_AGENT_INSTRUCTIONS.md)**.

Pick the row that matches your tool:

| Your AI tool can… | Do this |
|---|---|
| Browse/search **and** run code (Claude Code, ChatGPT with code interpreter/agent mode, Gemini agent tools, local agents with DeepSeek/Mistral + tools) | Give it the repo plus the instructions file. It installs the package, finds jobs, writes `output/jobs.json`, runs `jobfinder run --jobs-file output/jobs.json`, and reports `output/matches-<date>.md`. |
| Browse/search but **cannot** run code | Ask it to produce the jobs JSON (format above, with full descriptions). Save it on your laptop and run Option A with `--jobs-file`. |
| Neither (plain chat, no tools) | Paste your resume and the job descriptions into the chat with the **manual scoring prompt** in `docs/AI_AGENT_INSTRUCTIONS.md`. It follows the same rubric but the numbers are the model's own judgment, so they are less consistent than the code's. |

Notes for AI-driven runs:
- **Real postings only.** The instructions tell the AI never to invent jobs or descriptions and to
  say plainly when a source was unavailable.
- **Scheduling is separate from the AI.** To run it nightly without your laptop you need a scheduler:
  Claude Code scheduled routines, a GitHub Actions cron, or any cloud scheduler that can run a
  session/script. See `docs/ROUTINE.md` for the Claude Code routine used by the author.
- **Network limits.** Some sandboxes block `boards-api.greenhouse.io`, `api.lever.co` and
  `api.ashbyhq.com`. Allow those domains or the board sources return nothing (the run still works from
  `--jobs-file`).
- **Privacy.** Your resume contains personal details. Keep `resume.md`, `config.yaml` and `output/`
  out of public repos (they are gitignored); if a cloud run needs the resume, use a private repo or a
  secret store.

---

## Configuration

Every tunable lives in `jobfinder/config.py` (`Settings`) and is overridable in `config.yaml`: target
title patterns, locations, `max_age_days`, minimum ATS/callback scores, scoring weights, throttling.
Unknown keys in `config.yaml` are rejected. The keyword vocabulary is in `jobfinder/skills.py`; extend it
for your niche with `extra_keywords` (`{"Canonical name": "regex"}`).

## Tests

```bash
.venv/bin/pytest -q      # offline, synthetic data
```

## Caveats

- Scoring only "sees" keywords in the vocabulary. A job full of terms the vocabulary lacks can score
  too high on ATS; extend `skills.py` and sanity-check the top results by reading the job.
- Board APIs are public and unauthenticated; requests are throttled (1/s) with retry/backoff and a
  per-host circuit breaker.
- Posting dates come from the source; "seen" tracking only works if `output/seen.json` persists.
