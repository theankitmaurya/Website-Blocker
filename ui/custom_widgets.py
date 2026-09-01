"""
Premium custom-painted widgets for Website Blocker.

Exports
-------
CircularTimerWidget  – QPainter countdown ring (idle green / active violet).
DomainAvatarWidget   – Coloured initial-letter badge (fallback / offline).
FaviconWidget        – Shows real favicon fetched from network, falls back
                       to DomainAvatarWidget if unavailable.
domain_color         – Deterministic accent colour from a domain string.
"""
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush,
    QPixmap, QPainterPath,
)
from PySide6.QtWidgets import QWidget, QSizePolicy

if TYPE_CHECKING:
    from services.favicon_service import FaviconLoader


# ─────────────────────────────────────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_PALETTE = [
    QColor("#7C5CFC"),  # violet
    QColor("#F59E0B"),  # amber
    QColor("#22C55E"),  # emerald
    QColor("#3B82F6"),  # blue
    QColor("#EC4899"),  # pink
    QColor("#14B8A6"),  # teal
    QColor("#F97316"),  # orange
    QColor("#8B5CF6"),  # purple
]


def domain_color(domain: str) -> QColor:
    """Returns a deterministic accent colour for a domain string."""
    return _DOMAIN_PALETTE[abs(hash(domain)) % len(_DOMAIN_PALETTE)]


# ─────────────────────────────────────────────────────────────────────────────
# CircularTimerWidget
# ─────────────────────────────────────────────────────────────────────────────

