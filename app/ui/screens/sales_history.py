"""
CounterFlow v1.0.0 — Sales History Screen
==========================================
Split panel. Left: invoice list with search.
Right: invoice detail.
Click any invoice to see its line items and grand total.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.report_generator import CounterFlowReportGenerator
from app import theme as t


class CounterFlowSalesHistoryScreen(QWidget):
    """CounterFlow — Sales History Screen."""

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session  = counterflow_session
        self.counterflow_reporter = CounterFlowReportGenerator(counterflow_session)
        self._counterflow_invoices = []
        self._counterflow_build()
        self.counterflow_refresh()

    def _counterflow_build(self):
        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(32, 28, 32, 28)
        counterflow_layout.setSpacing(20)

        counterflow_title = QLabel("Sales History")
        counterflow_title_font = QFont("Segoe UI", 23)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # ── Splitter ───────────────────────────────────────────
        counterflow_splitter = QSplitter(Qt.Orientation.Horizontal)
        counterflow_splitter.setHandleWidth(6)
        counterflow_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
            QSplitter::handle:hover {
                background-color: #d1d5db; /* subtle indicator on hover */
            }
            QSplitter::handle:pressed {
                background-color: #9ca3af; /* stronger when dragging */
            }
        """)

        # Left: Invoice list
        counterflow_left = self._counterflow_build_invoice_list()
        counterflow_splitter.addWidget(counterflow_left)

        # Right: Invoice detail
        counterflow_right = self._counterflow_build_invoice_detail()
        counterflow_splitter.addWidget(counterflow_right)

        counterflow_splitter.setSizes([520, 560])
        counterflow_layout.addWidget(counterflow_splitter, 1)

    def _counterflow_build_invoice_list(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(0, 0, 8, 0)
        counterflow_layout.setSpacing(10)

        # ── Search bar ─────────────────────────────────────────
        self._counterflow_search_input = QLineEdit()
        self._counterflow_search_input.setPlaceholderText(
            "  Search by invoice number..."
        )
        self._counterflow_search_input.setMinimumHeight(46)
        self._counterflow_search_input.textChanged.connect(
            self._counterflow_on_search
        )
        counterflow_layout.addWidget(self._counterflow_search_input)

        # Wrap table in a card-like frame
        self._counterflow_list_card = QFrame()
        self._counterflow_list_card.setObjectName("counterflowListCard")
        self._counterflow_list_card.setStyleSheet(f"""
            QFrame#counterflowListCard {{
                background: {thm['card_bg']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self._counterflow_list_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self._counterflow_invoice_table = QTableWidget()
        self._counterflow_invoice_table.setColumnCount(4)
        self._counterflow_invoice_table.setHorizontalHeaderLabels(
            ["Invoice #", "Customer", "Total", "Date"]
        )
        self._counterflow_invoice_table.setShowGrid(False)
        self._counterflow_invoice_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_invoice_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._counterflow_invoice_table.verticalHeader().setVisible(False)
        self._counterflow_invoice_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_invoice_table.setColumnWidth(0, 135)
        self._counterflow_invoice_table.setColumnWidth(2, 115)
        self._counterflow_invoice_table.setColumnWidth(3, 175)
        self._counterflow_invoice_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: transparent;
            }
        """)
        self._counterflow_invoice_table.currentCellChanged.connect(
            self._counterflow_on_invoice_selected
        )
        card_layout.addWidget(self._counterflow_invoice_table)

        counterflow_layout.addWidget(self._counterflow_list_card)
        return counterflow_widget

    def _counterflow_build_invoice_detail(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_widget = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_widget)
        counterflow_layout.setContentsMargins(8, 0, 0, 0)
        counterflow_layout.setSpacing(16)

        # Detail header row: title + payment badge
        counterflow_header_row = QHBoxLayout()
        counterflow_header_row.setSpacing(12)
        self._counterflow_detail_title = QLabel("Select an invoice to view details")
        counterflow_detail_font = QFont("Segoe UI", 18)
        counterflow_detail_font.setWeight(QFont.Weight.Bold)
        self._counterflow_detail_title.setFont(counterflow_detail_font)
        counterflow_header_row.addWidget(self._counterflow_detail_title)

        self._counterflow_detail_payment_badge = QLabel()
        self._counterflow_detail_payment_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_detail_payment_badge.setFixedHeight(32)
        self._counterflow_detail_payment_badge.setVisible(False)
        counterflow_header_row.addWidget(self._counterflow_detail_payment_badge)
        counterflow_header_row.addStretch()
        counterflow_layout.addLayout(counterflow_header_row)

        # Detail card
        self._counterflow_detail_card = QFrame()
        self._counterflow_detail_card.setObjectName("counterflowDetailCard")
        self._counterflow_detail_card.setStyleSheet(f"""
            QFrame#counterflowDetailCard {{
                background: {thm['card_bg']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self._counterflow_detail_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self._counterflow_items_table = QTableWidget()
        self._counterflow_items_table.setColumnCount(4)
        self._counterflow_items_table.setHorizontalHeaderLabels(
            ["Product", "Price", "Qty", "Subtotal"]
        )
        self._counterflow_items_table.setShowGrid(False)
        self._counterflow_items_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_items_table.verticalHeader().setVisible(False)
        self._counterflow_items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_items_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: transparent;
            }
        """)
        card_layout.addWidget(self._counterflow_items_table)

        # Divider line above grand total
        counterflow_divider = QFrame()
        counterflow_divider.setFrameShape(QFrame.Shape.HLine)
        counterflow_divider.setFixedHeight(1)
        counterflow_divider.setStyleSheet(f"background: {thm['border']}; border: none;")
        card_layout.addWidget(counterflow_divider)

        # Grand total row (inside the card)
        counterflow_total_row = QHBoxLayout()
        counterflow_total_row.setContentsMargins(16, 4, 16, 4)
        self._counterflow_total_lbl = QLabel("Grand Total")
        self._counterflow_total_lbl.setStyleSheet(
            f"font-weight: 700; font-size: 17px; color: {thm['text_primary']};"
        )
        self._counterflow_grand_total = QLabel("\u2014")
        self._counterflow_grand_total.setStyleSheet(
            f"font-weight: 700; font-size: 18px; color: {thm['text_primary']};"
        )
        self._counterflow_grand_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        counterflow_total_row.addWidget(self._counterflow_total_lbl)
        counterflow_total_row.addStretch()
        counterflow_total_row.addWidget(self._counterflow_grand_total)
        card_layout.addLayout(counterflow_total_row)

        counterflow_layout.addWidget(self._counterflow_detail_card)

        return counterflow_widget

    # ── Data ───────────────────────────────────────────────────

    def counterflow_refresh(self):
        """CounterFlow \u2014 Reload invoice list from DB."""
        self._counterflow_invoices = self.counterflow_reporter.counterflow_recent_invoices(
            limit=100
        )
        self._counterflow_search_input.clear()
        self._counterflow_populate_table(self._counterflow_invoices)

    def _counterflow_populate_table(self, invoices: list):
        """CounterFlow \u2014 Fill the invoice table with given invoice list."""
        self._counterflow_displayed = invoices
        self._counterflow_invoice_table.setRowCount(len(invoices))

        for row, inv in enumerate(invoices):
            self._counterflow_invoice_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            customer_name = (
                inv.counterflow_customer.counterflow_name
                if inv.counterflow_customer else "Walk-in"
            )
            self._counterflow_invoice_table.setItem(
                row, 0, self._cf_item(inv.counterflow_invoice_number)
            )
            self._counterflow_invoice_table.setItem(
                row, 1, self._cf_item(customer_name)
            )
            self._counterflow_invoice_table.setItem(
                row, 2,
                self._cf_item(f"\u20b9{inv.counterflow_total_amount:,.0f}")
            )
            self._counterflow_invoice_table.setItem(
                row, 3,
                self._cf_item(
                    inv.counterflow_created_at.strftime("%d %b %Y %I:%M %p")
                )
            )

    def _counterflow_on_search(self, text: str):
        """CounterFlow \u2014 Filter invoices by invoice number as user types."""
        query = text.strip().upper()
        if not query:
            self._counterflow_populate_table(self._counterflow_invoices)
            return
        filtered = [
            inv for inv in self._counterflow_invoices
            if query in inv.counterflow_invoice_number.upper()
        ]
        self._counterflow_populate_table(filtered)

    # ── Detail ─────────────────────────────────────────────────

    def _counterflow_on_invoice_selected(self, row, *_):
        """CounterFlow \u2014 Load invoice detail when row is clicked."""
        displayed = getattr(self, '_counterflow_displayed', self._counterflow_invoices)
        if row < 0 or row >= len(displayed):
            return

        inv = displayed[row]
        self._counterflow_detail_title.setText(
            f"Invoice Detail: {inv.counterflow_invoice_number}"
        )

        # Show payment method badge
        thm = t.counterflow_theme()
        method = inv.counterflow_payment_method
        if method == "UPI":
            bg, fg = thm["upi_light"], thm["upi_text"]
        elif method == "CASH":
            bg, fg = thm["cash_light"], thm["cash_text"]
        else:
            bg, fg = thm["warning_light"], thm["warning_text"]
        self._counterflow_detail_payment_badge.setText(method)
        self._counterflow_detail_payment_badge.setStyleSheet(f"""
            background: {bg}; color: {fg};
            border-radius: 10px; padding: 2px 14px;
            font-size: 15px; font-weight: 600;
        """)
        self._counterflow_detail_payment_badge.setVisible(True)

        counterflow_items = inv.counterflow_items
        self._counterflow_items_table.setRowCount(len(counterflow_items))

        for r, item in enumerate(counterflow_items):
            self._counterflow_items_table.setRowHeight(
                r, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_items_table.setItem(
                r, 0,
                self._cf_item(item.counterflow_product.counterflow_name)
            )
            self._counterflow_items_table.setItem(
                r, 1,
                self._cf_item(f"\u20b9{item.counterflow_unit_price:,.2f}")
            )
            self._counterflow_items_table.setItem(
                r, 2,
                self._cf_item(str(item.counterflow_quantity))
            )
            self._counterflow_items_table.setItem(
                r, 3,
                self._cf_item(f"\u20b9{item.counterflow_line_total:,.2f}")
            )

        self._counterflow_grand_total.setText(
            f"\u20b9{inv.counterflow_total_amount:,.2f}"
        )

    # ── Helpers ────────────────────────────────────────────────

    def _counterflow_payment_badge(self, method: str) -> QWidget:
        thm = t.counterflow_theme()
        badge = QLabel(method)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if method == "UPI":
            bg, fg = thm["upi_light"],      thm["upi_text"]
        elif method == "CASH":
            bg, fg = thm["cash_light"],     thm["cash_text"]
        else:
            bg, fg = thm["warning_light"],  thm["warning_text"]

        badge.setStyleSheet(f"""
            background: {bg};
            color: {fg};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 14px;
            font-weight: 600;
        """)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)
        wl.addWidget(badge)
        return wrapper

    def counterflow_refresh_theme(self):
        """CounterFlow \u2014 Restyle labels, cards, and rebuild tables after theme change."""
        thm = t.counterflow_theme()
        self._counterflow_total_lbl.setStyleSheet(
            f"font-weight: 700; font-size: 17px; color: {thm['text_primary']};"
        )
        self._counterflow_grand_total.setStyleSheet(
            f"font-weight: 700; font-size: 18px; color: {thm['text_primary']};"
        )
        # Update card borders
        self._counterflow_list_card.setStyleSheet(f"""
            QFrame#counterflowListCard {{
                background: {thm['card_bg']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        self._counterflow_detail_card.setStyleSheet(f"""
            QFrame#counterflowDetailCard {{
                background: {thm['card_bg']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        self.counterflow_refresh()

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
