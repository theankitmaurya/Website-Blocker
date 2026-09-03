"""Settings and maintenance panel."""
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox,
)

from core.hosts_manager import HostsManager
from database.database import DatabaseManager
from utils.config import APP_NAME, APP_VERSION, DEFAULT_HOSTS_PATH, DEFAULT_HOSTS_BACKUP_PATH
from utils.permissions import is_admin
from utils.logger import get_logger

logger = get_logger(__name__)


class SettingsWidget(QWidget):
    history_cleared = Signal()

    def __init__(
        self,
        db: DatabaseManager,
        hosts_manager: HostsManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.hosts = hosts_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 26, 28, 26)
        main.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────
        lbl_title = QLabel("Settings")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel("Hosts file maintenance, data management, and app info")
        lbl_sub.setObjectName("PageSubtitle")
        main.addWidget(lbl_title)
        main.addWidget(lbl_sub)

        # ── Lock banner ───────────────────────────────────────────────
        self.lock_banner = QFrame()
        self.lock_banner.setObjectName("WarningCard")
        lock_lay = QHBoxLayout(self.lock_banner)
        lock_lay.setContentsMargins(14, 10, 14, 10)
        lock_lbl = QLabel(
            "🔒  Focus session active. Hosts restore and data clearing are locked."
        )
        lock_lbl.setStyleSheet("color:#D97706; font-weight:600; font-size:12px;")
        lock_lay.addWidget(lock_lbl)
        self.lock_banner.setVisible(False)
        main.addWidget(self.lock_banner)

        # ── Hosts file section ────────────────────────────────────────
        main.addWidget(self._section_label("HOSTS FILE & DNS"))
        hosts_card = self._card()
        hosts_lay = QVBoxLayout(hosts_card)
        hosts_lay.setContentsMargins(20, 18, 20, 18)
        hosts_lay.setSpacing(14)

        desc1 = QLabel(
            "If something goes wrong, restore your original hosts file from the "
            "automatic backup created before each blocking session. You can also "
            "manually flush the Windows DNS resolver cache."
        )
        desc1.setWordWrap(True)
        desc1.setStyleSheet("color:#565869; font-size:12px; line-height:1.5;")
        hosts_lay.addWidget(desc1)

        btns1 = QHBoxLayout()
        btns1.setSpacing(10)

        self.btn_restore = QPushButton("🔄  Restore Hosts Backup")
        self.btn_restore.setObjectName("BtnSecondary")
        self.btn_restore.setCursor(Qt.PointingHandCursor)
        self.btn_restore.clicked.connect(self._restore)
        btns1.addWidget(self.btn_restore)

        self.btn_flush = QPushButton("⚡  Flush DNS Cache")
        self.btn_flush.setObjectName("BtnSecondary")
        self.btn_flush.setCursor(Qt.PointingHandCursor)
        self.btn_flush.clicked.connect(self._flush_dns)
        btns1.addWidget(self.btn_flush)

        btns1.addStretch()
        hosts_lay.addLayout(btns1)
        main.addWidget(hosts_card)

        # ── Data management section ───────────────────────────────────
        main.addWidget(self._section_label("DATA MANAGEMENT"))
        data_card = self._card()
        data_lay = QVBoxLayout(data_card)
        data_lay.setContentsMargins(20, 18, 20, 18)
        data_lay.setSpacing(14)

        desc2 = QLabel(
            "Clear all recorded focus sessions and statistics from the local database. "
            "Your configured websites will not be affected."
        )
        desc2.setWordWrap(True)
        desc2.setStyleSheet("color:#565869; font-size:12px;")
        data_lay.addWidget(desc2)

        self.btn_clear = QPushButton("🗑  Clear Session History")
        self.btn_clear.setObjectName("BtnDanger")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_history)
        self.btn_clear.setFixedWidth(220)
        data_lay.addWidget(self.btn_clear, alignment=Qt.AlignLeft)
        main.addWidget(data_card)

        # ── System info ───────────────────────────────────────────────
        main.addWidget(self._section_label("SYSTEM INFORMATION"))
        info_card = self._card()
        info_lay = QVBoxLayout(info_card)
        info_lay.setContentsMargins(20, 18, 20, 18)
        info_lay.setSpacing(10)

        admin_status = (
            "<span style='color:#22C55E;'>✅  Administrator (elevated)</span>"
            if is_admin()
            else "<span style='color:#F59E0B;'>⚠️  Standard user — elevation required for blocking</span>"
        )

        rows = [
            ("Application",  f"{APP_NAME}  v{APP_VERSION}"),
            ("Permissions",  admin_status),
            ("Hosts file",   str(DEFAULT_HOSTS_PATH)),
            ("Backup path",  str(DEFAULT_HOSTS_BACKUP_PATH)),
            ("Platform",     "Windows 10 / 11"),
        ]

        for label, value in rows:
            row = QHBoxLayout()
            row.setSpacing(12)
            k = QLabel(label)
            k.setFixedWidth(110)
            k.setStyleSheet("color:#565869; font-size:12px; font-weight:600;")
            v = QLabel(value)
            v.setTextFormat(Qt.RichText)
            v.setStyleSheet("color:#9095A8; font-size:12px;")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v, 1)
            info_lay.addLayout(row)

        main.addWidget(info_card)
        main.addStretch()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#383A47; font-size:10px; font-weight:700; letter-spacing:1.1px;"
        )
        return lbl

    @staticmethod
    def _card() -> QFrame:
        card = QFrame()
        card.setObjectName("SecondaryCard")
        return card

    def set_locked(self, locked: bool) -> None:
        self.lock_banner.setVisible(locked)
        self.btn_restore.setEnabled(not locked)
        self.btn_clear.setEnabled(not locked)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _restore(self) -> None:
        reply = QMessageBox.warning(
            self, "Restore Backup",
            "This will overwrite the current hosts file with the backup copy and flush DNS.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.hosts.restore_backup():
                self.hosts.flush_dns()
                QMessageBox.information(
                    self, "Restored",
                    "Hosts file restored successfully and DNS cache flushed.",
                )
            else:
                QMessageBox.critical(
                    self, "Error",
                    "Could not restore backup.\n"
                    "Ensure a backup file exists and the app has write permission.",
                )

    def _flush_dns(self) -> None:
        ok = self.hosts.flush_dns()
        if ok:
            QMessageBox.information(self, "DNS Flushed", "Windows DNS resolver cache cleared.")
        else:
            QMessageBox.warning(self, "Failed", "Could not flush DNS cache.")

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self, "Clear Session History",
            "Delete all recorded focus sessions?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.clear_sessions()
            self.history_cleared.emit()
            QMessageBox.information(self, "Done", "Session history has been cleared.")
