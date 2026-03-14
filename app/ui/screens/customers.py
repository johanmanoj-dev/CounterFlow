"""
CounterFlow v1.0.0 — Customers Screen
=======================================
Customer list with credit balance color coding.
Green = zero, Amber = has balance, Red = near limit.
Matches approved CounterFlow design exactly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.core.customer_manager import CounterFlowCustomerManager
from app import theme as t


class CounterFlowCreditPaymentDialog(QDialog):
    """CounterFlow — Record credit payment popup."""

    def __init__(self, customer_name: str, current_balance: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CounterFlow — Record Credit Payment")
        self.setMinimumWidth(380)
        self._counterflow_build(customer_name, current_balance)

    def _counterflow_build(self, customer_name, balance):
        thm = t.counterflow_theme()
        self.setStyleSheet(f"background: {thm['bg_surface']};")

        counterflow_layout = QFormLayout(self)
        counterflow_layout.setContentsMargins(24, 24, 24, 24)
        counterflow_layout.setSpacing(14)

        counterflow_title = QLabel("Record Credit Payment")
        counterflow_title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; "
            f"color: {thm['text_primary']}; margin-bottom: 4px;"
        )
        counterflow_layout.addRow(counterflow_title)

        counterflow_name_lbl = QLabel(customer_name)
        counterflow_name_lbl.setStyleSheet(
            f"font-weight: 600; color: {thm['text_primary']};"
        )
        counterflow_layout.addRow("Customer:", counterflow_name_lbl)

        counterflow_bal_lbl = QLabel(f"₹{balance:,.2f}")
        counterflow_bal_lbl.setStyleSheet(
            f"color: {thm['warning']}; font-weight: 600;"
        )
        counterflow_layout.addRow("Outstanding:", counterflow_bal_lbl)

        self._counterflow_amount = QDoubleSpinBox()
        # Cap at the actual outstanding balance — overpayment is not allowed.
        self._counterflow_amount.setRange(0.01, max(0.01, balance))
        self._counterflow_amount.setValue(balance)   # default = pay in full
        self._counterflow_amount.setPrefix("₹ ")
        self._counterflow_amount.setDecimals(2)
        counterflow_layout.addRow("Amount Paid:", self._counterflow_amount)

        counterflow_btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        counterflow_btns.accepted.connect(self.accept)
        counterflow_btns.rejected.connect(self.reject)
        counterflow_layout.addRow(counterflow_btns)

    def counterflow_get_amount(self) -> float:
        return self._counterflow_amount.value()


class CounterFlowCustomersScreen(QWidget):
    """CounterFlow — Customer Management Screen."""

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session  = counterflow_session
        self.counterflow_cust_mgr = CounterFlowCustomerManager(counterflow_session)
        self._counterflow_build()
        self.counterflow_refresh()

    def _counterflow_build(self):
        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(32, 28, 32, 28)
        counterflow_layout.setSpacing(20)

        # ── Header ─────────────────────────────────────────────
        counterflow_header = QHBoxLayout()

        counterflow_title = QLabel("Customers")
        counterflow_title_font = QFont("Segoe UI", 20)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_header.addWidget(counterflow_title)
        counterflow_header.addStretch()

        self._counterflow_search = QLineEdit()
        self._counterflow_search.setPlaceholderText("  🔍  Search customers...")
        self._counterflow_search.setMinimumWidth(240)
        self._counterflow_search.setMinimumHeight(40)
        self._counterflow_search.textChanged.connect(self.counterflow_refresh)
        counterflow_header.addWidget(self._counterflow_search)

        counterflow_pay_btn = QPushButton("💳  Record Credit Payment")
        counterflow_pay_btn.setMinimumHeight(40)
        counterflow_pay_btn.clicked.connect(self._counterflow_record_payment)
        counterflow_header.addWidget(counterflow_pay_btn)

        counterflow_layout.addLayout(counterflow_header)

        # ── Table ──────────────────────────────────────────────
        self._counterflow_table = QTableWidget()
        self._counterflow_table.setColumnCount(5)
        self._counterflow_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Mobile", "Balance", "Limit"]
        )
        self._counterflow_table.setShowGrid(False)
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
        self._counterflow_table.setColumnWidth(0, 50)
        self._counterflow_table.setColumnWidth(2, 140)
        self._counterflow_table.setColumnWidth(3, 120)
        self._counterflow_table.setColumnWidth(4, 100)
        # Double-clicking a row opens the payment dialog directly,
        # so the cashier does not need to find and click the header button.
        self._counterflow_table.doubleClicked.connect(
            self._counterflow_record_payment
        )
        counterflow_layout.addWidget(self._counterflow_table)

    def counterflow_refresh(self):
        """CounterFlow — Reload customer table from DB."""
        counterflow_query = (
            self._counterflow_search.text().strip()
            if hasattr(self, "_counterflow_search") else ""
        )
        counterflow_customers = (
            self.counterflow_cust_mgr.counterflow_search_customers(counterflow_query)
            if counterflow_query
            else self.counterflow_cust_mgr.counterflow_get_all_customers()
        )

        self._counterflow_table.setRowCount(len(counterflow_customers))
        thm = t.counterflow_theme()

        for row, c in enumerate(counterflow_customers):
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

            # Balance with color
            counterflow_balance_item = QTableWidgetItem(
                f"₹{c.counterflow_credit_balance:,.0f}"
            )
            counterflow_balance_item.setFlags(
                counterflow_balance_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            if c.counterflow_credit_balance == 0:
                counterflow_balance_item.setForeground(QColor(thm["balance_zero"]))
            elif c.counterflow_credit_balance >= c.counterflow_credit_limit * 0.8:
                counterflow_balance_item.setForeground(QColor(thm["balance_high"]))
            else:
                counterflow_balance_item.setForeground(QColor(thm["balance_low"]))

            counterflow_balance_item.setFont(
                QFont("Segoe UI", 13, QFont.Weight.Bold)
            )
            self._counterflow_table.setItem(row, 3, counterflow_balance_item)
            self._counterflow_table.setItem(
                row, 4,
                self._cf_item(f"₹{c.counterflow_credit_limit:,.0f}")
            )

    def _counterflow_record_payment(self):
        counterflow_row = self._counterflow_table.currentRow()
        if counterflow_row < 0:
            QMessageBox.warning(
                self, "CounterFlow",
                "Please select a customer from the list first.\n"
                "You can also double-click a customer row to open this dialog."
            )
            return

        counterflow_cust_id   = int(
            self._counterflow_table.item(counterflow_row, 0).text()
        )
        counterflow_cust_name = self._counterflow_table.item(counterflow_row, 1).text()
        counterflow_balance   = float(
            self._counterflow_table.item(counterflow_row, 3)
            .text().replace("₹", "").replace(",", "")
        )

        # Guard: do not open dialog if balance is already zero
        if counterflow_balance <= 0:
            QMessageBox.information(
                self, "CounterFlow",
                f"{counterflow_cust_name} has no outstanding credit balance."
            )
            return

        counterflow_dialog = CounterFlowCreditPaymentDialog(
            counterflow_cust_name, counterflow_balance, self
        )
        if counterflow_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.counterflow_cust_mgr.counterflow_record_credit_payment(
                customer_id=counterflow_cust_id,
                amount=counterflow_dialog.counterflow_get_amount(),
            )
            self.counterflow_session.commit()
            self.counterflow_refresh()
            QMessageBox.information(
                self, "CounterFlow — Payment Recorded",
                f"Payment recorded for {counterflow_cust_name}."
            )
        except Exception as e:
            self.counterflow_session.rollback()
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def counterflow_refresh_theme(self):
        """CounterFlow — Rebuild table after theme change so balance
        colours use the current theme palette."""
        self.counterflow_refresh()

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
