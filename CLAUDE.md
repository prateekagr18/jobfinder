# CLAUDE.md

Daily job scanner (EM + Senior Engineer roles). Python 3.9+, `from __future__ import annotations`.

## Commands
`.venv/bin/pip install -e ".[dev]"` · `.venv/bin/pytest -q` · `.venv/bin/jobfinder run` · `.venv/bin/jobfinder resume`

## Layout (`jobfinder/`)
`sources/` (boards + file import + throttled `http.py`) · `matching.py` (track/location/dedupe) ·
`scoring.py` (ATS + callback) · `skills.py` (keyword vocab) · `resume.py` · `pipeline.py` · `report.py` · `config.py`.

## Conventions
- Every tunable lives in `config.py` `Settings` (overridable in `config.yaml`); no magic numbers in scoring logic beyond the documented curves.
- 100% docstring coverage; tests are offline/synthetic (`tests/conftest.py::make_job`).
- Sources never raise on network errors — log and return `[]`.
- `resume.md`, `config.yaml`, `output/` are personal and gitignored.
- When a change touches behavior, update README.md / this file / docs/ROUTINE.md.

## Two ways to run (keep both documented)
- **Local, no AI** (README Option A): `jobfinder run` over configured boards, optionally `--jobs-file`.
- **AI-assisted** (README Option B, `docs/AI_AGENT_INSTRUCTIONS.md`): any AI tool gathers real postings into a jobs JSON, then runs the same engine; Claude Code scheduling is in `docs/ROUTINE.md`.
The engine makes no LLM calls; keep it that way so any tool can drive it.

## Caveats
Callback score is a heuristic. The cloud sandbox blocks board APIs unless the environment's allowed domains include greenhouse/lever/ashby.
