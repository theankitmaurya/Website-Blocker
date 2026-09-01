"""Main application window – premium dark shell with sidebar navigation."""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QStatusBar,
    QMessageBox, QFrame,
)

from core.blocker import BlockerService
from core.domain_manager import DomainManager
from core.hosts_manager import HostsManager
from core.timer import BlockTimer
from database.database import DatabaseManager
from services.favicon_service import FaviconLoader
from ui.dashboard import DashboardWidget
from ui.websites import WebsitesWidget
from ui.statistics import StatisticsWidget
from ui.settings import SettingsWidget
from utils.config import APP_NAME, APP_VERSION
from utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Global Stylesheet
# ─────────────────────────────────────────────────────────────────────────────
STYLESHEET = """
/* ═══════════════════════════════════════════════
   Website Blocker — Premium Dark Theme v2
   ═══════════════════════════════════════════════ */

QMainWindow, QDialog {
    background-color: #0D0E12;
}

QWidget {
    background-color: transparent;
    color: #D4D6E0;
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #2C2D36;
    border-radius: 3px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #2C2D36;
    border-radius: 3px;
}

/* ── Sidebar ── */
#Sidebar {
    background-color: #111318;
    border-right: 1px solid rgba(255,255,255,0.045);
}

#SidebarHeader {
    background-color: transparent;
}

#SidebarLogo {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.2px;
}

#SidebarVersion {
    color: #383A47;
    font-size: 10px;
    letter-spacing: 0.7px;
}

#SidebarDivider {
    background-color: rgba(255,255,255,0.05);
    max-height: 1px;
    border: none;
}

#SidebarSection {
    color: #383A47;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
}

/* ── Nav Buttons ── */
#NavBtn {
    background: transparent;
    color: #565869;
    text-align: left;
    padding: 9px 14px;
    border-radius: 8px;
    border: none;
    font-size: 13px;
    font-weight: 500;
}
#NavBtn:hover {
    background: rgba(255,255,255,0.04);
    color: #A0A3B3;
}
#NavBtnActive {
    background: rgba(124,92,252,0.13);
    color: #A78BFA;
    text-align: left;
    padding: 9px 14px;
    border-radius: 8px;
    border: none;
    font-size: 13px;
    font-weight: 600;
}
#NavBtnActive:hover {
    background: rgba(124,92,252,0.18);
}

/* ── Content area ── */
#ContentArea {
    background-color: #0D0E12;
}

/* ── Page titles ── */
#PageTitle {
    color: #F0F1F5;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.3px;
}
#PageSubtitle {
    color: #565869;
    font-size: 12px;
}

/* ── Cards ── */
#PrimaryCard {
    background-color: #16171D;
    border: 1px solid rgba(255,255,255,0.055);
    border-radius: 16px;
}
#SecondaryCard {
    background-color: #111318;
    border: 1px solid rgba(255,255,255,0.038);
    border-radius: 12px;
}
#AccentCard {
    background-color: #17152A;
    border: 1px solid rgba(124,92,252,0.18);
    border-radius: 16px;
}
#WarningCard {
    background-color: rgba(245,158,11,0.06);
    border: 1px solid rgba(245,158,11,0.16);
    border-radius: 10px;
}

/* ── Status pills ── */
#PillIdle {
    background: rgba(74,222,128,0.09);
    color: #4ADE80;
    font-size: 10px;
    font-weight: 700;
    padding: 5px 13px;
    border-radius: 100px;
    border: 1px solid rgba(74,222,128,0.2);
    letter-spacing: 1px;
}
#PillActive {
    background: rgba(239,68,68,0.11);
    color: #F87171;
    font-size: 10px;
    font-weight: 700;
    padding: 5px 13px;
    border-radius: 100px;
    border: 1px solid rgba(239,68,68,0.22);
    letter-spacing: 1px;
}

/* ── Inputs ── */
QLineEdit, QSpinBox {
    background: #1A1C23;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 9px;
    padding: 9px 14px;
    color: #E4E6EB;
    font-size: 13px;
    selection-background-color: #7C5CFC;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid rgba(124,92,252,0.55);
    background: #1E2029;
    outline: none;
}
QLineEdit[hasError="true"] {
    border: 1px solid rgba(239,68,68,0.5);
}
QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    border: none;
    width: 14px;
}

/* ── Primary gradient button ── */
#BtnPrimary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7C5CFC, stop:1 #9E7EFD);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 13px;
    border-radius: 10px;
    border: none;
    padding: 11px 22px;
    letter-spacing: 0.1px;
}
#BtnPrimary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6B4EDB, stop:1 #8D6FE8);
}
#BtnPrimary:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5A40C0, stop:1 #7A60D4);
}
#BtnPrimary:disabled {
    background: #21222A;
    color: #3A3C47;
}

/* ── Danger button ── */
#BtnDanger {
    background: rgba(239,68,68,0.11);
    color: #F87171;
    font-weight: 700;
    font-size: 13px;
    border-radius: 10px;
    border: 1px solid rgba(239,68,68,0.2);
    padding: 11px 22px;
}
#BtnDanger:hover {
    background: rgba(239,68,68,0.2);
    border-color: rgba(239,68,68,0.38);
    color: #FCA5A5;
}
#BtnDanger:pressed {
    background: rgba(239,68,68,0.28);
}

/* ── Secondary button ── */
#BtnSecondary {
    background: rgba(255,255,255,0.045);
    color: #8E919F;
    font-weight: 500;
    font-size: 13px;
    border-radius: 9px;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 9px 18px;
}
#BtnSecondary:hover {
    background: rgba(255,255,255,0.075);
    color: #C0C3D2;
}

/* ── Ghost button ── */
#BtnGhost {
    background: transparent;
    color: #50526A;
    border: none;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
}
#BtnGhost:hover {
    color: #9094A8;
    background: rgba(255,255,255,0.04);
}

/* ── Chip button ── */
#BtnChip {
    background: rgba(124,92,252,0.07);
    color: #8B6EE8;
    border: 1px solid rgba(124,92,252,0.14);
    border-radius: 100px;
    padding: 4px 13px;
    font-size: 11px;
    font-weight: 500;
}
#BtnChip:hover {
    background: rgba(124,92,252,0.14);
    border-color: rgba(124,92,252,0.28);
    color: #B09FFD;
}

/* ── Duration toggle buttons ── */
#DurationBtn {
    background: rgba(255,255,255,0.04);
    color: #565869;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
    min-width: 46px;
}
#DurationBtn:hover {
    background: rgba(255,255,255,0.07);
    color: #A0A3B3;
}
#DurationBtnActive {
    background: rgba(124,92,252,0.15);
    color: #C4B5FD;
    border: 1px solid rgba(124,92,252,0.3);
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 46px;
}

/* ── Remove button (inside list rows) ── */
#BtnRemove {
    background: transparent;
    color: #40424F;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
}
#BtnRemove:hover {
    background: rgba(239,68,68,0.09);
    color: #F87171;
    border-color: rgba(239,68,68,0.18);
}

/* ── Radio buttons ── */
QRadioButton {
    color: #7A7D90;
    font-size: 13px;
    spacing: 7px;
}
QRadioButton:checked { color: #C4B5FD; font-weight: 600; }
QRadioButton::indicator {
    width: 16px; height: 16px; border-radius: 8px;
    border: 2px solid #2E303C; background: transparent;
}
QRadioButton::indicator:checked {
    border-color: #7C5CFC; background: #7C5CFC;
}

/* ── Checkboxes ── */
QCheckBox { color: #C0C3D2; font-size: 13px; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 2px solid #2A2C38; background: transparent;
}
QCheckBox::indicator:checked {
    border-color: #7C5CFC; background: #7C5CFC;
}
QCheckBox::indicator:hover { border-color: #6245C8; }

/* ── Lists ── */
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    background: transparent;
    border: none;
    padding: 0;
    margin: 2px 0;
}
QListWidget::item:selected { background: transparent; }

/* ── Tables ── */
QTableWidget {
    background: #111318;
    border: 1px solid rgba(255,255,255,0.045);
    border-radius: 12px;
    gridline-color: rgba(255,255,255,0.035);
    outline: none;
    selection-background-color: rgba(124,92,252,0.12);
}
QTableWidget::item {
    padding: 9px 14px;
    border: none;
    color: #B0B3C5;
}
QTableWidget::item:selected {
    background: rgba(124,92,252,0.12);
    color: #E4E6EB;
}
QHeaderView::section {
    background: #15161D;
    color: #50526A;
    padding: 10px 14px;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.045);
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.9px;
}

/* ── Status bar ── */
QStatusBar {
    background: #0A0B0F;
    color: #383A47;
    border-top: 1px solid rgba(255,255,255,0.035);
    font-size: 11px;
}

/* ── Message box ── */
QMessageBox { background: #16171D; }
QMessageBox QLabel { color: #C4C6D6; background: transparent; }
QMessageBox QPushButton { border-radius: 7px; padding: 7px 18px; }
"""


