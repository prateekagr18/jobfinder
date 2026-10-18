"""Command line: ``jobfinder run`` and ``jobfinder resume`` (inspect what the scorer sees)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .config import load_settings
from .pipeline import run
from .resume import load_resume, profile_from_text
from .skills import vocabulary


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point; returns a process exit code."""
    ap = argparse.ArgumentParser(prog="jobfinder", description=__doc__)
    ap.add_argument("--config", default="config.yaml", help="YAML settings (default: config.yaml)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch, score and write the daily report")
    r.add_argument("--jobs-file", help="extra jobs JSON (e.g. from Indeed/Dice) to score too")
    sub.add_parser("resume", help="show the keywords/years/management the scorer extracted")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    settings = load_settings(args.config)
    if args.cmd == "resume":
        vocab = vocabulary(settings.extra_keywords)
        p = profile_from_text(load_resume(settings.resume_path), vocab,
                              settings.years_experience, settings.has_management_experience)
        print(f"years={p.years_experience} management={p.has_management}")
        print("keywords:", ", ".join(sorted(p.keywords)))
        return 0

    results = run(settings, args.jobs_file)
    print((Path(settings.output_dir) / "digest.txt").read_text())
    return 0 if results is not None else 1


if __name__ == "__main__":
    sys.exit(main())
