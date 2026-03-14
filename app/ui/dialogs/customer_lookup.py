"""
CounterFlow v1.0.0 — Customer Lookup Dialog
=============================================
Search and select a customer by name or mobile.
Used from the POS billing screen when the
operator wants to find an existing customer.
Returns the selected customer object.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from app.core.customer_manager import CounterFlowCustomerManager
from app import theme as t


class CounterFlowCustomerLookupDialog(QDialog):
    """
    CounterFlow — Customer Lookup / Search Dialog.

    Usage:
        dialog = CounterFlowCustomerLookupDialog(
            counterflow_session=session,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            customer = dialog.counterflow_selected_customer

    The selected customer is stored in
    self.counterflow_selected_customer after acceptance.
    """

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session      = counterflow_session
        self.counterflow_cust_mgr     = CounterFlowCustomerManager(counterflow_session)
        self.counterflow_selected_customer = None
        self._counterflow_all_customers    = []

        self.setWindowTitle("CounterFlow — Customer Lookup")
        self.setMinimumWidth(560)
        self.setMinimumHeight(480)
        self.setModal(True)
        self._counterflow_build()
        self._counterflow_load_all()

    def _counterflow_build(self):
        thm = t.counterflow_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background: {thm['bg_surface']};
            }}
            QLabel {{
                background: transparent;
                color: {thm['text_primary']};
            }}
        """)

        counterflow_root = QVBoxLayout(self)
        counterflow_root.setContentsMargins(24, 24, 24, 20)
        counterflow_root.setSpacing(0)

        # ── Header ─────────────────────────────────────────────
        counterflow_title = QLabel("Customer Lookup")
        counterflow_title_font = QFont("Segoe UI", 17)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_root.addWidget(counterflow_title)

        counterflow_sub = QLabel("Search by name or mobile number.")
        counterflow_sub.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
        )
        counterflow_root.addWidget(counterflow_sub)
        counterflow_root.addSpacing(16)

        # ── Search input ───────────────────────────────────────
        counterflow_search_row = QHBoxLayout()
        counterflow_search_row.setSpacing(10)

        self._counterflow_search_input = QLineEdit()
        self._counterflow_search_input.setPlaceholderText(
            "  🔍   Search name or mobile..."
        )
        self._counterflow_search_input.setMinimumHeight(44)
        self._counterflow_search_input.textChanged.connect(
            self._counterflow_on_search_changed
        )

        counterflow_search_row.addWidget(self._counterflow_search_input)
        counterflow_root.addLayout(counterflow_search_row)
        counterflow_root.addSpacing(14)

        # ── Results table ──────────────────────────────────────
        self._counterflow_table = QTableWidget()
        self._counterflow_table.setColumnCount(4)
        self._counterflow_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Mobile", "Outstanding"]
        )
        self._counterflow_table.setShowGrid(False)
        self._counterflow_table.setAlternatingRowColors(False)
        self._counterflow_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._counterflow_table.verticalHeader().setVisible(False)
        self._counterflow_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_table.setColumnWidth(0, 48)
        self._counterflow_table.setColumnWidth(2, 130)
        self._counterflow_table.setColumnWidth(3, 120)
        self._counterflow_table.doubleClicked.connect(
            self._counterflow_on_double_click
        )
        counterflow_root.addWidget(self._counterflow_table)
        counterflow_root.addSpacing(8)

        # ── Count label ────────────────────────────────────────
        self._counterflow_count_label = QLabel("0 customers")
        self._counterflow_count_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
        )
        counterflow_root.addWidget(self._counterflow_count_label)
        counterflow_root.addSpacing(16)

        # ── Buttons ────────────────────────────────────────────
        counterflow_divider = QFrame()
        counterflow_divider.setFrameShape(QFrame.Shape.HLine)
        counterflow_divider.setFixedHeight(1)
        counterflow_divider.setStyleSheet(
            f"background: {thm['border']}; border: none;"
        )
        counterflow_root.addWidget(counterflow_divider)
        counterflow_root.addSpacing(14)

        counterflow_btn_row = QHBoxLayout()
        counterflow_btn_row.setSpacing(10)

        counterflow_cancel_btn = QPushButton("Cancel")
        counterflow_cancel_btn.setObjectName("counterflowOutlineBtn")
        counterflow_cancel_btn.setMinimumHeight(40)
        counterflow_cancel_btn.clicked.connect(self.reject)

        self._counterflow_select_btn = QPushButton("Select Customer")
        self._counterflow_select_btn.setMinimumHeight(40)
        self._counterflow_select_btn.setMinimumWidth(160)
        self._counterflow_select_btn.clicked.connect(self._counterflow_confirm_selection)

        counterflow_btn_row.addStretch()
        counterflow_btn_row.addWidget(counterflow_cancel_btn)
        counterflow_btn_row.addWidget(self._counterflow_select_btn)
        counterflow_root.addLayout(counterflow_btn_row)

    # ── Data ───────────────────────────────────────────────────

    def _counterflow_load_all(self):
        """CounterFlow — Load all customers into table on open."""
        self._counterflow_all_customers = (
            self.counterflow_cust_mgr.counterflow_get_all_customers()
        )
        self._counterflow_populate(self._counterflow_all_customers)
        QTimer.singleShot(100, self._counterflow_search_input.setFocus)

    def _counterflow_on_search_changed(self, text: str):
        """CounterFlow — Filter table as user types."""
        text = text.strip()
        if not text:
            self._counterflow_populate(self._counterflow_all_customers)
            return
        counterflow_results = self.counterflow_cust_mgr.counterflow_search_customers(
            text
        )
        self._counterflow_populate(counterflow_results)

    def _counterflow_populate(self, customers: list):
        """CounterFlow — Fill the table with a list of customers."""
        thm = t.counterflow_theme()
        self._counterflow_table.setRowCount(len(customers))

        for row, c in enumerate(customers):
            self._counterflow_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_table.setItem(
                row, 0, self._cf_item(str(c.counterflow_customer_id))
            )
            self._counterflow_table.setItem(
                row, 1, self._cf_item(c.counterflow_name)
            )
            self._counterflow_table.setItem(
                row, 2, self._cf_item(c.counterflow_mobile)
            )

            counterflow_balance_item = QTableWidgetItem(
                f"₹{c.counterflow_credit_balance:,.0f}"
            )
            counterflow_balance_item.setFlags(
                counterflow_balance_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            if c.counterflow_credit_balance == 0:
                counterflow_balance_item.setForeground(
                    QColor(thm["balance_zero"])
                )
            elif c.counterflow_credit_balance >= c.counterflow_credit_limit * 0.8:
                counterflow_balance_item.setForeground(
                    QColor(thm["balance_high"])
                )
            else:
                counterflow_balance_item.setForeground(
                    QColor(thm["balance_low"])
                )
            self._counterflow_table.setItem(row, 3, counterflow_balance_item)

        self._counterflow_count_label.setText(
            f"{len(customers)} customer{'s' if len(customers) != 1 else ''}"
        )

    # ── Selection ──────────────────────────────────────────────

    def _counterflow_on_double_click(self, index):
        """CounterFlow — Double click row to instantly select."""
        self._counterflow_confirm_selection()

    def _counterflow_confirm_selection(self):
        """CounterFlow — Set selected customer and close."""
        counterflow_row = self._counterflow_table.currentRow()
        if counterflow_row < 0:
            QMessageBox.information(
                self, "CounterFlow",
                "Please select a customer from the list."
            )
            return

        counterflow_cust_id = int(
            self._counterflow_table.item(counterflow_row, 0).text()
        )
        self.counterflow_selected_customer = (
            self.counterflow_cust_mgr.counterflow_get_by_id(counterflow_cust_id)
        )
        self.accept()

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
