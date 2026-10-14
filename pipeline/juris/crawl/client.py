"""Polite fetcher implementing SPEC §3 (REQ-CRAWL).

Single connection, delay >= 2.5 s plus jitter, on-disk cache keyed by canonical URL,
stop on the first 429/503 or after 3 consecutive errors, per-run request cap.
No retries, no concurrency, no workarounds (AGENTS.md rule 2). Live use is HUMAN-run only;
tests inject an httpx.MockTransport and never touch the network.
"""

import hashlib
import json
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx

ALLOWED_HOSTS = frozenset({"www.dgsi.pt"})
MIN_DELAY_S = 2.5
MAX_JITTER_S = 1.0
TIMEOUT_S = 30.0
MAX_CONSECUTIVE_ERRORS = 3
DEFAULT_MAX_REQUESTS = 800
STOP_STATUSES = frozenset({429, 503})


class CrawlStop(Exception):
    """The run must end now. Resume manually later (SPEC §3)."""


class FetchError(Exception):
    """One request failed; the run may continue until the error budget is spent."""


def canonical_url(url: str) -> str:
    """Drop the fragment and any `Highlight` query parameter (SPEC §3)."""
    parts = urlsplit(url)
    # Domino uses bare keywords (`?OpenDocument`): filter raw segments, never re-encode.
    segments = [s for s in parts.query.split("&") if s and s.split("=")[0].lower() != "highlight"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(segments), ""))


class PoliteFetcher:
    def __init__(
        self,
        cache_dir: Path,
        client: httpx.Client,
        *,
        contact: str,
        delay_s: float = MIN_DELAY_S,
        jitter_s: float = MAX_JITTER_S,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        if delay_s < MIN_DELAY_S:
            raise ValueError(f"delay_s must be >= {MIN_DELAY_S} (SPEC §3)")
        self._cache = cache_dir
        self._cache.mkdir(parents=True, exist_ok=True)
        self._client = client
        self._headers = {"User-Agent": f"jurisprudencia-prototype/0.1 (contact: {contact})"}
        self._delay = delay_s
        self._jitter = min(max(jitter_s, 0.0), MAX_JITTER_S)
        self._max = max_requests
        self._sleep = sleep
        self._rand = rand
        self.requests_made = 0
        self._consecutive_errors = 0

    def _path(self, url: str) -> Path:
        return self._cache / f"{hashlib.sha256(url.encode()).hexdigest()}.html"

    def cached(self, url: str) -> bool:
        return self._path(canonical_url(url)).exists()

    def get(self, url: str) -> bytes:
        """Return the raw body, from cache if present (a URL is never requested twice)."""
        url = canonical_url(url)
        host = urlsplit(url).netloc
        if host not in ALLOWED_HOSTS:
            raise ValueError(f"host not allowed: {host}")
        path = self._path(url)
        if path.exists():
            return path.read_bytes()
        if self.requests_made >= self._max:
            raise CrawlStop(f"max-requests reached ({self._max})")
        if self.requests_made > 0:
            self._sleep(self._delay + self._rand() * self._jitter)
        self.requests_made += 1
        try:
            resp = self._client.get(url, headers=self._headers, timeout=TIMEOUT_S)
        except httpx.HTTPError as exc:
            self._register_error()
            raise FetchError(f"{url}: {exc}") from exc
        if resp.status_code in STOP_STATUSES:
            raise CrawlStop(f"HTTP {resp.status_code} on {url}")
        if resp.status_code != 200:
            self._register_error()
            raise FetchError(f"{url}: HTTP {resp.status_code}")
        self._consecutive_errors = 0
        path.write_bytes(resp.content)
        meta = {
            "url": url,
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "fetched_at": datetime.now(UTC).isoformat(),
        }
        path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
        return resp.content

    def _register_error(self) -> None:
        self._consecutive_errors += 1
        if self._consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            raise CrawlStop(f"{MAX_CONSECUTIVE_ERRORS} consecutive errors")
