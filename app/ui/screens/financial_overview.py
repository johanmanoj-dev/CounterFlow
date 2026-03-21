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
from app.config import COUNTERFLOW_CREDIT_NEAR_LIMIT_PCT


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
        counterflow_title_font = QFont("Segoe UI", 23)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # ── 5 Stat Cards ───────────────────────────────────────
        counterflow_cards_row = QHBoxLayout()
        counterflow_cards_row.setSpacing(16)

        self._counterflow_card_revenue  = CounterFlowStatCard("Total Revenue",   "₹0")
        self._counterflow_card_growth   = CounterFlowStatCard("Monthly Growth",  "—", )
        self._counterflow_card_cash     = CounterFlowStatCard("Cash Sales",      "₹0",)
        self._counterflow_card_upi      = CounterFlowStatCard("UPI Sales",       "₹0",)
        self._counterflow_card_credit   = CounterFlowStatCard("Credit Sales",    "₹0", )

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

        self._counterflow_credit_heading = QLabel("Outstanding Credit")
        self._counterflow_credit_heading.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {thm['text_primary']};"
        )
        counterflow_layout.addWidget(self._counterflow_credit_heading)

        # Use a card frame for the grey background
        self._counterflow_credit_card = QFrame()
        self._counterflow_credit_card.setStyleSheet(f"""
            QFrame {{
                background: {thm['bg_surface']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        credit_card_layout = QVBoxLayout(self._counterflow_credit_card)
        credit_card_layout.setContentsMargins(1, 1, 1, 1)
        credit_card_layout.setSpacing(0)

        self._counterflow_credit_table = QTableWidget()
        self._counterflow_credit_table.setColumnCount(5)
        self._counterflow_credit_table.setHorizontalHeaderLabels(
            ["Name", "Mobile", "Balance", "Limit", "Usage %"]
        )
        self._counterflow_credit_table.setShowGrid(True)
        self._counterflow_credit_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_credit_table.verticalHeader().setVisible(False)
        self._counterflow_credit_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_credit_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_credit_table.setColumnWidth(1, 145)
        self._counterflow_credit_table.setColumnWidth(2, 135)
        self._counterflow_credit_table.setColumnWidth(3, 135)
        self._counterflow_credit_table.setColumnWidth(4, 85)
        self._counterflow_credit_table.setStyleSheet("border: none; background: transparent;")
        
        credit_card_layout.addWidget(self._counterflow_credit_table)
        counterflow_layout.addWidget(self._counterflow_credit_card)
        return counterflow_widget

    def _counterflow_build_products_table(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(0, 0, 0, 0)
        counterflow_layout.setSpacing(12)

        self._counterflow_products_heading = QLabel("Top Products")
        self._counterflow_products_heading.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {thm['text_primary']};"
        )
        counterflow_layout.addWidget(self._counterflow_products_heading)

        # Use a card frame for the grey background
        self._counterflow_products_card = QFrame()
        self._counterflow_products_card.setStyleSheet(f"""
            QFrame {{
                background: {thm['bg_surface']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        products_card_layout = QVBoxLayout(self._counterflow_products_card)
        products_card_layout.setContentsMargins(1, 1, 1, 1)
        products_card_layout.setSpacing(0)

        self._counterflow_products_table = QTableWidget()
        self._counterflow_products_table.setColumnCount(3)
        self._counterflow_products_table.setHorizontalHeaderLabels(
            ["Product", "Units Sold", "Revenue"]
        )
        self._counterflow_products_table.setShowGrid(True)
        self._counterflow_products_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_products_table.verticalHeader().setVisible(False)
        self._counterflow_products_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_products_table.setColumnWidth(1, 130)
        self._counterflow_products_table.setColumnWidth(2, 140)
        self._counterflow_products_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_products_table.setStyleSheet("border: none; background: transparent;")
        
        products_card_layout.addWidget(self._counterflow_products_table)
        counterflow_layout.addWidget(self._counterflow_products_card)
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

        # Monthly Growth — compare this month with last month
        from datetime import date, timedelta
        today = date.today()
        first_this = today.replace(day=1)
        last_prev  = first_this - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        this_month_invs  = self.counterflow_reporter.counterflow_invoices_by_date_range(first_this, today)
        prev_month_invs  = self.counterflow_reporter.counterflow_invoices_by_date_range(first_prev, last_prev)
        this_total = sum(i.counterflow_total_amount for i in this_month_invs)
        prev_total = sum(i.counterflow_total_amount for i in prev_month_invs)
        if prev_total > 0:
            growth_pct = ((this_total - prev_total) / prev_total) * 100
            sign = "+" if growth_pct >= 0 else ""
            self._counterflow_card_growth.counterflow_set_value(f"{sign}{growth_pct:.1f}%")
        elif this_total > 0:
            self._counterflow_card_growth.counterflow_set_value("+100%")
        else:
            self._counterflow_card_growth.counterflow_set_value("—")

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
            if usage >= COUNTERFLOW_CREDIT_NEAR_LIMIT_PCT * 100:
                counterflow_bal_item.setForeground(QColor(thm["balance_high"]))
            counterflow_bal_item.setFont(
                QFont("Segoe UI", 16, QFont.Weight.Bold)
            )
            counterflow_bal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._counterflow_credit_table.setItem(row, 2, counterflow_bal_item)

            self._counterflow_credit_table.setItem(
                row, 3,
                self._cf_item(f"₹{c['counterflow_limit']:,.0f}")
            )
            self._counterflow_credit_table.setItem(
                row, 4,
                self._cf_item(f"{usage}%")
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

    def counterflow_refresh_theme(self):
        """CounterFlow — Restyle headings, stat cards, and rebuild tables
        after theme change so all colours are dark-mode-aware."""
        thm = t.counterflow_theme()
        self._counterflow_credit_heading.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {thm['text_primary']};"
        )
        self._counterflow_products_heading.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {thm['text_primary']};"
        )
        # Refresh stat cards
        for card in [
            self._counterflow_card_revenue,
            self._counterflow_card_growth,
            self._counterflow_card_cash,
            self._counterflow_card_upi,
            self._counterflow_card_credit,
        ]:
            card.counterflow_refresh_theme()
        self.counterflow_refresh()

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
