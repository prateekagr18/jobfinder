# Nightly cloud routine (1:00am US Pacific) — Claude Code version

This is the Claude Code way to schedule it. For other AI tools or plain cron/GitHub Actions see the README
(Option A/B) and `docs/AI_AGENT_INSTRUCTIONS.md`; the scoring engine is the same.

The routine is a scheduled Claude Code cloud session. Each night it starts from a
fresh clone of this repo, so nothing depends on your laptop.

Cron (UTC fields in a fixed-offset form don't track DST, so use the TZ prefix):
`CRON_TZ=America/Los_Angeles 0 1 * * *` — jitter the minute if you like (e.g. `47 0`).

## Prompt the routine runs

1. `pip install -e .` in the repo (use the venv if present).
2. Search **Indeed** and **Dice** with the connectors, for each of:
   "Engineering Manager", "Senior Software Engineer", location San Francisco Bay Area
   and "remote", posted in the last 3 days (Dice: `posted_date=THREE`, `sort=datePosted`;
   Indeed: fetch job details for each plausible hit to get the full description).
3. Write every result to `output/jobs.json` as a list of
   `{title, company, location, url, description, source, posted_at, remote}`.
4. `jobfinder run --jobs-file output/jobs.json` (company ATS boards in `config.yaml`
   are scanned too, if the environment allows `boards-api.greenhouse.io`,
   `api.lever.co`, `api.ashbyhq.com`).
5. Send a push notification with `output/digest.txt` (top matches), and mention the
   report path `output/matches-<date>.md`.
