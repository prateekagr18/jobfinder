"""Text helpers: HTML stripping, normalization and boundary-safe keyword search."""

from __future__ import annotations

import html
import re
from typing import Tuple

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Headings after which a JD lists optional skills. Keywords found *only* there
# get a reduced weight — missing a "nice to have" shouldn't sink the ATS score.
_PREFERRED_RE = re.compile(
    r"(nice[ -]to[ -]haves?|bonus points|preferred qualifications|"
    r"it'?s a plus|pluses|bonus if|preferred skills)",
    re.IGNORECASE,
)


def strip_html(raw: str) -> str:
    """Turn ATS-board HTML into plain text.

    Greenhouse double-escapes its ``content`` field (``&lt;p&gt;``), so we unescape
    twice before removing tags; block tags become newlines to keep section breaks.
    """
    if not raw:
        return ""
    text = html.unescape(html.unescape(raw))
    text = re.sub(r"(?i)<\s*(br|/p|/li|/h\d|/div)\s*/?>", "\n", text)
    text = _TAG_RE.sub(" ", text)
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def normalize(text: str) -> str:
    """Lower-case and collapse whitespace; keeps ``+ # . /`` so C++/C#/Node.js survive."""
    return _WS_RE.sub(" ", text.lower()).strip()


def contains(text: str, pattern: str) -> int:
    """Count occurrences of regex ``pattern`` in normalized ``text`` at word boundaries.

    Boundaries are "not a letter/digit" rather than ``\\b`` so terms ending in
    symbols (``c++``, ``c#``) still match, while ``java`` won't match ``javascript``.
    """
    return len(re.findall(rf"(?<![a-z0-9])(?:{pattern})(?![a-z0-9])", text))


def split_preferred(text: str) -> Tuple[str, str]:
    """Split a JD into (core, preferred) at the first "nice to have"-style heading."""
    m = _PREFERRED_RE.search(text)
    if not m:
        return text, ""
    return text[: m.start()], text[m.start():]
