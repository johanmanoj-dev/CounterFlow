"""
CounterFlow v1.0.0 — Sidebar Navigation Component
===================================================
Left sidebar with logo + app name on same line,
navigation items with icons, dark mode toggle,
and "by CN-6" at the very bottom center.
Matches approved CounterFlow design exactly.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QCursor

from app import theme as counterflow_theme_module
from app.config import (
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_ICONS_DIR,
)

# ── CounterFlow Navigation Items ──────────────────────────────
# Base items visible to ALL roles
COUNTERFLOW_NAV_ITEMS_BASE = [
    ("counterflow_dashboard",        "dashboard",  "Dashboard"),
    ("counterflow_new_bill",         "new_bill",   "New Bill"),
    ("counterflow_inventory",        "inventory",  "Inventory"),
    ("counterflow_customers",        "customers",  "Customers"),
    ("counterflow_sales_history",    "sales",      "Sales History"),
    ("counterflow_financials",       "financials", "Financials"),
    ("counterflow_database_records", "database",   "Database & Records"),
]

# Admin-only items appended below the base list
COUNTERFLOW_NAV_ITEMS_ADMIN = [
    ("counterflow_staff_management", "staff",  "Staff Management"),
    ("counterflow_activity_logs",    "logs",   "Activity Logs"),
]

# ── CounterFlow Nav Icons (unicode fallback) ──────────────────
COUNTERFLOW_NAV_ICONS = {
    "dashboard":  "⊞",
    "new_bill":   "☰",
    "inventory":  "◎",
    "customers":  "⊕",
    "sales":      "↻",
    "financials": "$",
    "database":   "⊡",
    "staff":      "👤",
    "logs":       "📋",
}


# ──────────────────────────────────────────────────────────────
class CounterFlowNavButton(QPushButton):
    """
    CounterFlow — Single navigation button in the sidebar.
    Shows icon + label side by side.
    Has normal, hover, and active states.
    """

    def __init__(self, icon_key: str, label: str, parent=None):
        super().__init__(parent)
        self.counterflow_icon_key = icon_key
        self.counterflow_label    = label
        self.counterflow_active   = False

        self.setText(f"  {label}")
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(counterflow_theme_module.COUNTERFLOW_NAV_ITEM_HEIGHT)
        self.setMinimumWidth(counterflow_theme_module.COUNTERFLOW_SIDEBAR_WIDTH - 24)

        self._counterflow_apply_style()

    def _counterflow_apply_style(self):
        t = counterflow_theme_module.counterflow_theme()
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['text_sidebar']};
                border: none;
                border-radius: 8px;
                padding: 0px 14px;
                text-align: left;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['hover']};
                color: {t['text_sidebar_active']};
            }}
            QPushButton:checked {{
                background: {t['active_bg']};
                color: {t['text_sidebar_active']};
                font-weight: 600;
            }}
        """)

    def counterflow_refresh_style(self):
        """CounterFlow — Reapply style after theme change."""
        self._counterflow_apply_style()


