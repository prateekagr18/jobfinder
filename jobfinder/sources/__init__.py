"""Job sources: company ATS boards (Greenhouse / Lever / Ashby) and a JSON file import.

Board sources call the free, unauthenticated public job-board APIs those ATSs
expose for career pages. Postings there are the *original* listing — applying
on the company's own ATS (rather than via an aggregator re-post) lands you
directly in the recruiter's queue, and timestamps are accurate for freshness.

``FileSource`` loads jobs gathered elsewhere (e.g. by Claude via the Indeed/Dice
connectors in the nightly routine) so they're scored by the same engine.
"""

from __future__ import annotations

from .base import JobSource
from .boards import AshbySource, GreenhouseSource, LeverSource
from .file import FileSource

BOARD_SOURCES = {
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "ashby": AshbySource,
}

__all__ = ["JobSource", "GreenhouseSource", "LeverSource", "AshbySource", "FileSource", "BOARD_SOURCES"]