class CircularTimerWidget(QWidget):
    """
    QPainter countdown ring.

    Idle  → dim green full ring  + "--:--:--" + "READY TO FOCUS"
    Active → violet depleting arc with outer glow + live HH:MM:SS + "FOCUS SESSION"
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._progress: float = 0.0
        self._time_text: str = "--:--:--"
        self._status_text: str = "READY TO FOCUS"
        self._active: bool = False

        self.setMinimumSize(260, 260)
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)

    def set_idle(self) -> None:
        self._progress = 0.0
        self._time_text = "--:--:--"
        self._status_text = "READY TO FOCUS"
        self._active = False
        self.update()

    def set_active(self, remaining_seconds: int, total_seconds: int) -> None:
        self._active = True
        self._status_text = "FOCUS SESSION"
        self._progress = (
            max(0.0, min(1.0, remaining_seconds / total_seconds))
            if total_seconds > 0 else 0.0
        )
        h = remaining_seconds // 3600
        m = (remaining_seconds % 3600) // 60
        s = remaining_seconds % 60
        self._time_text = f"{h:02d}:{m:02d}:{s:02d}"
        self.update()

    def heightForWidth(self, width: int) -> int:
        return width

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        side = min(w, h)
        cx, cy = w / 2.0, h / 2.0
        ring_w = max(12, int(side * 0.054))
        margin = ring_w + 14

        arc_rect = QRectF(
            cx - side / 2 + margin, cy - side / 2 + margin,
            side - 2 * margin, side - 2 * margin,
        )

        # Track ring
        painter.setPen(QPen(QColor("#1C1D25"), ring_w, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(arc_rect)

        # Progress arc
        if self._active and self._progress > 0.001:
            start, span = 90 * 16, -int(self._progress * 360 * 16)
            painter.setPen(QPen(QColor(124, 92, 252, 38), ring_w + 16, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(arc_rect, start, span)
            painter.setPen(QPen(QColor("#7C5CFC"), ring_w, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(arc_rect, start, span)
        elif not self._active:
            painter.setPen(QPen(QColor(74, 222, 128, 35), ring_w, Qt.SolidLine, Qt.RoundCap))
            painter.drawEllipse(arc_rect)

        # Inner fill
        inner_r = arc_rect.width() / 2.0 - ring_w * 0.55
        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#0D0E12")))
        painter.drawEllipse(inner_rect)

        # Time text
        time_pt = max(10, int(side * 0.125))
        painter.setFont(QFont("Consolas", time_pt, QFont.Bold))
        painter.setPen(QColor("#E8EAEF") if self._active else QColor("#30323C"))
        painter.drawText(
            QRectF(cx - inner_r, cy - inner_r * 0.55, inner_r * 2, inner_r),
            Qt.AlignCenter, self._time_text,
        )

        # Status label
        lbl_pt = max(6, int(side * 0.044))
        painter.setFont(QFont("Segoe UI", lbl_pt))
        painter.setPen(QColor("#3A3C47"))
        painter.drawText(
            QRectF(cx - inner_r, cy + inner_r * 0.05, inner_r * 2, inner_r * 0.45),
            Qt.AlignCenter, self._status_text,
        )


# ─────────────────────────────────────────────────────────────────────────────
# DomainAvatarWidget  (offline / fallback)
# ─────────────────────────────────────────────────────────────────────────────

class DomainAvatarWidget(QWidget):
    """
    Circular badge with a coloured initial letter.
    Used as a standalone fallback when no FaviconLoader is available.
    """

    def __init__(
        self, domain: str, size: int = 34, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._letter = domain[0].upper() if domain else "?"
        self._color = domain_color(domain)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        s = self.width()
        c = self._color

        painter.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 20)))
        painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 55), 1.0))
        painter.drawEllipse(2, 2, s - 4, s - 4)

        painter.setFont(QFont("Segoe UI", max(7, int(s * 0.38)), QFont.Bold))
        painter.setPen(c)
        painter.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, self._letter)


# ─────────────────────────────────────────────────────────────────────────────
# FaviconWidget  (live favicon with letter-avatar fallback)
# ─────────────────────────────────────────────────────────────────────────────

class FaviconWidget(QWidget):
    """
    Circular badge that shows a domain's real favicon.

    Behaviour:
    - Immediately renders the colored-letter avatar.
    - Checks the local cache; if a PNG is present, upgrades to the real icon.
    - Fires loader.request(domain) so missing favicons are fetched in the
      background; upgrades to the real icon once the signal arrives.
    - Thread-safe: the favicon_ready signal is delivered on the Qt main thread
      by QNetworkAccessManager, so no extra locking is needed.
    """

    def __init__(
        self,
        domain: str,
        loader: "FaviconLoader",
        size: int = 36,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._domain = domain
        self._size = size
        self._color = domain_color(domain)
        self._letter = domain[0].upper() if domain else "?"
        self._pixmap: Optional[QPixmap] = None
        self.setFixedSize(size, size)

        # Listen for any favicon_ready event; filter by domain inside slot
        loader.favicon_ready.connect(self._on_favicon_ready)

        # Kick off fetch (no-op if already cached or in-flight)
        loader.request(domain)

    # ------------------------------------------------------------------
    # Slot
    # ------------------------------------------------------------------

    def _on_favicon_ready(self, domain: str, path: str) -> None:
        """Called on the main thread when a favicon download completes."""
        if domain != self._domain or not path:
            return
        self._load_pixmap(path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_pixmap(self, path: str) -> None:
        pix = QPixmap(path)
        if pix.isNull() or pix.width() <= 1 or pix.height() <= 1:
            return
        target = self._size - 12           # icon occupies the inner circle
        self._pixmap = pix.scaled(
            target, target, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.update()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        s = self._size
        c = self._color

        # Outer tinted circle (always present, provides consistent border)
        painter.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 18)))
        painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 50), 1.0))
        painter.drawEllipse(2, 2, s - 4, s - 4)

        if self._pixmap:
            # Clip subsequent drawing to a slightly smaller circle
            clip = QPainterPath()
            clip.addEllipse(QRectF(3, 3, s - 6, s - 6))
            painter.setClipPath(clip)

            # Dark fill so transparent PNGs look good on dark background
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#1A1C24")))
            painter.drawEllipse(QRectF(3, 3, s - 6, s - 6))

            # Centre the favicon pixmap
            x = (s - self._pixmap.width()) // 2
            y = (s - self._pixmap.height()) // 2
            painter.drawPixmap(x, y, self._pixmap)
        else:
            # Fallback: colored initial letter
            painter.setFont(QFont("Segoe UI", max(7, int(s * 0.38)), QFont.Bold))
            painter.setPen(c)
            painter.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, self._letter)
