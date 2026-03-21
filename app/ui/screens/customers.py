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
from app.core.auth import counterflow_auth_session
from app import theme as t
from app.config import COUNTERFLOW_CREDIT_NEAR_LIMIT_PCT


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
            f"font-size: 19px; font-weight: 700; "
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


class CounterFlowDeleteCustomerDialog(QDialog):
    """
    CounterFlow — Admin-only customer deletion confirmation dialog.
    Gives three options when the customer has an outstanding debt:
      • Delete and clear the debt (forgive it)
      • Delete and keep the debt record in logs (balance lost)
      • Cancel
    When the customer has zero balance, shows a simple Yes/Cancel.
    """

    # Result codes returned by counterflow_get_choice()
    CANCEL     = 0
    DELETE_CLEAR = 1   # delete + zero the balance first
    DELETE_KEEP  = 2   # delete as-is (balance recorded in log, then gone)

    def __init__(self, customer_name: str, balance: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CounterFlow — Delete Customer")
        self.setMinimumWidth(420)
        self._choice = self.CANCEL
        self._counterflow_build(customer_name, balance)
        self._counterflow_apply_style()

    def _counterflow_build(self, customer_name: str, balance: float):
        thm = t.counterflow_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Warning icon + title
        title = QLabel(f"Delete  \"{customer_name}\"?")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {thm['text_primary']};"
        )
        title.setWordWrap(True)
        layout.addWidget(title)

        if balance > 0:
            # Show debt warning
            debt_lbl = QLabel(
                f"⚠  This customer has an outstanding debt of  ₹{balance:,.2f}.\n"
                f"Choose how to handle it before deleting:"
            )
            debt_lbl.setWordWrap(True)
            debt_lbl.setStyleSheet(
                f"color: {thm['warning']}; font-size: 13px; font-weight: 600;"
            )
            layout.addWidget(debt_lbl)
            layout.addSpacing(4)

            btn_clear = QPushButton(f"Delete  +  Clear debt  (forgive ₹{balance:,.2f})")
            btn_clear.setObjectName("counterflowDangerBtn")
            btn_clear.setMinimumHeight(44)
            btn_clear.clicked.connect(lambda: self._counterflow_set(self.DELETE_CLEAR))
            layout.addWidget(btn_clear)

            btn_keep = QPushButton("Delete  without  clearing debt")
            btn_keep.setObjectName("counterflowOutlineBtn")
            btn_keep.setMinimumHeight(44)
            btn_keep.setStyleSheet(
                btn_keep.styleSheet() +
                f"color: {thm['danger']}; border-color: {thm['danger']};"
            )
            btn_keep.clicked.connect(lambda: self._counterflow_set(self.DELETE_KEEP))
            layout.addWidget(btn_keep)
        else:
            info = QLabel(
                "This customer has no outstanding debt.\n"
                "Their record will be permanently removed."
            )
            info.setWordWrap(True)
            info.setStyleSheet(f"color: {thm['text_secondary']}; font-size: 13px;")
            layout.addWidget(info)

            btn_delete = QPushButton("Yes, Delete Customer")
            btn_delete.setObjectName("counterflowDangerBtn")
            btn_delete.setMinimumHeight(44)
            btn_delete.clicked.connect(lambda: self._counterflow_set(self.DELETE_KEEP))
            layout.addWidget(btn_delete)

        # Cancel button always present
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("counterflowOutlineBtn")
        btn_cancel.setMinimumHeight(44)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def _counterflow_set(self, choice: int):
        self._choice = choice
        self.accept()

    def counterflow_get_choice(self) -> int:
        return self._choice

    def _counterflow_apply_style(self):
        thm = t.counterflow_theme()
        self.setStyleSheet(f"QDialog {{ background: {thm['bg_surface']}; }}")


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
        counterflow_layout.setContentsMargins(32, 14, 32, 28)
        counterflow_layout.setSpacing(20)

        # ── Header ─────────────────────────────────────────────
        counterflow_header = QHBoxLayout()

        counterflow_title = QLabel("Customers")
        counterflow_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        counterflow_title.setFixedHeight(46)
        counterflow_title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        counterflow_header.addWidget(counterflow_title)
        counterflow_header.addStretch()

        self._counterflow_search = QLineEdit()
        self._counterflow_search.setPlaceholderText("  ⌕  Search customers...")
        self._counterflow_search.setMinimumWidth(240)
        self._counterflow_search.setMinimumHeight(46)

        counterflow_search_font = self._counterflow_search.font()
        counterflow_search_font.setPixelSize(17)
        self._counterflow_search.setFont(counterflow_search_font)
        self._counterflow_search.textChanged.connect(self.counterflow_refresh)
        counterflow_header.addWidget(self._counterflow_search)

        counterflow_pay_btn = QPushButton("Record Credit Payment")
        counterflow_pay_btn.setMinimumHeight(46)
        counterflow_pay_btn.clicked.connect(self._counterflow_record_payment)
        counterflow_header.addWidget(counterflow_pay_btn)

        # ── Admin-only: Delete Customer button ─────────────────
        if counterflow_auth_session.counterflow_is_admin:
            self._counterflow_delete_btn = QPushButton("🗑  Delete Customer")
            self._counterflow_delete_btn.setObjectName("counterflowDangerBtn")
            self._counterflow_delete_btn.setMinimumHeight(46)
            self._counterflow_delete_btn.clicked.connect(self._counterflow_delete_customer)
            counterflow_header.addWidget(self._counterflow_delete_btn)

        counterflow_layout.addLayout(counterflow_header)

        # ── Table ──────────────────────────────────────────────
        self._counterflow_table = QTableWidget()
        self._counterflow_table.setColumnCount(5)
        self._counterflow_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Mobile", "Balance", "Limit"]
        )
        self._counterflow_table.setShowGrid(True)
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
        self._counterflow_table.setColumnWidth(0, 85)
        self._counterflow_table.setColumnWidth(2, 175)
        self._counterflow_table.setColumnWidth(3, 155)
        self._counterflow_table.setColumnWidth(4, 135)
        
        # Center headers
        self._counterflow_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
            elif c.counterflow_credit_balance >= c.counterflow_credit_limit * COUNTERFLOW_CREDIT_NEAR_LIMIT_PCT:
                counterflow_balance_item.setForeground(QColor(thm["balance_high"]))
            else:
                counterflow_balance_item.setForeground(QColor(thm["balance_low"]))

            counterflow_balance_item.setFont(
                QFont("Segoe UI", 16, QFont.Weight.Bold)
            )
            counterflow_balance_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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

    def _counterflow_delete_customer(self):
        """CounterFlow — Admin-only: permanently delete selected customer."""
        counterflow_row = self._counterflow_table.currentRow()
        if counterflow_row < 0:
            QMessageBox.warning(
                self, "CounterFlow",
                "Please select a customer from the list first."
            )
            return

        counterflow_cust_id   = int(self._counterflow_table.item(counterflow_row, 0).text())
        counterflow_cust_name = self._counterflow_table.item(counterflow_row, 1).text()
        counterflow_balance   = float(
            self._counterflow_table.item(counterflow_row, 3)
            .text().replace("₹", "").replace(",", "")
        )

        dialog = CounterFlowDeleteCustomerDialog(
            counterflow_cust_name, counterflow_balance, self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        choice = dialog.counterflow_get_choice()
        if choice == CounterFlowDeleteCustomerDialog.CANCEL:
            return

        clear_debt = (choice == CounterFlowDeleteCustomerDialog.DELETE_CLEAR)

        try:
            self.counterflow_cust_mgr.counterflow_delete_customer(
                customer_id=counterflow_cust_id,
                clear_debt=clear_debt,
            )
            self.counterflow_session.commit()
            self.counterflow_refresh()
            QMessageBox.information(
                self, "CounterFlow — Customer Deleted",
                f"\"{counterflow_cust_name}\" has been permanently removed."
                + (f"\nDebt of ₹{counterflow_balance:,.2f} was cleared." if clear_debt and counterflow_balance > 0 else "")
            )
        except Exception as e:
            self.counterflow_session.rollback()
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def counterflow_refresh_theme(self):
        """CounterFlow — Rebuild table after theme change so balance
        colours use the current theme palette."""
        self.counterflow_refresh()

    def _cf_item(self, text: str, align=Qt.AlignmentFlag.AlignCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(align)
        return item
