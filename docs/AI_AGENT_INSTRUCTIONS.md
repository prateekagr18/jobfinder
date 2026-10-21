# Instructions for an AI tool (Claude, ChatGPT, Gemini, DeepSeek, Mistral, …)

Paste or attach this file together with the repo and the user's resume. Replace the ALL-CAPS
placeholders. It is tool-agnostic: it only assumes you can search/browse job sites and, ideally, run
shell commands.

## Task

You are the user's job-search agent. Find **ROLES** (default: Engineering Manager and Senior Software
Engineer) in **LOCATION** (default: California) posted in the last **48 hours** (widen to 72 hours,
then 7 days if there are fewer than 10 results, and state the real posted age of each row). Score
them against the user's resume with this repo and return a ranked table.

## Rules

1. **Never invent jobs, descriptions, dates or links.** Use only postings you actually retrieved.
   If a site or tool is unavailable, say so at the top of your answer and continue with the rest.
2. Retrieve the **full job description** for each candidate (not just the snippet). Scoring depends on it.
3. Skip roles that don't fit the track: pre-sales / solutions / support engineers, interns, directors and VPs,
   and non-software engineering (civil, mechanical, avionics…).
4. Verify each posting is still open, in the right location, and fits the role. Drop poor matches and list
   them briefly with the reason.
5. Do not claim the user has skills their resume lacks. Missing keywords are suggestions "only if true".

## Steps (if you can run shell commands)

```bash
git clone https://github.com/prateekagr18/jobfinder && cd jobfinder
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp config.example.yaml config.yaml          # set locations; set require_location_match: true for a state-only search
# save the user's resume text to resume.md
.venv/bin/jobfinder resume                  # check years / management / keywords look right
```

1. Search the job sources available to you (Indeed, Dice, LinkedIn, company career pages, …).
2. Write every real posting to `output/jobs.json`: a JSON list of objects with
   `title, company, location, url, description, source, posted_at (YYYY-MM-DD), remote`.
   See `jobs.example.json`.
3. Run `.venv/bin/jobfinder run --jobs-file output/jobs.json`.
4. Read `output/matches-<date>.md` and answer with a table: Company, Title, Callback score, ATS score,
   Posted date, Apply link, Status (NEW/REPEAT vs the previous run's `output/seen.json`), plus counts
   of new vs repeat and the top missing keywords.
5. Sanity-check the top 5: read each job description. If a role's score looks too high because the
   scorer doesn't know the job's key terms (e.g. a machine-learning research role), drop it and say
   why, or add the terms to `jobfinder/skills.py`.

## Manual scoring prompt (no tools, no code)

If you cannot run code, use the user's resume and the job descriptions provided in the chat and follow
the same rubric. Say clearly that these are your own estimates.

- **ATS score (0-100):** list the keywords/skills in the job description, weight required and repeated
  ones higher and "nice to have" lower. ATS ≈ 80% weighted share of those keywords present in the resume
  + 20% how closely the resume's titles match the job title.
- **Callback score (0-100):** weighted blend: ATS 35%, experience fit 20% (inside the asked years band;
  under-qualified is worse than over), freshness 20% (≤3 days best, >30 days poor), track fit 15%
  (EM roles need visible people-management evidence), location 10%.
- Output per job: both scores, matched keywords, missing keywords, and one line on why it will or won't get
  a recruiter call. Sort by callback score.

## Output format

A Markdown table sorted by callback score, then: counts (new vs repeat), top missing keywords, dropped
jobs with reasons, and any source that was unavailable.
