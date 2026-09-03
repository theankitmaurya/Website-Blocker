"""Dashboard – circular ring timer, duration picker, and quick stats."""
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup, QSpinBox,
    QFrame, QMessageBox, QSizePolicy,
    QScrollArea,
)

from core.blocker import BlockerService, BlockerError
from core.domain_manager import DomainManager
from core.timer import BlockTimer
from database.database import DatabaseManager
from database.models import Session
from ui.custom_widgets import CircularTimerWidget
from utils.validators import get_website_name
from utils.permissions import is_admin, request_elevation
from utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_seconds(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_duration_human(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    if m:
        return f"{m}m"
    return f"{seconds}s"


# ─────────────────────────────────────────────────────────────────────────────
# DashboardWidget
# ─────────────────────────────────────────────────────────────────────────────

_DURATION_PRESETS = [
    ("15m",  15 * 60),
    ("30m",  30 * 60),
    ("1 hr", 60 * 60),
    ("2 hr", 2 * 60 * 60),
    ("4 hr", 4 * 60 * 60),
]


class DashboardWidget(QWidget):
    session_started = Signal(int)
    session_stopped = Signal()

    def __init__(
        self,
        db: DatabaseManager,
        blocker: BlockerService,
        domain_manager: DomainManager,
        timer: BlockTimer,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.blocker = blocker
        self.domain_manager = domain_manager
        self.timer = timer

        self.current_session: Optional[Session] = None
        self._total_duration: int = 3600          # remembered for ring calc
        self._selected_duration: int = 3600        # currently chosen preset

        self._duration_buttons: list[QPushButton] = []
        self._selected_preset_idx: int = 2         # default = "1 hr"

        self._setup_ui()
        self._connect_signals()
        self.refresh_stats()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # Wrap everything in a scroll area so it degrades on small screens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("ContentArea")

        content = QWidget()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll)

        main = QVBoxLayout(content)
        main.setContentsMargins(28, 26, 28, 26)
        main.setSpacing(18)

        # ── Page header ──────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("Dashboard")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel("Manage and monitor your focus sessions")
        lbl_sub.setObjectName("PageSubtitle")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        header_row.addLayout(title_col)

        header_row.addStretch()

        self.status_pill = QLabel("● IDLE")
        self.status_pill.setObjectName("PillIdle")
        header_row.addWidget(self.status_pill, alignment=Qt.AlignTop)

        main.addLayout(header_row)

        # ── Circular timer ───────────────────────────────────────────
        timer_frame = QFrame()
        timer_frame.setObjectName("PrimaryCard")
        timer_inner = QVBoxLayout(timer_frame)
        timer_inner.setContentsMargins(20, 24, 20, 24)
        timer_inner.setSpacing(0)

        self.ring = CircularTimerWidget()
        self.ring.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ring.setMaximumHeight(300)
        timer_inner.addWidget(self.ring, alignment=Qt.AlignCenter)

        main.addWidget(timer_frame)

        # ── IDLE controls ─────────────────────────────────────────────
        self.idle_card = QFrame()
        self.idle_card.setObjectName("SecondaryCard")
        idle_layout = QVBoxLayout(self.idle_card)
        idle_layout.setContentsMargins(20, 18, 20, 18)
        idle_layout.setSpacing(14)

        dur_label = QLabel("DURATION  ·  🔒 STRICT MODE (UNSTOPPABLE)")
        dur_label.setStyleSheet("color:#8B8FA8; font-size:11px; font-weight:700; letter-spacing:0.8px;")
        idle_layout.addWidget(dur_label)

        # Duration toggle buttons
        dur_row = QHBoxLayout()
        dur_row.setSpacing(6)
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        for i, (label, seconds) in enumerate(_DURATION_PRESETS):
            btn = QPushButton(label)
            btn.setObjectName("DurationBtnActive" if i == self._selected_preset_idx else "DurationBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i, secs=seconds: self._select_preset(idx, secs))
            dur_row.addWidget(btn)
            self._duration_buttons.append(btn)

        # Custom button
        btn_custom = QPushButton("Custom")
        btn_custom.setObjectName("DurationBtn")
        btn_custom.setCursor(Qt.PointingHandCursor)
        btn_custom.clicked.connect(lambda: self._select_preset(-1, 0))
        dur_row.addWidget(btn_custom)
        self._duration_buttons.append(btn_custom)
        dur_row.addStretch()
        idle_layout.addLayout(dur_row)

        # Custom spin row (hidden by default)
        self.custom_row = QWidget()
        custom_inner = QHBoxLayout(self.custom_row)
        custom_inner.setContentsMargins(0, 0, 0, 0)
        custom_inner.setSpacing(10)
        lbl_cust = QLabel("Custom duration:")
        lbl_cust.setStyleSheet("color:#7A7D90;")
        self.custom_spin = QSpinBox()
        self.custom_spin.setRange(1, 1440)
        self.custom_spin.setValue(45)
        self.custom_spin.setSuffix("  min")
        self.custom_spin.setFixedWidth(140)
        self.custom_spin.valueChanged.connect(self._on_custom_value_changed)
        custom_inner.addWidget(lbl_cust)
        custom_inner.addWidget(self.custom_spin)
        custom_inner.addStretch()
        self.custom_row.setVisible(False)
        idle_layout.addWidget(self.custom_row)

        # Start button
        self.start_btn = QPushButton("🚀   Start Strict Focus Session")
        self.start_btn.setObjectName("BtnPrimary")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)
        idle_layout.addWidget(self.start_btn)

        main.addWidget(self.idle_card)

        # ── ACTIVE controls ───────────────────────────────────────────
        self.active_card = QFrame()
        self.active_card.setObjectName("AccentCard")
        active_layout = QVBoxLayout(self.active_card)
        active_layout.setContentsMargins(20, 16, 20, 16)
        active_layout.setSpacing(12)

        self.blocked_sites_label = QLabel("Websites blocked:")
        self.blocked_sites_label.setStyleSheet("color:#8B6EE8; font-size:12px; font-weight:600;")
        active_layout.addWidget(self.blocked_sites_label)

        # Locked strict card indicator (replaces manual stop button)
        lock_box = QFrame()
        lock_box.setStyleSheet("""
            QFrame {
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.22);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        lock_lay = QHBoxLayout(lock_box)
        lock_lay.setContentsMargins(8, 6, 8, 6)
        lock_lay.setSpacing(10)

        icon_lbl = QLabel("🔒")
        icon_lbl.setStyleSheet("font-size: 20px;")
        lock_lay.addWidget(icon_lbl)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(2)
        txt_title = QLabel("Strict Mode Active")
        txt_title.setStyleSheet("color: #F87171; font-weight: 700; font-size: 13px;")
        txt_sub = QLabel("Timer cannot be stopped early. Websites will remain blocked until the session completes.")
        txt_sub.setStyleSheet("color: #8B8FA8; font-size: 11px;")
        txt_sub.setWordWrap(True)
        txt_col.addWidget(txt_title)
        txt_col.addWidget(txt_sub)
        lock_lay.addLayout(txt_col, 1)

        active_layout.addWidget(lock_box)

        self.active_card.setVisible(False)
        main.addWidget(self.active_card)

        # ── Stats row ─────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        self.card_focus = self._make_stat_card("TODAY'S FOCUS", "0h 0m", "#7C5CFC")
        self.card_sessions = self._make_stat_card("SESSIONS", "0", "#22C55E")
        self.card_sites = self._make_stat_card("BLOCKED SITES", "0 active", "#F59E0B")

        stats_row.addWidget(self.card_focus)
        stats_row.addWidget(self.card_sessions)
        stats_row.addWidget(self.card_sites)
        main.addLayout(stats_row)

    @staticmethod
    def _make_stat_card(title: str, value: str, accent: str) -> QFrame:
        card = QFrame()
        card.setObjectName("SecondaryCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(f"color:#383A47; font-size:10px; font-weight:700; letter-spacing:0.9px;")
        lay.addWidget(t)

        v = QLabel(value)
        v.setStyleSheet(f"color:{accent}; font-size:20px; font-weight:700; letter-spacing:-0.3px;")
        lay.addWidget(v)

        # Store reference on card for updates
        card.value_label = v
        return card

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.timer.tick.connect(self._on_tick)
        self.timer.finished.connect(self._on_timer_finished)

    # ------------------------------------------------------------------
    # Duration selection
    # ------------------------------------------------------------------

    def _select_preset(self, idx: int, seconds: int) -> None:
        """Activates a duration preset button (or custom if idx == -1)."""
        is_custom = idx == -1
        self._selected_preset_idx = idx
        self._selected_duration = seconds if not is_custom else self.custom_spin.value() * 60
        self.custom_row.setVisible(is_custom)

        for i, btn in enumerate(self._duration_buttons):
            is_active = (i == idx) or (is_custom and i == len(self._duration_buttons) - 1)
            new_name = "DurationBtnActive" if is_active else "DurationBtn"
            if btn.objectName() != new_name:
                btn.setObjectName(new_name)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def _on_custom_value_changed(self, value: int) -> None:
        self._selected_duration = value * 60

    def get_selected_duration_seconds(self) -> int:
        if self._selected_preset_idx == -1:
            return self.custom_spin.value() * 60
        if 0 <= self._selected_preset_idx < len(_DURATION_PRESETS):
            return _DURATION_PRESETS[self._selected_preset_idx][1]
        return 3600

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def _on_start_clicked(self) -> None:
        domains = self.domain_manager.get_enabled_domains()
        if not domains:
            QMessageBox.warning(
                self, "No Websites Configured",
                "There are no enabled websites to block.\n\n"
                "Go to the Websites tab and add or enable at least one domain first.",
            )
            return

        duration = self.get_selected_duration_seconds()
        try:
            session = self.blocker.start_session(
                domains=domains, duration_seconds=duration
            )
            self.current_session = session
            self._total_duration = duration
            self.timer.start(duration)
            self._enter_active_mode(duration, domains)
            self.session_started.emit(duration)
        except BlockerError as e:
            if not is_admin():
                reply = QMessageBox.question(
                    self,
                    "Administrator Privileges Required",
                    "Modifying the Windows hosts file requires Administrator privileges.\n\n"
                    "Would you like to restart Website Blocker with Administrator privileges now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    if request_elevation():
                        from PySide6.QtWidgets import QApplication
                        QApplication.quit()
                        return
            QMessageBox.critical(
                self, "Blocking Failed",
                f"Could not start the blocking session:\n\n{e}\n\n"
                "Please run Website Blocker as Administrator (Right click -> Run as administrator).",
            )

    def stop_current_session(self, status: str = "completed") -> None:
        self.timer.stop()
        if self.current_session and self.current_session.id:
            self.blocker.end_session(self.current_session.id, status=status)
            self.current_session = None
        self._enter_idle_mode()
        self.refresh_stats()
        self.session_stopped.emit()

    # ------------------------------------------------------------------
    # Timer callbacks
    # ------------------------------------------------------------------

    def _on_tick(self, remaining: int) -> None:
        self.ring.set_active(remaining, self._total_duration)

    def _on_timer_finished(self) -> None:
        if self.current_session and self.current_session.id:
            self.blocker.end_session(self.current_session.id, status="completed")
            self.current_session = None
        self._enter_idle_mode()
        self.refresh_stats()
        self.session_stopped.emit()
        QMessageBox.information(
            self, "🎉 Session Complete!",
            "Your focus session has ended.\n\nAll websites have been unblocked — great work!",
        )

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _enter_active_mode(self, duration: int, domains: list[str]) -> None:
        self.status_pill.setText("🔴  BLOCKING ACTIVE")
        self.status_pill.setObjectName("PillActive")
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        names = [get_website_name(d) for d in domains]
        count = len(names)
        shown = ", ".join(names[:3])
        more = f" +{count - 3} more" if count > 3 else ""
        self.blocked_sites_label.setText(f"Blocking  {shown}{more}")

        self.ring.set_active(duration, self._total_duration)
        self.idle_card.setVisible(False)
        self.active_card.setVisible(True)

    def _enter_idle_mode(self) -> None:
        self.status_pill.setText("● IDLE")
        self.status_pill.setObjectName("PillIdle")
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        self.ring.set_idle()
        self.idle_card.setVisible(True)
        self.active_card.setVisible(False)

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def restore_active_session(self, session: Session) -> None:
        """Restores dashboard to active state after startup recovery."""
        self.current_session = session
        try:
            start_dt = datetime.fromisoformat(session.start_time)
            elapsed = (datetime.now() - start_dt).total_seconds()
            remaining = max(0, int(session.duration_seconds - elapsed))
            self._total_duration = session.duration_seconds
            domains = self.domain_manager.get_enabled_domains()

            self.timer.start(session.duration_seconds, start_time=start_dt)
            self._enter_active_mode(remaining, domains)
            self.session_started.emit(remaining)
        except Exception as e:
            logger.error("restore_active_session failed: %s", e)
            self._enter_idle_mode()

    # ------------------------------------------------------------------
    # Stats refresh
    # ------------------------------------------------------------------

    def refresh_stats(self) -> None:
        today_sec, today_count = self.db.get_today_stats()
        self.card_focus.value_label.setText(format_duration_human(today_sec))
        self.card_sessions.value_label.setText(str(today_count))

        sites = self.domain_manager.list_all()
        enabled = sum(1 for s in sites if s.enabled)
        self.card_sites.value_label.setText(
            f"{enabled}/{len(sites)}" if sites else "—"
        )
