"""
CounterFlow v1.0.0 — Payment Confirmation Dialog
==================================================
Final checkout confirmation dialog shown before
a bill is finalized. Displays the bill summary,
customer info, and payment method selection.
Gives the cashier a last review before committing.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.billing import CounterFlowBillingSession
from app import theme as t


class CounterFlowPaymentDialog(QDialog):
    """
    CounterFlow — Payment Confirmation Dialog.

    Shows a summary of the current bill and
    asks the cashier to confirm the payment method.

    Usage:
        dialog = CounterFlowPaymentDialog(
            counterflow_billing_session=billing,
            counterflow_customer_name="Ravi Kumar",
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            method = dialog.counterflow_selected_method
    """

    def __init__(
        self,
        counterflow_billing_session: CounterFlowBillingSession,
        counterflow_customer_name:   str  = "Walk-in Customer",
        parent=None,
    ):
        super().__init__(parent)
        self._counterflow_billing       = counterflow_billing_session
        self._counterflow_customer_name = counterflow_customer_name
        self.counterflow_selected_method = None

        self.setWindowTitle("CounterFlow — Confirm Payment")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._counterflow_build()

    def _counterflow_build(self):
        thm = t.counterflow_theme()
        # Apply theme to the dialog AND all direct QLabel / QPushButton children.
        # Without the explicit QLabel and QPushButton rules here the global
        # app stylesheet wins with light-mode colours, because QDialog is a
        # top-level window and Qt re-evaluates the cascade from the root — the
        # inline setStyleSheet on the dialog takes precedence for the widget
        # itself but NOT for its children unless they are included.
        self.setStyleSheet(f"""
            QDialog {{
                background: {thm['bg_surface']};
            }}
            QLabel {{
                background: transparent;
                color: {thm['text_primary']};
            }}
            QPushButton#counterflowOutlineBtn {{
                background: transparent;
                color: {thm['text_primary']};
                border: 1px solid {thm['border']};
            }}
            QPushButton#counterflowOutlineBtn:hover {{
                background: {thm['hover']};
            }}
        """)

        counterflow_root = QVBoxLayout(self)
        counterflow_root.setContentsMargins(28, 28, 28, 24)
        counterflow_root.setSpacing(0)

        # ── Title ──────────────────────────────────────────────
        counterflow_title = QLabel("Confirm Payment")
        counterflow_title_font = QFont("Segoe UI", 17)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_root.addWidget(counterflow_title)

        counterflow_sub = QLabel("Review the bill and select a payment method.")
        counterflow_sub.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
        )
        counterflow_root.addWidget(counterflow_sub)
        counterflow_root.addSpacing(20)
        counterflow_root.addWidget(self._counterflow_divider())
        counterflow_root.addSpacing(20)

        # ── Customer info ──────────────────────────────────────
        counterflow_cust_row = QHBoxLayout()
        counterflow_cust_lbl = QLabel("Customer")
        counterflow_cust_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 13px;"
        )
        counterflow_cust_val = QLabel(self._counterflow_customer_name)
        counterflow_cust_val.setStyleSheet(
            f"color: {thm['text_primary']}; font-size: 13px; font-weight: 600;"
        )
        counterflow_cust_row.addWidget(counterflow_cust_lbl)
        counterflow_cust_row.addStretch()
        counterflow_cust_row.addWidget(counterflow_cust_val)
        counterflow_root.addLayout(counterflow_cust_row)
        counterflow_root.addSpacing(8)

        # ── Items count ────────────────────────────────────────
        counterflow_items_row = QHBoxLayout()
        counterflow_items_lbl = QLabel("Items")
        counterflow_items_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 13px;"
        )
        counterflow_items_val = QLabel(
            str(self._counterflow_billing.counterflow_item_count)
        )
        counterflow_items_val.setStyleSheet(
            f"color: {thm['text_primary']}; font-size: 13px; font-weight: 600;"
        )
        counterflow_items_row.addWidget(counterflow_items_lbl)
        counterflow_items_row.addStretch()
        counterflow_items_row.addWidget(counterflow_items_val)
        counterflow_root.addLayout(counterflow_items_row)
        counterflow_root.addSpacing(16)

        counterflow_root.addWidget(self._counterflow_divider())
        counterflow_root.addSpacing(16)

        # ── Total amount card ──────────────────────────────────
        counterflow_total_card = QFrame()
        counterflow_total_card.setStyleSheet(f"""
            QFrame {{
                background: {thm['text_primary']};
                border-radius: 12px;
                border: none;
            }}
        """)
        counterflow_total_card.setMinimumHeight(90)

        counterflow_total_layout = QVBoxLayout(counterflow_total_card)
        counterflow_total_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        counterflow_total_title_lbl = QLabel("Total Amount")
        counterflow_total_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counterflow_total_title_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.65); font-size: 12px; "
            "background: transparent; border: none;"
        )

        counterflow_total_amount_lbl = QLabel(
            self._counterflow_billing.counterflow_display_total
        )
        counterflow_total_amount_font = QFont("Segoe UI", 26)
        counterflow_total_amount_font.setWeight(QFont.Weight.Bold)
        counterflow_total_amount_lbl.setFont(counterflow_total_amount_font)
        counterflow_total_amount_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counterflow_total_amount_lbl.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        counterflow_total_layout.addWidget(counterflow_total_title_lbl)
        counterflow_total_layout.addWidget(counterflow_total_amount_lbl)
        counterflow_root.addWidget(counterflow_total_card)
        counterflow_root.addSpacing(20)

        # ── Payment method buttons ─────────────────────────────
        counterflow_pay_label = QLabel("Select Payment Method")
        counterflow_pay_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; "
            f"color: {thm['text_secondary']};"
        )
        counterflow_root.addWidget(counterflow_pay_label)
        counterflow_root.addSpacing(10)

        counterflow_methods_row = QHBoxLayout()
        counterflow_methods_row.setSpacing(10)

        counterflow_cash_btn   = self._counterflow_method_btn(
            "💵  CASH",   thm["cash_color"],   thm["cash_light"],   "CASH"
        )
        counterflow_upi_btn    = self._counterflow_method_btn(
            "📲  UPI",    thm["upi_color"],    thm["upi_light"],    "UPI"
        )
        counterflow_credit_btn = self._counterflow_method_btn(
            "💳  CREDIT", thm["credit_color"], thm["credit_light"], "CREDIT"
        )

        counterflow_methods_row.addWidget(counterflow_cash_btn)
        counterflow_methods_row.addWidget(counterflow_upi_btn)
        counterflow_methods_row.addWidget(counterflow_credit_btn)
        counterflow_root.addLayout(counterflow_methods_row)
        counterflow_root.addSpacing(16)

        # ── Cancel ─────────────────────────────────────────────
        counterflow_root.addWidget(self._counterflow_divider())
        counterflow_root.addSpacing(16)

        counterflow_cancel_btn = QPushButton("Cancel")
        counterflow_cancel_btn.setObjectName("counterflowOutlineBtn")
        counterflow_cancel_btn.setMinimumHeight(40)
        counterflow_cancel_btn.clicked.connect(self.reject)
        counterflow_root.addWidget(counterflow_cancel_btn)

    def _counterflow_method_btn(
        self,
        label:      str,
        color:      str,
        light_bg:   str,
        method_key: str,
    ) -> QPushButton:
        """CounterFlow — Styled payment method button."""
        btn = QPushButton(label)
        btn.setMinimumHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: 2px solid {color};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {light_bg};
            }}
        """)
        btn.clicked.connect(
            lambda: self._counterflow_select_method(method_key)
        )
        return btn

    def _counterflow_select_method(self, method: str):
        """CounterFlow — Store selected method and close."""
        self.counterflow_selected_method = method
        self.accept()

    def _counterflow_divider(self) -> QFrame:
        thm = t.counterflow_theme()
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {thm['border']}; border: none;")
        return line
