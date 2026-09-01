"""
Favicon fetching and disk-caching service.

Architecture
------------
FaviconLoader (QObject) uses Qt's QNetworkAccessManager for non-blocking HTTP.
All downloads happen inside the Qt event loop — no threads needed.

Usage:
    loader = FaviconLoader(parent_qobject)
    loader.favicon_ready.connect(my_slot)   # slot(domain: str, path: str)
    loader.request("youtube.com")           # returns immediately

When the favicon is ready, favicon_ready(domain, path) is emitted.
path is an absolute path string, or "" when the download failed / yielded no
usable icon (e.g. Google's 1×1 transparent placeholder).

Cache layout:
    data/favicons/<domain>.png   ← successful downloads
"""

import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Set

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
)

from utils.config import DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Cache directory
# ─────────────────────────────────────────────────────────────────────────────

FAVICON_DIR: Path = DATA_DIR / "favicons"
FAVICON_DIR.mkdir(parents=True, exist_ok=True)

# Minimum byte size to consider a download a real image (not a 1×1 placeholder)
_MIN_FAVICON_BYTES = 200

# Google's favicon CDN – returns 64×64 PNG for most domains
_GOOGLE_URL = "https://www.google.com/s2/favicons?domain={}&sz=64"

# DuckDuckGo CDN – reliable fallback
_DDG_URL = "https://icons.duckduckgo.com/ip3/{}.ico"


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_cached_favicon(domain: str) -> Optional[Path]:
    """Returns the cached favicon Path for *domain*, or None."""
    for ext in (".png", ".ico"):
        p = FAVICON_DIR / f"{domain}{ext}"
        if p.exists() and p.stat().st_size >= _MIN_FAVICON_BYTES:
            return p
    return None


def clear_favicon_cache(domain: str) -> None:
    """Deletes all cached icon files for *domain* (for testing / reset)."""
    for ext in (".png", ".ico"):
        p = FAVICON_DIR / f"{domain}{ext}"
        if p.exists():
            p.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# FaviconLoader
# ─────────────────────────────────────────────────────────────────────────────

class FaviconLoader(QObject):
    """
    Async, deduplicated favicon fetcher backed by QNetworkAccessManager.

    Signals
    -------
    favicon_ready(domain, path)
        Emitted on the main thread when a favicon becomes available.
        ``path`` is a non-empty absolute path string, or "" if no icon
        could be retrieved for this domain.
    """

    favicon_ready = Signal(str, str)  # (domain, abs_path_or_empty)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._pending: Dict[QNetworkReply, str] = {}  # reply → domain
        self._in_flight: Set[str] = set()             # domains being fetched
        self._fallback: Dict[str, bool] = {}           # domain → used_fallback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request(self, domain: str) -> None:
        """
        Request a favicon for *domain*.
        - Returns immediately if the favicon is already cached.
        - De-duplicates: silently ignores a request if one is in-flight.
        - Otherwise fires an async HTTP GET (primary → Google CDN).
        """
        cached = get_cached_favicon(domain)
        if cached:
            self.favicon_ready.emit(domain, str(cached))
            return

        if domain in self._in_flight:
            return

        self._in_flight.add(domain)
        self._fallback[domain] = False
        self._get(_GOOGLE_URL.format(urllib.parse.quote(domain, safe=""), ), domain)

    def prefetch_all(self, domains: list[str]) -> None:
        """Convenience: request favicons for every domain in *domains*."""
        for d in domains:
            self.request(d)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, domain: str) -> None:
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", b"Website-Blocker/1.0 (Windows; Favicon)")
        reply: QNetworkReply = self._nam.get(req)
        self._pending[reply] = domain
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply: QNetworkReply) -> None:
        domain = self._pending.pop(reply, "")

        if not domain:
            reply.deleteLater()
            return

        error = reply.error()
        if error == QNetworkReply.NetworkError.NoError:
            data: bytes = bytes(reply.readAll())
            if len(data) >= _MIN_FAVICON_BYTES:
                # Save to cache
                dest = FAVICON_DIR / f"{domain}.png"
                dest.write_bytes(data)
                logger.info("Favicon cached  %s  (%d B → %s)", domain, len(data), dest.name)
                self._in_flight.discard(domain)
                self.favicon_ready.emit(domain, str(dest))
                reply.deleteLater()
                return

            # Google returned a tiny placeholder — try DuckDuckGo fallback once
            if not self._fallback.get(domain):
                logger.debug("Google favicon too small for %s, trying DDG fallback", domain)
                self._fallback[domain] = True
                reply.deleteLater()
                # Re-use the same slot; domain is still in _in_flight
                self._get(_DDG_URL.format(urllib.parse.quote(domain, safe="")), domain)
                return

            # Both sources failed – emit empty
            logger.debug("No usable favicon for %s", domain)

        else:
            logger.debug("Favicon network error for %s: %s", domain, reply.errorString())

            # Try DDG fallback on network error from Google (if not already tried)
            if not self._fallback.get(domain):
                self._fallback[domain] = True
                reply.deleteLater()
                self._get(_DDG_URL.format(urllib.parse.quote(domain, safe="")), domain)
                return

        self._in_flight.discard(domain)
        self.favicon_ready.emit(domain, "")
        reply.deleteLater()
