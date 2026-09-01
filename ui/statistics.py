"""Statistics panel – focus time metrics and session history table."""
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar,
)

from database.database import DatabaseManager
from ui.dashboard import format_duration_human
from utils.logger import get_logger

logger = get_logger(__name__)

# Accent colours for stat cards
_CARD_ACCENTS = ["#7C5CFC", "#22C55E", "#F59E0B", "#3B82F6"]


class StatisticsWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self._setup_ui()
        self.refresh_stats()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 26, 28, 26)
        main.setSpacing(20)

        # ── Page header ──────────────────────────────────────────────
        lbl_title = QLabel("Statistics")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel("Your productivity metrics and session history")
        lbl_sub.setObjectName("PageSubtitle")
        main.addWidget(lbl_title)
        main.addWidget(lbl_sub)

        # ── Metric cards row ──────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._today_time_val, today_card = self._metric_card(
            "TODAY'S FOCUS", "0h 0m", "#7C5CFC"
        )
        self._today_sess_val, today_s_card = self._metric_card(
            "TODAY'S SESSIONS", "0", "#22C55E"
        )
        self._week_time_val, week_card = self._metric_card(
            "THIS WEEK", "0h 0m", "#F59E0B"
        )
        self._week_sess_val, week_s_card = self._metric_card(
            "WEEKLY SESSIONS", "0", "#3B82F6"
        )

        for card in (today_card, today_s_card, week_card, week_s_card):
            cards_row.addWidget(card)
        main.addLayout(cards_row)

        # ── Session history label ─────────────────────────────────────
        hist_row = QHBoxLayout()
        lbl_hist = QLabel("Session History")
        lbl_hist.setStyleSheet("font-size:15px; font-weight:700; color:#D0D3E0;")
        hist_row.addWidget(lbl_hist)
        hist_row.addStretch()
        self._total_lbl = QLabel("")
        self._total_lbl.setStyleSheet("color:#565869; font-size:12px;")
        hist_row.addWidget(self._total_lbl)
        main.addLayout(hist_row)

        # ── Table ─────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["DATE", "START TIME", "DURATION", "TYPE", "STATUS"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        main.addWidget(self.table, 1)

    @staticmethod
    def _metric_card(title: str, value: str, accent: str):
        """Creates a styled metric card and returns (value_label, frame)."""
        card = QFrame()
        card.setObjectName("SecondaryCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(6)

        t = QLabel(title)
        t.setStyleSheet(
            f"color:#383A47; font-size:10px; font-weight:700; letter-spacing:0.9px;"
        )
        lay.addWidget(t)

        v = QLabel(value)
        v.setStyleSheet(
            f"color:{accent}; font-size:22px; font-weight:700; letter-spacing:-0.4px;"
        )
        lay.addWidget(v)

        return v, card

    def refresh_stats(self) -> None:
        today_sec, today_count = self.db.get_today_stats()
        self._today_time_val.setText(format_duration_human(today_sec))
        self._today_sess_val.setText(str(today_count))

        week_sec, week_count = self.db.get_week_stats()
        self._week_time_val.setText(format_duration_human(week_sec))
        self._week_sess_val.setText(str(week_count))

        sessions = self.db.get_sessions(limit=100)
        self._total_lbl.setText(f"{len(sessions)} sessions recorded")
        self.table.setRowCount(len(sessions))

        for row, sess in enumerate(sessions):
            try:
                dt = datetime.fromisoformat(sess.start_time)
                date_str = dt.strftime("%b %d, %Y")
                time_str = dt.strftime("%I:%M %p")
            except Exception:
                date_str = "—"
                time_str = sess.start_time

            dur_str = format_duration_human(sess.duration_seconds)
            type_str = sess.type.capitalize()

            status = sess.status
            if status == "completed":
                status_text = "✓  Completed"
                status_color = "#22C55E"
            elif status == "stopped":
                status_text = "⏹  Stopped"
                status_color = "#F59E0B"
            elif status == "active":
                status_text = "●  Active"
                status_color = "#7C5CFC"
            else:
                status_text = status.capitalize()
                status_color = "#565869"

            cells = [
                (date_str, "#7A7D90"),
                (time_str, "#C0C3D2"),
                (dur_str,  "#C0C3D2"),
                (type_str, "#7A7D90"),
                (status_text, status_color),
            ]

            for col, (text, color) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, col, item)

        self.table.resizeRowsToContents()
