"""Polite HTTP client shared by all board sources.

Throttling: a fixed ``delay`` between requests (these are free public endpoints;
being polite keeps us un-banned). Retries: 429/5xx/connection errors back off
exponentially, honouring ``Retry-After``. A 404 means a wrong board token — no
retry, logged, skipped. A per-host circuit breaker stops trying a host after a
connection-level failure so a blocked/down host costs one timeout, not
(boards × retries) of them — important in sandboxes with egress allow-lists.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, Set
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)

USER_AGENT = "jobfinder/0.1 (personal job search; low volume)"


class HttpClient:
    """GET-JSON with throttle, retry/backoff and a per-host circuit breaker."""

    def __init__(
        self,
        timeout: float = 20.0,
        delay: float = 1.0,
        max_retries: int = 3,
        backoff: float = 2.0,
        session: Optional[requests.Session] = None,
        sleep=time.sleep,
    ):
        """Configure limits; ``session``/``sleep`` are injectable for tests."""
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self._sleep = sleep
        self._last = 0.0
        self.dead_hosts: Set[str] = set()

    def _throttle(self) -> None:
        """Sleep so consecutive requests are at least ``delay`` seconds apart."""
        wait = self._last + self.delay - time.monotonic()
        if wait > 0:
            self._sleep(wait)
        self._last = time.monotonic()

    def get_json(self, url: str, params: Optional[dict] = None) -> Optional[Any]:
        """Return parsed JSON, or ``None`` on a permanent/exhausted failure (never raises)."""
        host = urlparse(url).netloc
        if host in self.dead_hosts:
            return None
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                log.warning("%s unreachable (%s); skipping host for this run", host, exc.__class__.__name__)
                self.dead_hosts.add(host)
                return None
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    log.warning("Non-JSON response from %s", url)
                    return None
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                retry_after = resp.headers.get("Retry-After", "")
                wait = float(retry_after) if retry_after.isdigit() else self.backoff ** (attempt + 1)
                log.info("%s from %s; retrying in %.0fs", resp.status_code, url, wait)
                self._sleep(wait)
                continue
            log.warning("GET %s -> HTTP %s; skipping", url, resp.status_code)
            return None
        return None
