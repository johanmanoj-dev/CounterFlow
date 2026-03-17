"""
CounterFlow v1.0.0 — POS Billing Screen
=========================================
The heart of CounterFlow. Two-panel layout.
Left: barcode input + items table.
Right: total display + customer + payment buttons.

Logical constraints enforced here:
  - Bill cannot be finalized when empty
  - CREDIT payment requires a valid mobile number
  - Invalid mobile number blocks finalization (no silent drop)
  - New customers require a name before the bill commits
  - Mobile field accepts up to 15 chars (handles +91 prefix)
  - Mobile lookup triggered by Enter or "Find" button, NOT editingFinished
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from app.core.billing import CounterFlowBillingSession
from app.core.inventory_manager import CounterFlowInventoryManager
from app.core.customer_manager import CounterFlowCustomerManager
from app.core.credit_manager import (
    CounterFlowBillingFinalizer,
    CounterFlowCreditLimitError,
    CounterFlowEmptyBillError,
)
from app.utils.validators import counterflow_validate_mobile as _counterflow_validate_mobile_strict
from app import theme as t


class CounterFlowPOSScreen(QWidget):
    """
    CounterFlow — POS Billing Screen.
    Two panel layout. Barcode scanner input always focused.
    Inventory deducted ONLY on finalization.
    """

    counterflow_bill_finalized = pyqtSignal()

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session    = counterflow_session
        self.counterflow_billing    = CounterFlowBillingSession()
        self.counterflow_inventory  = CounterFlowInventoryManager(counterflow_session)
        self.counterflow_customers  = CounterFlowCustomerManager(counterflow_session)
        # True when the looked-up mobile belongs to a brand-new customer
        self._counterflow_is_new_customer = False
        # True once _counterflow_on_mobile_entered() has successfully
        # run for the current value in the mobile field. Reset whenever
        # the text changes so we always re-verify before finalizing.
        self._counterflow_lookup_done = False
        self._counterflow_build()
        self._counterflow_setup_shortcuts()

    # ── Build ──────────────────────────────────────────────────

    def _counterflow_build(self):
        counterflow_root = QHBoxLayout(self)
        counterflow_root.setContentsMargins(0, 0, 0, 0)
        counterflow_root.setSpacing(0)

        counterflow_left  = self._counterflow_build_left_panel()
        counterflow_right = self._counterflow_build_right_panel()

        counterflow_root.addWidget(counterflow_left,  65)
        counterflow_root.addWidget(counterflow_right, 35)

        QTimer.singleShot(100, self._counterflow_barcode_input.setFocus)

    def _counterflow_build_left_panel(self) -> QWidget:
        thm = t.counterflow_theme()
        counterflow_panel  = QWidget()
        counterflow_layout = QVBoxLayout(counterflow_panel)
        counterflow_layout.setContentsMargins(32, 28, 24, 28)
        counterflow_layout.setSpacing(16)

        # Title
        counterflow_title = QLabel("New Bill — POS")
        counterflow_title_font = QFont("Segoe UI", 23)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # Barcode row
        counterflow_barcode_row = QHBoxLayout()
        counterflow_barcode_row.setSpacing(8)

        self._counterflow_barcode_input = QLineEdit()
        self._counterflow_barcode_input.setPlaceholderText("Scan or enter barcode...")
        self._counterflow_barcode_input.setMinimumHeight(50)
        self._counterflow_barcode_input.returnPressed.connect(
            self._counterflow_on_barcode_entered
        )

        counterflow_add_btn = QPushButton("+ Add")
        counterflow_add_btn.setMinimumHeight(50)
        counterflow_add_btn.setMinimumWidth(80)
        counterflow_add_btn.clicked.connect(self._counterflow_on_barcode_entered)

        counterflow_barcode_row.addWidget(self._counterflow_barcode_input)
        counterflow_barcode_row.addWidget(counterflow_add_btn)
        counterflow_layout.addLayout(counterflow_barcode_row)

        # Bill table
        self._counterflow_bill_table = QTableWidget()
        self._counterflow_bill_table.setColumnCount(6)
        self._counterflow_bill_table.setHorizontalHeaderLabels(
            ["#", "Product", "Price", "Qty", "Total", ""]
        )
        self._counterflow_bill_table.setShowGrid(False)
        self._counterflow_bill_table.setAlternatingRowColors(False)
        self._counterflow_bill_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_bill_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._counterflow_bill_table.verticalHeader().setVisible(False)
        self._counterflow_bill_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_bill_table.setColumnWidth(0, 40)
        self._counterflow_bill_table.setColumnWidth(5, 40)
        counterflow_layout.addWidget(self._counterflow_bill_table)

        # Item count
        self._counterflow_item_count_label = QLabel("0 items in cart")
        self._counterflow_item_count_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )
        counterflow_layout.addWidget(self._counterflow_item_count_label)

        return counterflow_panel

    def _counterflow_build_right_panel(self) -> QWidget:
        thm = t.counterflow_theme()

        counterflow_panel = QWidget()
        # Use a specific object name so the rule only applies to the panel
        # itself — NOT to every child QWidget. Without this the broad
        # "QWidget {}" rule cascades into child inputs/buttons and overrides
        # the global application stylesheet, causing dark-mode colours to
        # become invisible on those children.
        counterflow_panel.setObjectName("counterflowRightPanel")
        counterflow_panel.setStyleSheet(f"""
            QWidget#counterflowRightPanel {{
                background: {thm['bg_surface']};
                border-left: 1px solid {thm['border']};
            }}
        """)
        # Keep a reference so counterflow_refresh_theme() can update it.
        self._counterflow_right_panel = counterflow_panel
        counterflow_layout = QVBoxLayout(counterflow_panel)
        counterflow_layout.setContentsMargins(24, 28, 24, 28)
        counterflow_layout.setSpacing(16)

        # ── Total card ─────────────────────────────────────────
        self._counterflow_total_card = QFrame()
        self._counterflow_total_card.setStyleSheet(f"""
            QFrame {{
                background: #111827;
                border-radius: 12px;
                border: 1px solid {thm['border']};
            }}
        """)
        self._counterflow_total_card.setMinimumHeight(116)

        counterflow_total_layout = QVBoxLayout(self._counterflow_total_card)
        counterflow_total_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        counterflow_total_title = QLabel("Total Amount")
        counterflow_total_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counterflow_total_title.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 16px; background: transparent; border: none;"
        )

        self._counterflow_total_label = QLabel("₹0.00")
        counterflow_total_font = QFont("Segoe UI", 31)
        counterflow_total_font.setWeight(QFont.Weight.Bold)
        self._counterflow_total_label.setFont(counterflow_total_font)
        self._counterflow_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_total_label.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        counterflow_total_layout.addWidget(counterflow_total_title)
        counterflow_total_layout.addWidget(self._counterflow_total_label)
        counterflow_layout.addWidget(self._counterflow_total_card)

        # ── Customer section ───────────────────────────────────
        counterflow_cust_card = QFrame()
        counterflow_cust_card.setObjectName("counterflowCustCard")
        counterflow_cust_card.setStyleSheet(f"""
            QFrame#counterflowCustCard {{
                background: {thm['bg_app']};
                border: 1px solid {thm['border']};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        # Keep a reference so counterflow_refresh_theme() can update it.
        self._counterflow_cust_card = counterflow_cust_card
        counterflow_cust_layout = QVBoxLayout(counterflow_cust_card)
        counterflow_cust_layout.setContentsMargins(16, 14, 16, 14)
        counterflow_cust_layout.setSpacing(8)

        # Mobile row: input + Find button
        counterflow_mobile_row = QHBoxLayout()
        counterflow_mobile_row.setSpacing(6)

        self._counterflow_mobile_input = QLineEdit()
        self._counterflow_mobile_input.setPlaceholderText("Customer mobile number")
        # 15 chars to accommodate +91 prefix (e.g. +919876543210 = 13 chars)
        self._counterflow_mobile_input.setMaxLength(15)
        # Use returnPressed only — NOT editingFinished, which fires when any
        # other widget (including the Pay buttons) steals focus, creating a
        # race between validation and finalization.
        self._counterflow_mobile_input.returnPressed.connect(
            self._counterflow_on_mobile_entered
        )
        # Whenever the cashier edits the mobile field the previous lookup
        # result is no longer valid — force a fresh lookup before pay.
        self._counterflow_mobile_input.textChanged.connect(
            self._counterflow_on_mobile_text_changed
        )

        self._counterflow_find_btn = QPushButton("Find")
        self._counterflow_find_btn.setFixedWidth(70)
        self._counterflow_find_btn.setFixedHeight(46)
        self._counterflow_find_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {thm['text_primary']};
                border: 1.5px solid {thm['border']};
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {thm['hover']};
            }}
        """)
        self._counterflow_find_btn.clicked.connect(self._counterflow_on_mobile_entered)

        counterflow_mobile_row.addWidget(self._counterflow_mobile_input)
        counterflow_mobile_row.addWidget(self._counterflow_find_btn)
        counterflow_cust_layout.addLayout(counterflow_mobile_row)

        # Customer status label
        self._counterflow_customer_info = QLabel("Customer: Walk-in Customer")
        self._counterflow_customer_info.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )
        counterflow_cust_layout.addWidget(self._counterflow_customer_info)

        # Customer name input — shown only when a NEW (unknown) mobile is entered
        self._counterflow_name_input = QLineEdit()
        self._counterflow_name_input.setPlaceholderText("Customer name (required for new customers)")
        self._counterflow_name_input.setVisible(False)
        counterflow_cust_layout.addWidget(self._counterflow_name_input)

        counterflow_layout.addWidget(counterflow_cust_card)

        # ── Payment buttons ────────────────────────────────────
        counterflow_pay_row = QHBoxLayout()
        counterflow_pay_row.setSpacing(8)

        self._counterflow_cash_btn   = self._counterflow_pay_btn("CASH",   "#16a34a", "#dcfce7")
        self._counterflow_upi_btn    = self._counterflow_pay_btn("UPI",    "#2563eb", "#dbeafe")
        self._counterflow_credit_btn = self._counterflow_pay_btn("CREDIT", "#d97706", "#fef3c7")

        # Disabled until at least one item is in the cart — prevents
        # blank ₹0.00 bills being committed on an empty session.
        self._counterflow_cash_btn.setEnabled(False)
        self._counterflow_upi_btn.setEnabled(False)
        self._counterflow_credit_btn.setEnabled(False)

        self._counterflow_cash_btn.clicked.connect(
            lambda: self._counterflow_finalize("CASH")
        )
        self._counterflow_upi_btn.clicked.connect(
            lambda: self._counterflow_finalize("UPI")
        )
        self._counterflow_credit_btn.clicked.connect(
            lambda: self._counterflow_finalize("CREDIT")
        )

        counterflow_pay_row.addWidget(self._counterflow_cash_btn)
        counterflow_pay_row.addWidget(self._counterflow_upi_btn)
        counterflow_pay_row.addWidget(self._counterflow_credit_btn)
        counterflow_layout.addLayout(counterflow_pay_row)

        # ── Cancel button ──────────────────────────────────────
        counterflow_cancel_btn = QPushButton("Cancel Bill")
        counterflow_cancel_btn.setObjectName("counterflowDangerBtn")
        counterflow_cancel_btn.setMinimumHeight(50)
        counterflow_cancel_btn.clicked.connect(self._counterflow_cancel_bill)
        counterflow_layout.addWidget(counterflow_cancel_btn)

        counterflow_layout.addStretch()
        return counterflow_panel

    def _counterflow_pay_btn(self, label, color, bg) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: 1.5px solid {color};
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {bg};
            }}
        """)
        return btn

    def _counterflow_setup_shortcuts(self):
        QShortcut(
            QKeySequence("F2"), self,
            self._counterflow_barcode_input.setFocus
        )

    def _counterflow_update_pay_buttons(self):
        """
        CounterFlow — Enable payment buttons only when a customer has been
        verified via the Find / Enter lookup. Buttons remain disabled (and
        visually greyed-out) until _counterflow_lookup_done is True, which
        means the cashier has pressed Find or Enter and the mobile number
        has been matched against the database (existing) or flagged as new.

        This is the single authoritative place that controls button state —
        all other methods call here rather than toggling setEnabled directly.
        """
        counterflow_ready = (
            self._counterflow_lookup_done
            and not self.counterflow_billing.counterflow_is_empty
        )
        self._counterflow_cash_btn.setEnabled(counterflow_ready)
        self._counterflow_upi_btn.setEnabled(counterflow_ready)
        self._counterflow_credit_btn.setEnabled(counterflow_ready)

    # ── Theme Refresh ──────────────────────────────────────────

    def counterflow_refresh_theme(self):
        """
        CounterFlow — Re-apply the current theme to all widget-level
        stylesheets inside the POS screen.  Called by the main window
        whenever the user toggles dark / light mode.
        """
        thm = t.counterflow_theme()

        # Right panel background + border
        self._counterflow_right_panel.setStyleSheet(f"""
            QWidget#counterflowRightPanel {{
                background: {thm['bg_surface']};
                border-left: 1px solid {thm['border']};
            }}
        """)

        # Customer card
        self._counterflow_cust_card.setStyleSheet(f"""
            QFrame#counterflowCustCard {{
                background: {thm['bg_app']};
                border: 1px solid {thm['border']};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        # Customer status label colour
        self._counterflow_customer_info.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )

        # Total card — always dark background with border
        self._counterflow_total_card.setStyleSheet(f"""
            QFrame {{
                background: #111827;
                border-radius: 12px;
                border: 1px solid {thm['border']};
            }}
        """)

        # Total label — always white on the dark card
        self._counterflow_total_label.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        # Item count label
        self._counterflow_item_count_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )

        # Find button
        self._counterflow_find_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {thm['text_primary']};
                border: 1.5px solid {thm['border']};
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {thm['hover']};
            }}
        """)

    # ── Event Handlers ─────────────────────────────────────────

    def _counterflow_on_barcode_entered(self):
        counterflow_barcode = self._counterflow_barcode_input.text().strip()
        if not counterflow_barcode:
            return
        self._counterflow_barcode_input.clear()

        counterflow_product = self.counterflow_inventory.counterflow_get_by_barcode(
            counterflow_barcode
        )
        if not counterflow_product:
            QMessageBox.warning(
                self, "CounterFlow — Not Found",
                f"No product found for barcode:\n{counterflow_barcode}"
            )
            return

        if counterflow_product.counterflow_stock_qty <= 0:
            QMessageBox.warning(
                self, "CounterFlow — Out of Stock",
                f"'{counterflow_product.counterflow_name}' is out of stock."
            )
            return

        self.counterflow_billing.counterflow_add_item(counterflow_product)
        self._counterflow_refresh_table()

    def _counterflow_on_mobile_entered(self):
        """
        CounterFlow — Look up a customer by the entered mobile number.
        Triggered explicitly by Enter key or the Find button only —
        never by editingFinished, which fires on any focus loss.
        """
        counterflow_mobile = self._counterflow_mobile_input.text().strip()

        if not counterflow_mobile:
            self._counterflow_customer_info.setText("Customer: Walk-in Customer")
            self._counterflow_name_input.setVisible(False)
            self._counterflow_name_input.clear()
            self._counterflow_is_new_customer = False
            self.counterflow_billing.counterflow_clear_customer()
            return

        # Strict validation — checks 10 digits AND 6/7/8/9 prefix;
        # strips +91 / leading-0 and returns the clean 10-digit number.
        counterflow_valid, counterflow_cleaned = _counterflow_validate_mobile_strict(
            counterflow_mobile
        )
        if not counterflow_valid:
            self._counterflow_customer_info.setText("⚠  Invalid mobile number")
            self._counterflow_name_input.setVisible(False)
            self._counterflow_is_new_customer = False
            return

        counterflow_customer = self.counterflow_customers.counterflow_get_by_mobile(
            counterflow_cleaned
        )
        if counterflow_customer:
            # Existing customer — show their details, hide name field
            self._counterflow_customer_info.setText(
                f"✓  {counterflow_customer.counterflow_name}  |  "
                f"Credit: ₹{counterflow_customer.counterflow_credit_balance:,.0f}"
                f" / ₹{counterflow_customer.counterflow_credit_limit:,.0f}"
            )
            self._counterflow_name_input.setVisible(False)
            self._counterflow_name_input.clear()
            self._counterflow_is_new_customer = False
            self.counterflow_billing.counterflow_bind_customer(
                counterflow_customer.counterflow_customer_id,
                counterflow_customer.counterflow_mobile,
                counterflow_customer.counterflow_name,
            )
        else:
            # New customer — ask cashier for their name before finalizing
            self._counterflow_customer_info.setText(
                "✦  New customer — enter name below"
            )
            self._counterflow_name_input.setVisible(True)
            self._counterflow_name_input.clear()
            self._counterflow_name_input.setFocus()
            self._counterflow_is_new_customer = True
            self.counterflow_billing.counterflow_bind_customer(
                None, counterflow_cleaned, ""
            )

        # Mark the current mobile value as verified — finalize can now
        # trust _counterflow_is_new_customer and the billing session state.
        self._counterflow_lookup_done = True
        # Unlock payment buttons now that a customer is verified.
        self._counterflow_update_pay_buttons()

    def _counterflow_on_mobile_text_changed(self):
        """
        CounterFlow — Reset lookup state whenever the cashier edits the
        mobile field. This forces a fresh Find/Enter lookup before the
        bill can be finalized with a customer attached.
        """
        self._counterflow_lookup_done = False
        self._counterflow_is_new_customer = False
        self.counterflow_billing.counterflow_clear_customer()
        # Re-lock payment buttons until the new number is verified.
        self._counterflow_update_pay_buttons()

    def _counterflow_finalize(self, method: str):
        """
        CounterFlow — Validate all constraints then commit the bill atomically.

        Constraints enforced (in order):
          1. Bill must not be empty
          2. CREDIT payment requires a valid mobile number
          3. Invalid mobile format blocks finalization
          4. New customer requires a name to be entered
        """
        # ── Constraint 1: non-empty bill ───────────────────────
        if self.counterflow_billing.counterflow_is_empty:
            QMessageBox.warning(
                self, "CounterFlow",
                "Please add at least one product before checkout."
            )
            return

        # ── Read and validate mobile ───────────────────────────
        counterflow_mobile_raw = self._counterflow_mobile_input.text().strip()
        counterflow_mobile     = None
        counterflow_customer_name = "CounterFlow Customer"

        if counterflow_mobile_raw:
            counterflow_valid, counterflow_cleaned_mobile = (
                _counterflow_validate_mobile_strict(counterflow_mobile_raw)
            )
            # ── Constraint 3: invalid mobile blocks finalization ─
            if not counterflow_valid:
                QMessageBox.warning(
                    self, "CounterFlow — Invalid Mobile Number",
                    "The mobile number entered is not valid.\n\n"
                    "Please correct it, or clear the field to proceed as a Walk-in customer."
                )
                self._counterflow_mobile_input.setFocus()
                self._counterflow_mobile_input.selectAll()
                return
            counterflow_mobile = counterflow_cleaned_mobile

        # ── Constraint 2: CREDIT requires a mobile ────────────
        if method == "CREDIT" and not counterflow_mobile:
            QMessageBox.warning(
                self, "CounterFlow — Customer Required",
                "Credit sales must be linked to a customer.\n\n"
                "Please enter the customer's mobile number before selecting CREDIT."
            )
            self._counterflow_mobile_input.setFocus()
            return

        # ── Constraint 2.5: mobile entered but Find never clicked ─
        # If the cashier typed a number and clicked Pay without pressing
        # Enter / Find, _counterflow_lookup_done is still False — the
        # customer database was never queried, so _counterflow_is_new_customer
        # is wrong and the billing session has no customer bound.
        # We auto-run the lookup here so the bill is always linked correctly.
        if counterflow_mobile and not self._counterflow_lookup_done:
            self._counterflow_on_mobile_entered()
            # If the lookup set an error (invalid number after re-check),
            # bail out. The status label already shows the ⚠ warning.
            if not self._counterflow_lookup_done:
                QMessageBox.warning(
                    self, "CounterFlow — Customer Lookup Required",
                    "The mobile number could not be verified.\n\n"
                    "Please press the 'Find' button (or Enter) to look up the customer "
                    "before finalizing the bill."
                )
                self._counterflow_mobile_input.setFocus()
                return

        # ── Constraint 4: new customer requires a name ─────────
        if counterflow_mobile and self._counterflow_is_new_customer:
            counterflow_entered_name = self._counterflow_name_input.text().strip()
            if not counterflow_entered_name:
                QMessageBox.warning(
                    self, "CounterFlow — Name Required",
                    "This is a new customer. Please enter their name before proceeding."
                )
                self._counterflow_name_input.setFocus()
                return
            counterflow_customer_name = counterflow_entered_name
        elif counterflow_mobile and not self._counterflow_is_new_customer:
            # Existing customer — name already stored, use it from billing session
            counterflow_customer_name = (
                self.counterflow_billing.counterflow_customer_name
                or "CounterFlow Customer"
            )

        # ── Finalize ───────────────────────────────────────────
        counterflow_finalizer = CounterFlowBillingFinalizer(self.counterflow_session)
        try:
            counterflow_invoice = counterflow_finalizer.counterflow_finalize(
                billing_session=self.counterflow_billing,
                payment_method=method,
                customer_mobile=counterflow_mobile,
                customer_name=counterflow_customer_name,
            )
            QMessageBox.information(
                self, "CounterFlow — Bill Finalized",
                f"Invoice {counterflow_invoice.counterflow_invoice_number} saved.\n"
                f"Total: ₹{counterflow_invoice.counterflow_total_amount:,.2f}\n"
                f"Payment: {method}"
            )
            self._counterflow_reset()
            self.counterflow_bill_finalized.emit()

        except CounterFlowCreditLimitError as e:
            counterflow_reply = QMessageBox.warning(
                self, "CounterFlow — Credit Limit Exceeded",
                f"⚠  {e.counterflow_customer.counterflow_name} has exceeded their credit limit.\n\n"
                f"Current Balance:  ₹{e.counterflow_customer.counterflow_credit_balance:,.2f}\n"
                f"Credit Limit:     ₹{e.counterflow_customer.counterflow_credit_limit:,.2f}\n"
                f"Bill Amount:      ₹{e.counterflow_bill_amount:,.2f}\n"
                f"Over by:          ₹{e.counterflow_over_by:,.2f}\n\n"
                f"Override and continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if counterflow_reply == QMessageBox.StandardButton.Yes:
                try:
                    counterflow_invoice = counterflow_finalizer.counterflow_finalize(
                        billing_session=self.counterflow_billing,
                        payment_method=method,
                        customer_mobile=counterflow_mobile,
                        customer_name=counterflow_customer_name,
                        force_credit_override=True,
                    )
                    QMessageBox.information(
                        self, "CounterFlow — Bill Finalized",
                        f"Invoice {counterflow_invoice.counterflow_invoice_number} saved.\n"
                        f"Total: ₹{counterflow_invoice.counterflow_total_amount:,.2f}\n"
                        f"Payment: {method}"
                    )
                    self._counterflow_reset()
                    self.counterflow_bill_finalized.emit()
                except Exception as ex:
                    QMessageBox.critical(self, "CounterFlow — Error", str(ex))

        except CounterFlowEmptyBillError as e:
            QMessageBox.warning(self, "CounterFlow", str(e))
        except ValueError as e:
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def _counterflow_cancel_bill(self):
        if not self.counterflow_billing.counterflow_is_empty:
            counterflow_reply = QMessageBox.question(
                self, "CounterFlow — Cancel Bill",
                "Discard the current bill?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if counterflow_reply != QMessageBox.StandardButton.Yes:
                return
        self._counterflow_reset()

    # ── Helpers ────────────────────────────────────────────────

    def _counterflow_refresh_table(self):
        thm = t.counterflow_theme()
        counterflow_items = self.counterflow_billing.counterflow_items
        self._counterflow_bill_table.setRowCount(len(counterflow_items))

        for row, item in enumerate(counterflow_items):
            self._counterflow_bill_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_bill_table.setItem(
                row, 0, self._cf_item(str(row + 1))
            )
            self._counterflow_bill_table.setItem(
                row, 1,
                self._cf_item(item.counterflow_product.counterflow_name)
            )
            self._counterflow_bill_table.setItem(
                row, 2,
                self._cf_item(f"₹{item.counterflow_product.counterflow_price:,.0f}")
            )
            self._counterflow_bill_table.setItem(
                row, 3,
                self._cf_item(str(item.counterflow_quantity))
            )
            self._counterflow_bill_table.setItem(
                row, 4,
                self._cf_item(f"₹{item.counterflow_line_total:,.0f}")
            )

            # Remove button
            counterflow_remove_btn = QPushButton("×")
            counterflow_remove_btn.setFixedSize(28, 28)
            counterflow_remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {thm['text_secondary']};
                    border: none;
                    font-size: 19px;
                    font-weight: bold;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    color: {thm['danger']};
                    background: {thm['danger_light']};
                }}
            """)
            pid = item.counterflow_product.counterflow_product_id
            counterflow_remove_btn.clicked.connect(
                lambda _, p=pid: self._counterflow_remove_item(p)
            )
            wrapper = QWidget()
            wl = QHBoxLayout(wrapper)
            wl.setContentsMargins(4, 0, 4, 0)
            wl.addWidget(counterflow_remove_btn)
            self._counterflow_bill_table.setCellWidget(row, 5, wrapper)

        self._counterflow_total_label.setText(
            f"₹{self.counterflow_billing.counterflow_total:,.2f}"
        )
        self._counterflow_item_count_label.setText(
            f"{self.counterflow_billing.counterflow_item_count} items in cart"
        )

        # Payment button state is controlled by customer verification,
        # not cart contents. _counterflow_update_pay_buttons() is the
        # single place that decides enabled/disabled.
        self._counterflow_update_pay_buttons()

    def _counterflow_remove_item(self, product_id: int):
        self.counterflow_billing.counterflow_remove_item(product_id)
        self._counterflow_refresh_table()

    def _counterflow_reset(self):
        self.counterflow_billing.counterflow_clear()
        self._counterflow_mobile_input.clear()
        self._counterflow_name_input.clear()
        self._counterflow_name_input.setVisible(False)
        self._counterflow_is_new_customer = False
        self._counterflow_lookup_done = False
        self._counterflow_customer_info.setText("Customer: Walk-in Customer")
        self._counterflow_refresh_table()
        QTimer.singleShot(100, self._counterflow_barcode_input.setFocus)

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
