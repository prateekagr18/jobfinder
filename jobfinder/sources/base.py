"""The ``JobSource`` interface every source implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

from ..models import Job


class JobSource(ABC):
    """Fetches the current postings for one board (company) or one file."""

    name = "base"

    @abstractmethod
    def fetch(self) -> List[Job]:
        """Return normalized jobs; must not raise on network/data errors (log and return [])."""


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 (incl. trailing ``Z``) to aware UTC; ``None`` if absent/unparseable."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def from_epoch_ms(value) -> Optional[datetime]:
    """Lever-style epoch milliseconds → aware UTC datetime."""
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def looks_remote(*parts: Optional[str]) -> bool:
    """True if any location/workplace string says remote."""
    return any(p and "remote" in p.lower() for p in parts)
