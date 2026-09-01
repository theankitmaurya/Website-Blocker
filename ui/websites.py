"""Websites management panel — premium rows with real favicons."""
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QFrame, QSizePolicy,
)

from core.domain_manager import DomainManager
from database.models import Website
from services.favicon_service import FaviconLoader
from ui.custom_widgets import FaviconWidget
from utils.validators import get_website_name
from utils.logger import get_logger

logger = get_logger(__name__)

_QUICK_DOMAINS = [
    "youtube.com", "instagram.com", "reddit.com",
    "twitter.com", "netflix.com", "tiktok.com",
]


# ─────────────────────────────────────────────────────────────────────────────
# Row widget
# ─────────────────────────────────────────────────────────────────────────────

class WebsiteRowWidget(QWidget):
    """
    Premium styled row:
      [Checkbox] ● [FaviconWidget] ● [Name + Domain Subtitle] ● [ENABLED/OFF badge] ● [Remove btn]

    FaviconWidget shows a letter-avatar immediately and upgrades to the real
    favicon once the async network fetch completes.
    """

    toggled = Signal(int, bool)
    deleted = Signal(int)

    def __init__(
        self,
        website: Website,
        loader: FaviconLoader,
        locked: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.website = website
        self.locked = locked
        self._loader = loader
        self._build()

    def _build(self) -> None:
        self.setObjectName("WebsiteRow")
        self.setStyleSheet("""
            #WebsiteRow {
                background: #16171D;
                border: 1px solid rgba(255,255,255,0.048);
                border-radius: 10px;
            }
            #WebsiteRow:hover {
                border-color: rgba(255,255,255,0.085);
                background: #18191F;
            }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(12)

        # ── Toggle Checkbox ──────────────────────────────────────────
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.website.enabled)
        self.checkbox.setEnabled(not self.locked)
        self.checkbox.toggled.connect(self._on_toggled)
        self.checkbox.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.checkbox)

        # ── Real favicon (async) ────────────────────────────────────
        favicon = FaviconWidget(self.website.domain, self._loader, size=36)
        lay.addWidget(favicon)

        # ── Website Name & Domain text column ───────────────────────
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.name_lbl = QLabel(self.website.display_name)
        self.name_lbl.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #E2E4EE;
            }
        """)

        self.domain_lbl = QLabel(self.website.domain)
        self.domain_lbl.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #5E6173;
            }
        """)

        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.domain_lbl)
        lay.addLayout(info_layout, 1)

        # ── Status badge ─────────────────────────────────────────────
        status_text = "ENABLED" if self.website.enabled else "OFF"
        status_color = "#22C55E" if self.website.enabled else "#383A47"
        self.status_lbl = QLabel(status_text)
        self.status_lbl.setStyleSheet(
            f"color:{status_color}; font-size:9px; font-weight:700; letter-spacing:0.8px;"
        )
        lay.addWidget(self.status_lbl)

        # ── Remove button ────────────────────────────────────────────
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("BtnRemove")
        self.remove_btn.setEnabled(not self.locked)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.clicked.connect(self._on_delete)
        lay.addWidget(self.remove_btn)

    def _on_toggled(self, checked: bool) -> None:
        color = "#22C55E" if checked else "#383A47"
        text = "ENABLED" if checked else "OFF"
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(
            f"color:{color}; font-size:9px; font-weight:700; letter-spacing:0.8px;"
        )
        if self.website.id is not None:
            self.toggled.emit(self.website.id, checked)

    def _on_delete(self) -> None:
        if self.website.id is not None:
            self.deleted.emit(self.website.id)


# ─────────────────────────────────────────────────────────────────────────────
# WebsitesWidget
# ─────────────────────────────────────────────────────────────────────────────

class WebsitesWidget(QWidget):
    websites_changed = Signal()

    def __init__(
        self,
        domain_manager: DomainManager,
        favicon_loader: FaviconLoader,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.domain_manager = domain_manager
        self.favicon_loader = favicon_loader
        self.is_locked = False
        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 26, 28, 26)
        main.setSpacing(18)

        # ── Page header ──────────────────────────────────────────────
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("Websites")
        lbl_title.setObjectName("PageTitle")
        lbl_sub = QLabel("Add and manage websites to block during focus sessions")
        lbl_sub.setObjectName("PageSubtitle")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        main.addLayout(title_col)

        # ── Session-active lock banner ────────────────────────────────
        self.lock_banner = QFrame()
        self.lock_banner.setObjectName("WarningCard")
        lock_lay = QHBoxLayout(self.lock_banner)
        lock_lay.setContentsMargins(14, 10, 14, 10)
        lock_lbl = QLabel(
            "🔒  A focus session is currently active. "
            "Websites cannot be modified until the session ends."
        )
        lock_lbl.setStyleSheet("color:#D97706; font-weight:600; font-size:12px;")
        lock_lay.addWidget(lock_lbl)
        self.lock_banner.setVisible(False)
        main.addWidget(self.lock_banner)

        # ── Add website card ──────────────────────────────────────────
        add_card = QFrame()
        add_card.setObjectName("SecondaryCard")
        add_lay = QVBoxLayout(add_card)
        add_lay.setContentsMargins(18, 16, 18, 16)
        add_lay.setSpacing(12)

        add_lbl = QLabel("ADD WEBSITE")
        add_lbl.setStyleSheet("color:#383A47; font-size:10px; font-weight:700; letter-spacing:0.9px;")
        add_lay.addWidget(add_lbl)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Paste a URL or domain — e.g. youtube.com or https://reddit.com/r/python"
        )
        self.input_field.setMinimumHeight(40)
        self.input_field.returnPressed.connect(self._on_add)
        input_row.addWidget(self.input_field, 1)

        self.add_btn = QPushButton("  +  Add  ")
        self.add_btn.setObjectName("BtnPrimary")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add)
        input_row.addWidget(self.add_btn)
        add_lay.addLayout(input_row)

        # Feedback label (hidden until needed)
        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setVisible(False)
        self.feedback_lbl.setStyleSheet("font-size:12px; font-weight:600;")
        add_lay.addWidget(self.feedback_lbl)

        # Quick-add chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        lbl_quick = QLabel("Quick add:")
        lbl_quick.setStyleSheet("color:#383A47; font-size:11px;")
        chips_row.addWidget(lbl_quick)
        for site in _QUICK_DOMAINS:
            chip = QPushButton(f"+ {get_website_name(site)}")
            chip.setObjectName("BtnChip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _, s=site: self._quick_add(s))
            chips_row.addWidget(chip)
        chips_row.addStretch()
        add_lay.addLayout(chips_row)

        main.addWidget(add_card)

        # ── List header ───────────────────────────────────────────────
        list_header = QHBoxLayout()
        self.count_lbl = QLabel("Configured Websites")
        self.count_lbl.setStyleSheet("font-size:13px; font-weight:700; color:#C0C3D2;")
        list_header.addWidget(self.count_lbl)
        list_header.addStretch()

        self.btn_all = QPushButton("Enable all")
        self.btn_all.setObjectName("BtnGhost")
        self.btn_all.clicked.connect(self._enable_all)
        list_header.addWidget(self.btn_all)

        self.btn_none = QPushButton("Disable all")
        self.btn_none.setObjectName("BtnGhost")
        self.btn_none.clicked.connect(self._disable_all)
        list_header.addWidget(self.btn_none)
        main.addLayout(list_header)

        # ── List widget ───────────────────────────────────────────────
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("WebsitesList")
        self.list_widget.setSpacing(3)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main.addWidget(self.list_widget, 1)

        # ── Empty state ───────────────────────────────────────────────
        self.empty_state = QFrame()
        empty_lay = QVBoxLayout(self.empty_state)
        empty_lay.setAlignment(Qt.AlignCenter)
        empty_icon = QLabel("🌐")
        empty_icon.setStyleSheet("font-size:40px;")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_msg = QLabel(
            "No websites configured yet.\n"
            "Add your first domain above to get started."
        )
        empty_msg.setStyleSheet("color:#383A47; font-size:13px;")
        empty_msg.setAlignment(Qt.AlignCenter)
        empty_lay.addWidget(empty_icon)
        empty_lay.addSpacing(8)
        empty_lay.addWidget(empty_msg)
        main.addWidget(self.empty_state)

    # ------------------------------------------------------------------
    # Locking
    # ------------------------------------------------------------------

    def set_locked(self, locked: bool) -> None:
        self.is_locked = locked
        self.lock_banner.setVisible(locked)
        self.input_field.setEnabled(not locked)
        self.add_btn.setEnabled(not locked)
        self.btn_all.setEnabled(not locked)
        self.btn_none.setEnabled(not locked)
        self.refresh_list()

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    def _show_feedback(self, text: str, error: bool = False) -> None:
        color = "#EF4444" if error else "#22C55E"
        self.feedback_lbl.setText(text)
        self.feedback_lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{color};")
        self.feedback_lbl.setVisible(True)

    # ------------------------------------------------------------------
    # Domain operations
    # ------------------------------------------------------------------

    def _quick_add(self, domain: str) -> None:
        if self.is_locked:
            return
        self.input_field.setText(domain)
        self._on_add()

    def _on_add(self) -> None:
        if self.is_locked:
            return
        text = self.input_field.text().strip()
        if not text:
            self._show_feedback("Please enter a website link or domain.", error=True)
            return

        result = self.domain_manager.add(text)
        if result.success:
            self.input_field.clear()
            site_name = get_website_name(result.domain or text)
            self._show_feedback(f"Added  '{site_name}'  ({result.domain})", error=False)
            # Pre-fetch the favicon in the background right away
            if result.domain:
                self.favicon_loader.request(result.domain)
            self.refresh_list()
            self.websites_changed.emit()
        elif result.error == "invalid":
            self._show_feedback(f"'{text}' is not a valid website link or domain.", error=True)
        elif result.error == "duplicate":
            site_name = get_website_name(result.domain or text)
            self._show_feedback(f"'{site_name}' ({result.domain}) is already in the list.", error=True)
        else:
            self._show_feedback("Could not add website.", error=True)

    def _on_row_toggled(self, wid: int, enabled: bool) -> None:
        if not self.is_locked:
            self.domain_manager.toggle(wid, enabled)
            self.websites_changed.emit()

    def _on_row_deleted(self, wid: int) -> None:
        if not self.is_locked:
            self.domain_manager.remove(wid)
            self.refresh_list()
            self.websites_changed.emit()

    def _enable_all(self) -> None:
        if self.is_locked:
            return
        for w in self.domain_manager.list_all():
            if w.id and not w.enabled:
                self.domain_manager.toggle(w.id, True)
        self.refresh_list()
        self.websites_changed.emit()

    def _disable_all(self) -> None:
        if self.is_locked:
            return
        for w in self.domain_manager.list_all():
            if w.id and w.enabled:
                self.domain_manager.toggle(w.id, False)
        self.refresh_list()
        self.websites_changed.emit()

    # ------------------------------------------------------------------
    # List refresh
    # ------------------------------------------------------------------

    def refresh_list(self) -> None:
        self.list_widget.clear()
        sites = self.domain_manager.list_all()

        has_sites = bool(sites)
        self.list_widget.setVisible(has_sites)
        self.empty_state.setVisible(not has_sites)

        enabled_count = sum(1 for s in sites if s.enabled)
        self.count_lbl.setText(
            f"Configured Websites  ·  {enabled_count}/{len(sites)} enabled"
            if sites else "Configured Websites"
        )

        for site in sites:
            row = WebsiteRowWidget(
                site,
                loader=self.favicon_loader,
                locked=self.is_locked,
            )
            row.toggled.connect(self._on_row_toggled)
            row.deleted.connect(self._on_row_deleted)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
