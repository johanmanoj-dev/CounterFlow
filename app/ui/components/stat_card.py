"""
CounterFlow v1.0.0 — Stat Card Component
==========================================
Reusable card widget used on Dashboard and
Financials screens. Shows a title, value,
icon, and optional change indicator.
Matches the approved CounterFlow design.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app import theme as counterflow_theme_module


class CounterFlowStatCard(QWidget):
    """
    CounterFlow — Stat Card Widget.

    Displays:
        - Title text (top left)
        - Icon (top right)
        - Value (large, center)
        - Change indicator (bottom, green/red)

    Usage:
        card = CounterFlowStatCard(
            counterflow_title="Today's Sales",
            counterflow_value="₹24,580",
            counterflow_icon="$",
            counterflow_change="+12.5% from yesterday",
            counterflow_change_positive=True,
        )
    """

    def __init__(
        self,
        counterflow_title:           str,
        counterflow_value:           str  = "—",
        counterflow_icon:            str  = "",
        counterflow_change:          str  = "",
        counterflow_change_positive: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._counterflow_title           = counterflow_title
        self._counterflow_change          = counterflow_change
        self._counterflow_change_positive = counterflow_change_positive

        self.setObjectName("counterflowCard")
        self.setMinimumHeight(126)
        self.setMinimumWidth(180)

        self._counterflow_build(
            counterflow_title,
            counterflow_value,
            counterflow_icon,
            counterflow_change,
            counterflow_change_positive,
        )
        self._counterflow_apply_style()

    def _counterflow_build(
        self,
        title,
        value,
        icon,
        change,
        change_positive,
    ):
        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(20, 16, 20, 16)
        counterflow_layout.setSpacing(4)

        # ── Row 1: Title (+ Icon if provided) ──────────────────
        counterflow_top_row = QHBoxLayout()
        counterflow_top_row.setContentsMargins(0, 0, 0, 0)

        self._counterflow_title_label = QLabel(title)
        self._counterflow_title_label.setObjectName("counterflowCardTitle")

        counterflow_top_row.addWidget(self._counterflow_title_label)
        counterflow_top_row.addStretch()

        if icon:
            self._counterflow_icon_label = QLabel(icon)
            self._counterflow_icon_label.setObjectName("counterflowCardIcon")
            self._counterflow_icon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            counterflow_top_row.addWidget(self._counterflow_icon_label)

        counterflow_layout.addLayout(counterflow_top_row)
        counterflow_layout.addSpacing(8)

        # ── Row 2: Value ───────────────────────────────────────
        self._counterflow_value_label = QLabel(value)
        self._counterflow_value_label.setObjectName("counterflowCardValue")

        counterflow_layout.addWidget(self._counterflow_value_label)

        # ── Row 3: Change Indicator ────────────────────────────
        if change:
            self._counterflow_change_label = QLabel(change)
            self._counterflow_change_label.setObjectName(
                "counterflowCardChangePos" if change_positive
                else "counterflowCardChangeNeg"
            )
            counterflow_layout.addWidget(self._counterflow_change_label)
        else:
            self._counterflow_change_label = None

        counterflow_layout.addStretch()

    # ── Public Update Methods ──────────────────────────────────

    def counterflow_set_value(self, value: str):
        """CounterFlow — Update the displayed value."""
        self._counterflow_value_label.setText(value)

    def counterflow_set_change(self, change: str, positive: bool = True):
        """CounterFlow — Update the change indicator text."""
        if self._counterflow_change_label:
            self._counterflow_change_label.setText(change)
            self._counterflow_change_label.setObjectName(
                "counterflowCardChangePos" if positive
                else "counterflowCardChangeNeg"
            )
            self._counterflow_apply_style()

    def counterflow_set_title(self, title: str):
        """CounterFlow — Update the card title."""
        self._counterflow_title_label.setText(title)

    def counterflow_refresh_theme(self):
        """CounterFlow — Reapply styles after theme change."""
        self._counterflow_apply_style()

    # ── Style ──────────────────────────────────────────────────

    def _counterflow_apply_style(self):
        t = counterflow_theme_module.counterflow_theme()
        self.setStyleSheet(f"""
            QWidget#counterflowCard {{
                background: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#counterflowCardTitle {{
                color: {t['text_primary']};
                font-size: 14px;
                font-weight: 800;
                letter-spacing: -0.5px;
            }}
            QLabel#counterflowCardIcon {{
                color: {t['text_secondary']};
                font-size: 5px;
            }}
            QLabel#counterflowCardValue {{
                color: {t['text_primary']};
                font-size: 20px;
                font-weight: 600;
            }}
            QLabel#counterflowCardChangePos {{
                color: {t['success']};
                font-size: 19px;
                font-weight: 500;
            }}
            QLabel#counterflowCardChangeNeg {{
                color: {t['danger']};
                font-size: 19px;
                font-weight: 500;
            }}
        """)