# ─────────────────────────────────────────────────────────────────────────────
# MainWindow
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Premium main window with sidebar navigation and stacked content pages."""

    # nav items: (label, emoji, page_index)
    _NAV_ITEMS = [
        ("Dashboard",   "󰮯", 0),
        ("Websites",    "󰖟", 1),
        ("Statistics",  "󰈸", 2),
        ("Settings",    "󰒓", 3),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME}  ·  v{APP_VERSION}")
        self.resize(960, 660)
        self.setMinimumSize(800, 560)

        # ── Core services ──
        self.db = DatabaseManager()
        self.db.initialize()
        self.hosts = HostsManager()
        self.blocker = BlockerService(self.db, self.hosts)
        self.domain_manager = DomainManager(self.db)
        self.timer = BlockTimer(self)
        self.favicon_loader = FaviconLoader(self)

        self._nav_buttons: list[QPushButton] = []
        self._current_page = 0

        self._build_ui()
        self._wire_events()
        self._startup_recovery()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setStyleSheet(STYLESHEET)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content(), 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.setFixedHeight(28)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 22, 14, 22)
        layout.setSpacing(0)

        # Brand
        brand_label = QLabel(f"🛡️  {APP_NAME}")
        brand_label.setObjectName("SidebarLogo")
        layout.addWidget(brand_label)

        ver_label = QLabel(f"VERSION  {APP_VERSION}")
        ver_label.setObjectName("SidebarVersion")
        layout.addWidget(ver_label)

        layout.addSpacing(20)

        # Divider
        div = QFrame()
        div.setObjectName("SidebarDivider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)

        layout.addSpacing(16)

        # Nav section label
        nav_section = QLabel("NAVIGATION")
        nav_section.setObjectName("SidebarSection")
        layout.addWidget(nav_section)
        layout.addSpacing(8)

        # Nav buttons
        icons = ["📊", "🌐", "📈", "⚙️"]
        labels = ["Dashboard", "Websites", "Statistics", "Settings"]

        for idx, (icon, label) in enumerate(zip(icons, labels)):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("NavBtnActive" if idx == 0 else "NavBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(False)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            layout.addWidget(btn)
            layout.addSpacing(3)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Bottom divider + app info
        div2 = QFrame()
        div2.setObjectName("SidebarDivider")
        div2.setFrameShape(QFrame.HLine)
        layout.addWidget(div2)
        layout.addSpacing(10)

        footer = QLabel("Windows  ·  Python 3.13")
        footer.setObjectName("SidebarVersion")
        layout.addWidget(footer)

        return sidebar

    def _build_content(self) -> QWidget:
        container = QWidget()
        container.setObjectName("ContentArea")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()

        self.page_dashboard = DashboardWidget(
            db=self.db,
            blocker=self.blocker,
            domain_manager=self.domain_manager,
            timer=self.timer,
        )
        self.page_websites = WebsitesWidget(
            domain_manager=self.domain_manager,
            favicon_loader=self.favicon_loader,
        )
        self.page_statistics = StatisticsWidget(db=self.db)
        self.page_settings = SettingsWidget(db=self.db, hosts_manager=self.hosts)

        for page in (self.page_dashboard, self.page_websites,
                     self.page_statistics, self.page_settings):
            self.stack.addWidget(page)

        layout.addWidget(self.stack)
        return container

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, index: int) -> None:
        if index == self._current_page:
            return
        for i, btn in enumerate(self._nav_buttons):
            btn.setObjectName("NavBtnActive" if i == index else "NavBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._current_page = index
        self.stack.setCurrentIndex(index)

        if index == 0:
            self.page_dashboard.refresh_stats()
        elif index == 1:
            self.page_websites.refresh_list()
        elif index == 2:
            self.page_statistics.refresh_stats()

    # ------------------------------------------------------------------
    # Event wiring
    # ------------------------------------------------------------------

    def _wire_events(self) -> None:
        self.page_dashboard.session_started.connect(self._on_session_started)
        self.page_dashboard.session_stopped.connect(self._on_session_stopped)
        self.page_websites.websites_changed.connect(self._on_websites_changed)
        self.page_settings.history_cleared.connect(self._on_history_cleared)

    def _on_session_started(self, _duration: int) -> None:
        self.page_websites.set_locked(True)
        self.statusBar().showMessage(
            "🔴  Focus session active — websites are blocked", 6000
        )

    def _on_session_stopped(self) -> None:
        self.page_websites.set_locked(False)
        self.page_statistics.refresh_stats()
        self.statusBar().showMessage(
            "✅  Session ended — hosts file restored  ·  DNS flushed", 6000
        )

    def _on_websites_changed(self) -> None:
        self.page_dashboard.refresh_stats()

    def _on_history_cleared(self) -> None:
        self.page_dashboard.refresh_stats()
        self.page_statistics.refresh_stats()
        self.statusBar().showMessage("Session history cleared", 3000)

    # ------------------------------------------------------------------
    # Startup recovery
    # ------------------------------------------------------------------

    def _startup_recovery(self) -> None:
        # Prefetch favicons for all stored domains in the background
        all_domains = [w.domain for w in self.domain_manager.list_all()]
        if all_domains:
            self.favicon_loader.prefetch_all(all_domains)
            logger.info("Prefetching favicons for %d domain(s).", len(all_domains))

        recovered = self.blocker.recover_interrupted_session()
        if recovered:
            logger.info("Restoring session #%s into UI.", recovered.id)
            self.page_dashboard.restore_active_session(recovered)
            self.page_websites.set_locked(True)
            self.statusBar().showMessage(
                "⚠️  Resumed active session from previous run", 8000
            )
        else:
            self.statusBar().showMessage(f"{APP_NAME} is ready", 3000)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        if self.timer.is_running:
            reply = QMessageBox.question(
                self,
                "Session In Progress",
                "A focus session is currently running.\n\n"
                "Stop the session and unblock websites before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Yes:
                self.page_dashboard.stop_current_session(status="stopped")
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
