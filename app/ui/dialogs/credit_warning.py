"""
CounterFlow v1.0.0 — Credit Warning Dialog
============================================
Shown when a customer is about to exceed their
credit limit. Displays full context (balance,
limit, bill amount, over-by) and asks the
cashier to override or cancel the transaction.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app import theme as t


class CounterFlowCreditWarningDialog(QDialog):
    """
    CounterFlow — Credit Limit Exceeded Warning Dialog.

    Shown when CREDIT payment is attempted and the
    customer would exceed their credit limit.

    Usage:
        dialog = CounterFlowCreditWarningDialog(
            counterflow_customer_name="Ravi Kumar",
            counterflow_current_balance=3200.00,
            counterflow_credit_limit=5000.00,
            counterflow_bill_amount=2100.00,
            counterflow_over_by=300.00,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User chose to override — proceed
        else:
            # User cancelled
    """

    def __init__(
        self,
        counterflow_customer_name:    str,
        counterflow_current_balance:  float,
        counterflow_credit_limit:     float,
        counterflow_bill_amount:      float,
        counterflow_over_by:          float,
        parent=None,
    ):
        super().__init__(parent)
        self._counterflow_customer_name   = counterflow_customer_name
        self._counterflow_current_balance = counterflow_current_balance
        self._counterflow_credit_limit    = counterflow_credit_limit
        self._counterflow_bill_amount     = counterflow_bill_amount
        self._counterflow_over_by         = counterflow_over_by

        self.setWindowTitle("CounterFlow — Credit Limit Exceeded")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._counterflow_build()

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
        counterflow_root.setContentsMargins(28, 28, 28, 24)
        counterflow_root.setSpacing(0)

        # ── Warning icon + title ───────────────────────────────
        counterflow_title_row = QHBoxLayout()
        counterflow_title_row.setSpacing(12)

        counterflow_warning_icon = QLabel("⚠")
        counterflow_warning_icon.setStyleSheet(
            f"font-size: 28px; color: {thm['warning']};"
        )
        counterflow_title_row.addWidget(counterflow_warning_icon)

        counterflow_title_col = QVBoxLayout()
        counterflow_title_col.setSpacing(2)
        counterflow_title_col.setContentsMargins(0, 0, 0, 0)

        counterflow_title_lbl = QLabel("Credit Limit Exceeded")
        counterflow_title_font = QFont("Segoe UI", 16)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title_lbl.setFont(counterflow_title_font)

        counterflow_sub_lbl = QLabel(
            f"{self._counterflow_customer_name} has exceeded their credit limit."
        )
        counterflow_sub_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
        )

        counterflow_title_col.addWidget(counterflow_title_lbl)
        counterflow_title_col.addWidget(counterflow_sub_lbl)

        counterflow_title_col_widget = QWidget()
        counterflow_title_col_widget.setLayout(counterflow_title_col)
        counterflow_title_row.addWidget(counterflow_title_col_widget)
        counterflow_title_row.addStretch()

        counterflow_root.addLayout(counterflow_title_row)
        counterflow_root.addSpacing(20)
        counterflow_root.addWidget(self._counterflow_divider())
        counterflow_root.addSpacing(20)

        # ── Credit breakdown card ──────────────────────────────
        counterflow_card = QFrame()
        counterflow_card.setStyleSheet(f"""
            QFrame {{
                background: {thm['warning_light']};
                border: 1px solid {thm['warning']};
                border-radius: 10px;
            }}
        """)
        counterflow_card_layout = QVBoxLayout(counterflow_card)
        counterflow_card_layout.setContentsMargins(18, 16, 18, 16)
        counterflow_card_layout.setSpacing(10)

        counterflow_rows = [
            ("Current Balance",  f"₹{self._counterflow_current_balance:,.2f}", thm["text_primary"]),
            ("Credit Limit",     f"₹{self._counterflow_credit_limit:,.2f}",    thm["text_primary"]),
            ("This Bill",        f"₹{self._counterflow_bill_amount:,.2f}",      thm["text_primary"]),
        ]
        for counterflow_lbl_text, counterflow_val_text, counterflow_val_color in counterflow_rows:
            counterflow_row = QHBoxLayout()
            counterflow_row_lbl = QLabel(counterflow_lbl_text)
            counterflow_row_lbl.setStyleSheet(
                f"color: {thm['text_secondary']}; font-size: 13px; background: transparent;"
            )
            counterflow_row_val = QLabel(counterflow_val_text)
            counterflow_row_val.setStyleSheet(
                f"color: {counterflow_val_color}; font-size: 13px; "
                f"font-weight: 600; background: transparent;"
            )
            counterflow_row_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            counterflow_row.addWidget(counterflow_row_lbl)
            counterflow_row.addStretch()
            counterflow_row.addWidget(counterflow_row_val)
            counterflow_card_layout.addLayout(counterflow_row)

        # Divider inside card
        counterflow_inner_divider = QFrame()
        counterflow_inner_divider.setFrameShape(QFrame.Shape.HLine)
        counterflow_inner_divider.setFixedHeight(1)
        counterflow_inner_divider.setStyleSheet(
            f"background: {thm['warning']}; border: none;"
        )
        counterflow_card_layout.addWidget(counterflow_inner_divider)

        # Over by row — prominent
        counterflow_over_row = QHBoxLayout()
        counterflow_over_lbl = QLabel("Over By")
        counterflow_over_lbl.setStyleSheet(
            f"color: {thm['danger']}; font-size: 14px; "
            f"font-weight: 700; background: transparent;"
        )
        counterflow_over_val = QLabel(f"₹{self._counterflow_over_by:,.2f}")
        counterflow_over_val.setStyleSheet(
            f"color: {thm['danger']}; font-size: 14px; "
            f"font-weight: 700; background: transparent;"
        )
        counterflow_over_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        counterflow_over_row.addWidget(counterflow_over_lbl)
        counterflow_over_row.addStretch()
        counterflow_over_row.addWidget(counterflow_over_val)
        counterflow_card_layout.addLayout(counterflow_over_row)

        counterflow_root.addWidget(counterflow_card)
        counterflow_root.addSpacing(20)

        # ── Question label ─────────────────────────────────────
        counterflow_question = QLabel("Do you want to override and continue?")
        counterflow_question.setStyleSheet(
            f"font-size: 13px; color: {thm['text_primary']};"
        )
        counterflow_root.addWidget(counterflow_question)
        counterflow_root.addSpacing(14)

        # ── Action buttons ─────────────────────────────────────
        counterflow_btn_row = QHBoxLayout()
        counterflow_btn_row.setSpacing(10)

        counterflow_cancel_btn = QPushButton("Cancel Transaction")
        counterflow_cancel_btn.setObjectName("counterflowOutlineBtn")
        counterflow_cancel_btn.setMinimumHeight(42)
        counterflow_cancel_btn.clicked.connect(self.reject)

        counterflow_override_btn = QPushButton("Override & Continue")
        counterflow_override_btn.setMinimumHeight(42)
        counterflow_override_btn.setMinimumWidth(180)
        counterflow_override_btn.setStyleSheet(f"""
            QPushButton {{
                background: {thm['warning']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {thm['warning_text']};
            }}
        """)
        counterflow_override_btn.clicked.connect(self.accept)

        counterflow_btn_row.addWidget(counterflow_cancel_btn)
        counterflow_btn_row.addStretch()
        counterflow_btn_row.addWidget(counterflow_override_btn)
        counterflow_root.addLayout(counterflow_btn_row)

    def _counterflow_divider(self) -> QFrame:
        thm = t.counterflow_theme()
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {thm['border']}; border: none;")
        return line