# ──────────────────────────────────────────────────────────────
class CounterFlowSidebar(QWidget):
    """
    CounterFlow — Main Sidebar Navigation Widget.

    Layout:
        TOP    → Logo + App name (same line) + subtitle
        MIDDLE → Navigation buttons
        BOTTOM → Dark mode toggle + "by CN-6"

    Signals:
        counterflow_page_changed(str) — emitted when nav item clicked
        counterflow_dark_mode_toggled(bool) — emitted on dark mode toggle
    """

    counterflow_page_changed      = pyqtSignal(str)
    counterflow_dark_mode_toggled = pyqtSignal(bool)
    counterflow_logout_requested  = pyqtSignal()

    def __init__(self, is_admin: bool = False, parent=None):
        super().__init__(parent)
        self._counterflow_is_admin    = is_admin
        self._counterflow_buttons: dict[str, CounterFlowNavButton] = {}
        self._counterflow_active_key: str = None
        self._counterflow_dividers: list = []

        # Build nav list based on role
        self._counterflow_nav_items = list(COUNTERFLOW_NAV_ITEMS_BASE)
        if is_admin:
            self._counterflow_nav_items += COUNTERFLOW_NAV_ITEMS_ADMIN

        self.setObjectName("counterflowSidebar")
        self.setFixedWidth(counterflow_theme_module.COUNTERFLOW_SIDEBAR_WIDTH)
        self._counterflow_build()
        self._counterflow_apply_sidebar_style()

    # ── Build ──────────────────────────────────────────────────

    def _counterflow_build(self):
        counterflow_root = QVBoxLayout(self)
        counterflow_root.setContentsMargins(12, 0, 12, 0)
        counterflow_root.setSpacing(0)

        # ── Header: Logo + Name ────────────────────────────────
        counterflow_header = self._counterflow_build_header()
        counterflow_root.addWidget(counterflow_header)
        counterflow_root.addSpacing(8)

        # ── Navigation Items ───────────────────────────────────
        for counterflow_key, counterflow_icon, counterflow_label in self._counterflow_nav_items:
            # Insert visual section divider before admin-only items
            if counterflow_key == "counterflow_staff_management":
                counterflow_root.addSpacing(6)
                admin_div = self._counterflow_divider()
                self._counterflow_dividers.append(admin_div)
                counterflow_root.addWidget(admin_div)
                admin_section_lbl = QLabel("  ADMIN")
                admin_section_lbl.setObjectName("cfAdminSectionLabel")
                admin_section_lbl.setStyleSheet(
                    "color: #6b7280; font-size: 10px; font-weight: 700; "
                    "letter-spacing: 1.2px; background: transparent; border: none; "
                    "padding-left: 14px; padding-top: 6px; padding-bottom: 2px;"
                )
                counterflow_root.addWidget(admin_section_lbl)

            counterflow_btn = CounterFlowNavButton(
                icon_key=counterflow_icon,
                label=counterflow_label,
            )
            counterflow_btn.clicked.connect(
                lambda checked, k=counterflow_key: self._counterflow_on_nav_click(k)
            )
            counterflow_root.addWidget(counterflow_btn)
            counterflow_root.addSpacing(2)
            self._counterflow_buttons[counterflow_key] = counterflow_btn

        # ── Spacer ─────────────────────────────────────────────
        counterflow_root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Bottom divider ─────────────────────────────────────
        counterflow_div2 = self._counterflow_divider()
        self._counterflow_dividers.append(counterflow_div2)
        counterflow_root.addWidget(counterflow_div2)
        counterflow_root.addSpacing(8)

        # ── Logout Button ──────────────────────────────────────
        counterflow_logout_btn = self._counterflow_build_logout_btn()
        counterflow_root.addWidget(counterflow_logout_btn)
        counterflow_root.addSpacing(4)

        # ── Dark Mode Toggle ───────────────────────────────────
        counterflow_dark_btn = self._counterflow_build_dark_toggle()
        counterflow_root.addWidget(counterflow_dark_btn)
        counterflow_root.addSpacing(8)

        # ── "by CN-6" bottom center ────────────────────────────
        counterflow_credit = self._counterflow_build_credit()
        counterflow_root.addWidget(counterflow_credit)
        counterflow_root.addSpacing(12)

    def _counterflow_build_header(self) -> QWidget:
        """
        CounterFlow — Builds the logo + name header.
        Logo and name are on the SAME horizontal line.
        """
        counterflow_header = QWidget()
        counterflow_header.setFixedHeight(68)
        counterflow_header.setStyleSheet("background: transparent; border: none;")
        counterflow_layout = QHBoxLayout(counterflow_header)
        counterflow_layout.setContentsMargins(4, 14, 4, 0)
        counterflow_layout.setSpacing(10)

        # Logo
        self._counterflow_logo_label = QLabel()
        self._counterflow_logo_label.setFixedSize(
            counterflow_theme_module.COUNTERFLOW_LOGO_SIZE,
            counterflow_theme_module.COUNTERFLOW_LOGO_SIZE
        )
        self._counterflow_load_logo()

        # Name only
        self._counterflow_name_label = QLabel("CounterFlow POS")
        counterflow_name_font = QFont("Segoe UI", 14)
        counterflow_name_font.setWeight(QFont.Weight.Bold)
        self._counterflow_name_label.setFont(counterflow_name_font)
        self._counterflow_name_label.setStyleSheet("background: transparent; border: none;")

        counterflow_layout.addWidget(self._counterflow_logo_label)
        counterflow_layout.addWidget(self._counterflow_name_label)
        counterflow_layout.addStretch()

        return counterflow_header

    def _counterflow_load_logo(self):
        """CounterFlow — Load logo image into the logo label."""
        counterflow_logo_path = os.path.join(
            COUNTERFLOW_ICONS_DIR,
            "counterflow_logo.png"
        )
        size = counterflow_theme_module.COUNTERFLOW_LOGO_SIZE

        if os.path.exists(counterflow_logo_path):
            counterflow_pix = QPixmap(counterflow_logo_path).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._counterflow_logo_label.setPixmap(counterflow_pix)
        else:
            self._counterflow_logo_label.setText("CF")
            self._counterflow_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._counterflow_logo_label.setStyleSheet("""
                background: #111827;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            """)

    def _counterflow_build_logout_btn(self) -> QPushButton:
        """CounterFlow — Logout button at bottom of sidebar."""
        self._counterflow_logout_btn = QPushButton("  ⏻   Logout")
        self._counterflow_logout_btn.setFixedHeight(
            counterflow_theme_module.COUNTERFLOW_NAV_ITEM_HEIGHT
        )
        self._counterflow_logout_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self._counterflow_logout_btn.clicked.connect(
            lambda: self.counterflow_logout_requested.emit()
        )
        self._counterflow_apply_logout_btn_style()
        return self._counterflow_logout_btn

    def _counterflow_build_dark_toggle(self) -> QPushButton:
        """CounterFlow — Dark mode toggle button at bottom of sidebar."""
        self._counterflow_dark_btn = QPushButton("  ☾   Dark Mode")
        self._counterflow_dark_btn.setCheckable(True)
        self._counterflow_dark_btn.setFixedHeight(
            counterflow_theme_module.COUNTERFLOW_NAV_ITEM_HEIGHT
        )
        self._counterflow_dark_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self._counterflow_dark_btn.clicked.connect(
            self._counterflow_on_dark_toggle
        )
        self._counterflow_apply_dark_btn_style()
        return self._counterflow_dark_btn

    def _counterflow_build_credit(self) -> QLabel:
        """CounterFlow — 'by CN-6' label at bottom center."""
        self._counterflow_credit_label = QLabel("CounterFlow POS v1.0.0 by CN-6")
        self._counterflow_credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_apply_credit_style()
        return self._counterflow_credit_label

    def _counterflow_divider(self) -> QFrame:
        counterflow_line = QFrame()
        counterflow_line.setFrameShape(QFrame.Shape.HLine)
        counterflow_line.setFixedHeight(1)
        t = counterflow_theme_module.counterflow_theme()
        counterflow_line.setStyleSheet(
            f"background: {t['border']}; border: none;"
        )
        return counterflow_line

    # ── Event Handlers ─────────────────────────────────────────

    def _counterflow_on_nav_click(self, key: str):
        """CounterFlow — Handle navigation button click."""
        for k, btn in self._counterflow_buttons.items():
            btn.setChecked(k == key)
        self._counterflow_active_key = key
        self.counterflow_page_changed.emit(key)

    def _counterflow_on_dark_toggle(self, checked: bool):
        """CounterFlow — Handle dark mode toggle."""
        counterflow_theme_module.counterflow_set_dark(checked)
        self.counterflow_dark_mode_toggled.emit(checked)
        self._counterflow_apply_dark_btn_style()

    # ── Public Methods ─────────────────────────────────────────

    def counterflow_set_active(self, key: str):
        """CounterFlow — Programmatically set active nav item."""
        self._counterflow_on_nav_click(key)

    def counterflow_refresh_theme(self):
        """CounterFlow — Reapply all styles after theme change."""
        self._counterflow_apply_sidebar_style()
        self._counterflow_apply_logout_btn_style()
        self._counterflow_apply_dark_btn_style()
        self._counterflow_apply_credit_style()
        self._counterflow_load_logo()
        t = counterflow_theme_module.counterflow_theme()
        for div in self._counterflow_dividers:
            div.setStyleSheet(f"background: {t['border']}; border: none;")
        for btn in self._counterflow_buttons.values():
            btn.counterflow_refresh_style()

    # ── Style Helpers ──────────────────────────────────────────

    def _counterflow_apply_sidebar_style(self):
        t = counterflow_theme_module.counterflow_theme()
        self.setStyleSheet(f"""
            QWidget#counterflowSidebar {{
                background: {t['bg_sidebar']};
                border-right: 1px solid {t['sidebar_border']};
            }}
            QWidget#counterflowSidebar > QWidget {{
                background: transparent;
                border: none;
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {t['text_primary']};
            }}
        """)

    def _counterflow_apply_logout_btn_style(self):
        t = counterflow_theme_module.counterflow_theme()
        self._counterflow_logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['danger']};
                border: none;
                border-radius: 8px;
                padding: 0px 14px;
                text-align: left;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {t['danger_light']};
                color: {t['danger']};
            }}
        """)

    def _counterflow_apply_dark_btn_style(self):
        t = counterflow_theme_module.counterflow_theme()
        icon = "☀" if counterflow_theme_module.counterflow_is_dark() else "☾"
        label = "Light Mode" if counterflow_theme_module.counterflow_is_dark() else "Dark Mode"
        self._counterflow_dark_btn.setText(f"  {icon}   {label}")
        self._counterflow_dark_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['text_secondary']};
                border: none;
                border-radius: 8px;
                padding: 0px 14px;
                text-align: left;
                font-size: 14px;
                font-weight: 400;
            }}
            QPushButton:hover {{
                background: {t['hover']};
                color: {t['text_primary']};
            }}
        """)

    def _counterflow_apply_credit_style(self):
        t = counterflow_theme_module.counterflow_theme()
        self._counterflow_credit_label.setStyleSheet(f"""
            color: {t['text_secondary']};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
