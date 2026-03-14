"""
CounterFlow v1.0.0 — Financial Overview Screen
================================================
5 stat cards on top. Two side-by-side tables below:
Outstanding Credit (with progress bar) + Top Products.
Matches approved CounterFlow design exactly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.ui.components.stat_card import CounterFlowStatCard
from app.core.report_generator import CounterFlowReportGenerator
from app import theme as t


class CounterFlowFinancialScreen(QWidget):
    """CounterFlow — Financial Overview Screen."""

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session  = counterflow_session
        self.counterflow_reporter = CounterFlowReportGenerator(counterflow_session)
        self._counterflow_build()
        self.counterflow_refresh()

    def _counterflow_build(self):
        counterflow_scroll = QScrollArea()
        counterflow_scroll.setWidgetResizable(True)
        counterflow_scroll.setFrameShape(QFrame.Shape.NoFrame)

        counterflow_container = QWidget()
        counterflow_layout    = QVBoxLayout(counterflow_container)
        counterflow_layout.setContentsMargins(32, 28, 32, 28)
        counterflow_layout.setSpacing(24)

        # Title
        counterflow_title = QLabel("Financials")
        counterflow_title_font = QFont("Segoe UI", 20)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # ── 5 Stat Cards ───────────────────────────────────────
        counterflow_cards_row = QHBoxLayout()
        counterflow_cards_row.setSpacing(16)

        self._counterflow_card_revenue  = CounterFlowStatCard("Total Revenue",   "₹0", "$")
        self._counterflow_card_growth   = CounterFlowStatCard("Monthly Growth",  "—",  "↗")
        self._counterflow_card_cash     = CounterFlowStatCard("Cash Sales",      "₹0", "🗂")
        self._counterflow_card_upi      = CounterFlowStatCard("UPI Sales",       "₹0", "↗")
        self._counterflow_card_credit   = CounterFlowStatCard("Credit Sales",    "₹0", "💳")

        for card in [
            self._counterflow_card_revenue,
            self._counterflow_card_growth,
            self._counterflow_card_cash,
            self._counterflow_card_upi,
            self._counterflow_card_credit,
        ]:
            card.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )
            counterflow_cards_row.addWidget(card)

        counterflow_layout.addLayout(counterflow_cards_row)

        # ── Two tables side by side ────────────────────────────
        counterflow_tables_row = QHBoxLayout()
        counterflow_tables_row.setSpacing(24)

        # Outstanding Credit table
        counterflow_credit_section = self._counterflow_build_credit_table()
        counterflow_tables_row.addWidget(counterflow_credit_section, 50)

        # Top Products table
        counterflow_products_section = self._counterflow_build_products_table()
        counterflow_tables_row.addWidget(counterflow_products_section, 50)

        counterflow_layout.addLayout(counterflow_tables_row)
        counterflow_layout.addStretch()

        counterflow_scroll.setWidget(counterflow_container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(counterflow_scroll)

    def _counterflow_build_credit_table(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(0, 0, 0, 0)
        counterflow_layout.setSpacing(12)

        counterflow_heading = QLabel("Outstanding Credit")
        counterflow_heading.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {thm['text_primary']};"
        )
        counterflow_layout.addWidget(counterflow_heading)

        self._counterflow_credit_table = QTableWidget()
        self._counterflow_credit_table.setColumnCount(5)
        self._counterflow_credit_table.setHorizontalHeaderLabels(
            ["Name", "Mobile", "Balance", "Limit", "Usage %"]
        )
        self._counterflow_credit_table.setShowGrid(False)
        self._counterflow_credit_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_credit_table.verticalHeader().setVisible(False)
        self._counterflow_credit_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_credit_table.setColumnWidth(1, 110)
        self._counterflow_credit_table.setColumnWidth(2, 80)
        self._counterflow_credit_table.setColumnWidth(3, 70)
        self._counterflow_credit_table.setColumnWidth(4, 100)
        counterflow_layout.addWidget(self._counterflow_credit_table)
        return counterflow_widget

    def _counterflow_build_products_table(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(0, 0, 0, 0)
        counterflow_layout.setSpacing(12)

        counterflow_heading = QLabel("Top Products")
        counterflow_heading.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {thm['text_primary']};"
        )
        counterflow_layout.addWidget(counterflow_heading)

        self._counterflow_products_table = QTableWidget()
        self._counterflow_products_table.setColumnCount(3)
        self._counterflow_products_table.setHorizontalHeaderLabels(
            ["Product", "Units Sold", "Revenue"]
        )
        self._counterflow_products_table.setShowGrid(False)
        self._counterflow_products_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_products_table.verticalHeader().setVisible(False)
        self._counterflow_products_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        counterflow_layout.addWidget(self._counterflow_products_table)
        return counterflow_widget

    def counterflow_refresh(self):
        """CounterFlow — Reload all financial data from DB."""
        thm = t.counterflow_theme()
        # All-time totals for the revenue stat cards
        all_time = self.counterflow_reporter.counterflow_all_time_summary()
        credits  = self.counterflow_reporter.counterflow_outstanding_credit_summary()
        products = self.counterflow_reporter.counterflow_top_selling_products(limit=10)

        # Cards — use lifetime figures so "Total Revenue" is genuinely all-time
        self._counterflow_card_revenue.counterflow_set_value(
            f"₹{all_time['counterflow_total_sales']:,.0f}"
        )
        self._counterflow_card_cash.counterflow_set_value(
            f"₹{all_time['counterflow_cash_sales']:,.0f}"
        )
        self._counterflow_card_upi.counterflow_set_value(
            f"₹{all_time['counterflow_upi_sales']:,.0f}"
        )
        self._counterflow_card_credit.counterflow_set_value(
            f"₹{all_time['counterflow_credit_sales']:,.0f}"
        )

        # Outstanding Credit table
        self._counterflow_credit_table.setRowCount(len(credits))
        for row, c in enumerate(credits):
            self._counterflow_credit_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_credit_table.setItem(
                row, 0, self._cf_item(c["counterflow_name"])
            )
            self._counterflow_credit_table.setItem(
                row, 1, self._cf_item(c["counterflow_mobile"])
            )
            # Balance colored
            counterflow_bal_item = QTableWidgetItem(
                f"₹{c['counterflow_balance']:,.0f}"
            )
            counterflow_bal_item.setFlags(
                counterflow_bal_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            usage = c["counterflow_usage_percent"]
            if usage >= 80:
                counterflow_bal_item.setForeground(QColor(thm["balance_high"]))
            elif usage >= 40:
                counterflow_bal_item.setForeground(QColor(thm["balance_low"]))
            else:
                counterflow_bal_item.setForeground(QColor(thm["balance_zero"]))
            self._counterflow_credit_table.setItem(row, 2, counterflow_bal_item)

            self._counterflow_credit_table.setItem(
                row, 3,
                self._cf_item(f"₹{c['counterflow_limit']:,.0f}")
            )

            # Progress bar for usage %
            counterflow_progress = QProgressBar()
            counterflow_progress.setValue(int(usage))
            counterflow_progress.setTextVisible(False)
            counterflow_progress.setFixedHeight(8)
            if usage >= 80:
                color = thm["balance_high"]
            elif usage >= 40:
                color = thm["balance_low"]
            else:
                color = thm["balance_zero"]
            counterflow_progress.setStyleSheet(f"""
                QProgressBar {{
                    background: {thm['border']};
                    border-radius: 4px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {color};
                    border-radius: 4px;
                }}
            """)
            counterflow_pct_label = QLabel(f"{usage}%")
            counterflow_pct_label.setStyleSheet(
                f"color: {thm['text_secondary']}; font-size: 11px;"
            )
            counterflow_progress_widget = QWidget()
            counterflow_progress_layout = QVBoxLayout(counterflow_progress_widget)
            counterflow_progress_layout.setContentsMargins(4, 0, 4, 0)
            counterflow_progress_layout.setSpacing(2)
            counterflow_progress_layout.addWidget(counterflow_progress)
            counterflow_progress_layout.addWidget(counterflow_pct_label)
            self._counterflow_credit_table.setCellWidget(
                row, 4, counterflow_progress_widget
            )

        # Top Products table
        self._counterflow_products_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self._counterflow_products_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_products_table.setItem(
                row, 0, self._cf_item(p["counterflow_name"])
            )
            self._counterflow_products_table.setItem(
                row, 1, self._cf_item(str(p["counterflow_units_sold"]))
            )
            self._counterflow_products_table.setItem(
                row, 2,
                self._cf_item(p["counterflow_display_revenue"])
            )

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
