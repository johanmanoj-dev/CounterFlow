"""
CounterFlow v1.0.0 — Dashboard Screen
=======================================
Main overview screen shown on app startup.
Displays 6 stat cards and recent invoices table.
Matches approved CounterFlow design exactly.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.ui.components.stat_card import CounterFlowStatCard
from app.core.report_generator import CounterFlowReportGenerator
from app.core.inventory_manager import CounterFlowInventoryManager
from app.core.customer_manager import CounterFlowCustomerManager
from app import theme as t


class CounterFlowDashboardScreen(QWidget):
    """
    CounterFlow — Dashboard Screen.
    Shows daily summary cards and recent transactions.
    """

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session  = counterflow_session
        self.counterflow_reporter = CounterFlowReportGenerator(counterflow_session)
        self.counterflow_inventory = CounterFlowInventoryManager(counterflow_session)
        self.counterflow_customers = CounterFlowCustomerManager(counterflow_session)
        self._counterflow_build()

    def _counterflow_build(self):
        # ── Root layout — created exactly once on this widget ──
        counterflow_root = QVBoxLayout(self)
        counterflow_root.setContentsMargins(0, 0, 0, 0)

        self._counterflow_scroll = QScrollArea()
        self._counterflow_scroll.setWidgetResizable(True)
        self._counterflow_scroll.setFrameShape(QFrame.Shape.NoFrame)
        counterflow_root.addWidget(self._counterflow_scroll)

        # Build the scrollable content for the first time
        self._counterflow_build_content()

    def _counterflow_build_content(self):
        """CounterFlow — Build (or rebuild) the scrollable page content.

        Safe to call multiple times. Replaces the QScrollArea's inner
        widget so the root QVBoxLayout on self is never touched again.
        """
        counterflow_container = QWidget()
        counterflow_layout    = QVBoxLayout(counterflow_container)
        counterflow_layout.setContentsMargins(32, 28, 32, 28)
        counterflow_layout.setSpacing(24)

        # ── Greeting ───────────────────────────────────────────
        counterflow_greeting = self._counterflow_build_greeting()
        counterflow_layout.addWidget(counterflow_greeting)

        # ── Stat Cards Grid ────────────────────────────────────
        counterflow_cards_widget = self._counterflow_build_cards()
        counterflow_layout.addWidget(counterflow_cards_widget)

        # ── Recent Invoices ────────────────────────────────────
        counterflow_recent_label = QLabel("Recent Invoices")
        counterflow_recent_label.setStyleSheet(
            f"font-size: 16px; font-weight: 700; "
            f"color: {t.counterflow_theme()['text_primary']};"
        )
        counterflow_layout.addWidget(counterflow_recent_label)

        self._counterflow_invoice_table = self._counterflow_build_table()
        counterflow_layout.addWidget(self._counterflow_invoice_table)

        self._counterflow_scroll.setWidget(counterflow_container)

    def _counterflow_build_greeting(self) -> QWidget:
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(0, 0, 0, 0)
        counterflow_layout.setSpacing(4)

        counterflow_now  = datetime.now()
        counterflow_hour = counterflow_now.hour
        if counterflow_hour < 12:
            counterflow_greet = "Good morning"
        elif counterflow_hour < 17:
            counterflow_greet = "Good afternoon"
        else:
            counterflow_greet = "Good evening"

        counterflow_title = QLabel(f"{counterflow_greet}, Admin")
        counterflow_title_font = QFont("Segoe UI", 22)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_title.setStyleSheet(
            f"color: {t.counterflow_theme()['text_primary']};"
        )

        counterflow_sub = QLabel("Here's what's happening with your store today.")
        counterflow_sub.setStyleSheet(
            f"color: {t.counterflow_theme()['text_secondary']}; font-size: 13px;"
        )

        counterflow_layout.addWidget(counterflow_title)
        counterflow_layout.addWidget(counterflow_sub)
        return counterflow_widget

    def _counterflow_build_cards(self) -> QWidget:
        counterflow_widget = QWidget()
        counterflow_grid   = QGridLayout(counterflow_widget)
        counterflow_grid.setContentsMargins(0, 0, 0, 0)
        counterflow_grid.setSpacing(16)

        self._counterflow_card_sales    = CounterFlowStatCard("Today's Sales",       "₹0",    "$")
        self._counterflow_card_orders   = CounterFlowStatCard("Total Orders",        "0",     "🛒")
        self._counterflow_card_customers= CounterFlowStatCard("Active Customers",    "0",     "👤")
        self._counterflow_card_avg      = CounterFlowStatCard("Avg. Order Value",    "₹0",    "↗")
        self._counterflow_card_credit   = CounterFlowStatCard("Credit Outstanding",  "₹0",    "💳")
        self._counterflow_card_lowstock = CounterFlowStatCard("Low Stock Items",     "0",     "📦")

        counterflow_cards = [
            self._counterflow_card_sales,
            self._counterflow_card_orders,
            self._counterflow_card_customers,
            self._counterflow_card_avg,
            self._counterflow_card_credit,
            self._counterflow_card_lowstock,
        ]
        for i, card in enumerate(counterflow_cards):
            counterflow_grid.addWidget(card, i // 3, i % 3)

        return counterflow_widget

    def _counterflow_build_table(self) -> QTableWidget:
        counterflow_table = QTableWidget()
        counterflow_table.setColumnCount(5)
        counterflow_table.setHorizontalHeaderLabels(
            ["Invoice #", "Customer", "Total", "Payment", "Time"]
        )
        counterflow_table.setAlternatingRowColors(False)
        counterflow_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        counterflow_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        counterflow_table.setShowGrid(False)
        counterflow_table.verticalHeader().setVisible(False)
        counterflow_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        counterflow_table.setRowHeight(0, t.COUNTERFLOW_TABLE_ROW_HEIGHT)
        return counterflow_table

    # ── Public ─────────────────────────────────────────────────

    def counterflow_refresh(self):
        """CounterFlow — Refresh all dashboard data from DB."""
        thm = t.counterflow_theme()

        summary   = self.counterflow_reporter.counterflow_daily_summary()
        low_stock = self.counterflow_inventory.counterflow_get_low_stock_products()
        all_custs = len(self.counterflow_customers.counterflow_get_all_customers())

        avg_order = (
            summary["counterflow_total_sales"] / summary["counterflow_invoice_count"]
            if summary["counterflow_invoice_count"] > 0 else 0
        )
        outstanding = self.counterflow_reporter.counterflow_total_outstanding_credit()

        self._counterflow_card_sales.counterflow_set_value(
            f"₹{summary['counterflow_total_sales']:,.0f}"
        )
        self._counterflow_card_orders.counterflow_set_value(
            str(summary["counterflow_invoice_count"])
        )
        self._counterflow_card_customers.counterflow_set_value(str(all_custs))
        self._counterflow_card_avg.counterflow_set_value(f"₹{avg_order:,.2f}")
        self._counterflow_card_credit.counterflow_set_value(f"₹{outstanding:,.0f}")
        self._counterflow_card_lowstock.counterflow_set_value(str(len(low_stock)))

        # Recent invoices table
        recent = self.counterflow_reporter.counterflow_recent_invoices(limit=15)
        self._counterflow_invoice_table.setRowCount(len(recent))

        for row, inv in enumerate(recent):
            self._counterflow_invoice_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            customer_name = (
                inv.counterflow_customer.counterflow_name
                if inv.counterflow_customer else "Walk-in Customer"
            )
            time_str = self._counterflow_format_time(inv.counterflow_created_at)

            self._counterflow_invoice_table.setItem(
                row, 0,
                self._cf_item(inv.counterflow_invoice_number)
            )
            self._counterflow_invoice_table.setItem(
                row, 1,
                self._cf_item(customer_name)
            )
            self._counterflow_invoice_table.setItem(
                row, 2,
                self._cf_item(f"₹{inv.counterflow_total_amount:,.0f}")
            )

            # Payment badge
            badge_widget = self._counterflow_payment_badge(
                inv.counterflow_payment_method
            )
            self._counterflow_invoice_table.setCellWidget(row, 3, badge_widget)

            self._counterflow_invoice_table.setItem(
                row, 4,
                self._cf_item(time_str)
            )

    # ── Helpers ────────────────────────────────────────────────

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _counterflow_payment_badge(self, method: str) -> QWidget:
        thm = t.counterflow_theme()
        badge = QLabel(method)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if method == "UPI":
            bg, fg = thm["upi_light"], thm["upi_text"]
        elif method == "CASH":
            bg, fg = thm["cash_light"], thm["cash_text"]
        else:
            bg, fg = thm["warning_light"], thm["warning_text"]

        badge.setStyleSheet(f"""
            background: {bg};
            color: {fg};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        wrapper = QWidget()
        layout  = QHBoxLayout(wrapper)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(badge)
        return wrapper

    def _counterflow_format_time(self, dt: datetime) -> str:
        # Use utcnow() — all CounterFlow timestamps are stored as UTC
        now   = datetime.utcnow()
        delta = now - dt
        secs  = int(delta.total_seconds())
        if secs < 60:
            return "Just now"
        elif secs < 3600:
            return f"{secs // 60} min ago"
        elif secs < 86400:
            return f"{secs // 3600} hr ago"
        else:
            return dt.strftime("%d %b")

    def counterflow_refresh_theme(self):
        """CounterFlow — Rebuild scrollable content after theme change.

        Uses setWidget() on the persistent QScrollArea so the root
        QVBoxLayout on self is only ever created once — avoiding the
        Qt 'widget already has a layout' warning and the orphaned-
        stat-card bug that resulted from calling _counterflow_build()
        a second time.
        """
        self._counterflow_build_content()
        self.counterflow_refresh()
