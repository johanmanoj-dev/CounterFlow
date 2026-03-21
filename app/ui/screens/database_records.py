"""
CounterFlow v1.0.0 — Database & Records Screen
================================================
Filter transactions by date range, payment method,
and customer. Quick filter buttons. Export to CSV.
Expandable rows show item detail. Summary bar.
Matches approved CounterFlow design exactly.
"""

import csv
from datetime import date, timedelta, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDateEdit, QFileDialog,
    QMessageBox, QFrame, QCompleter, QApplication
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QIcon

from app.core.report_generator import CounterFlowReportGenerator
from app.core.customer_manager import CounterFlowCustomerManager
from app import theme as t


class CounterFlowDatabaseScreen(QWidget):
    """CounterFlow — Database & Records Screen."""

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session  = counterflow_session
        self.counterflow_reporter = CounterFlowReportGenerator(counterflow_session)
        self.counterflow_cust_mgr = CounterFlowCustomerManager(counterflow_session)
        self._counterflow_current_invoices = []
        self._counterflow_expanded_row: int = -1   # table row index of open detail row, or -1
        self._counterflow_build()
        self._counterflow_apply_quick_filter("today")

    def _counterflow_build(self):
        thm = t.counterflow_theme()
        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(32, 28, 32, 28)
        counterflow_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────
        counterflow_title = QLabel("Database & Records")
        counterflow_title_font = QFont("Segoe UI", 23)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # ── Date + Dropdown filters ────────────────────────────
        counterflow_filter_row1 = QHBoxLayout()
        counterflow_filter_row1.setSpacing(12)

        # From date
    
        self._counterflow_from_date = QDateEdit()
        self._counterflow_from_date.setCalendarPopup(True)
        self._counterflow_from_date.setDate(
            QDate.currentDate().addDays(-30)
        )
        self._counterflow_from_date.setDisplayFormat("dd / MM / yyyy")
        self._counterflow_from_date.setMinimumWidth(140)

        self._counterflow_to_lbl = QLabel("to")
        self._counterflow_to_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 16px;"
        )

        self._counterflow_to_date = QDateEdit()
        self._counterflow_to_date.setCalendarPopup(True)
        self._counterflow_to_date.setDate(QDate.currentDate())
        self._counterflow_to_date.setDisplayFormat("dd / MM / yyyy")
        self._counterflow_to_date.setMinimumWidth(140)

        # Payment method dropdown
        self._counterflow_method_combo = QComboBox()
        self._counterflow_method_combo.addItems(
            ["All Methods", "CASH", "UPI", "CREDIT"]
        )
        self._counterflow_method_combo.setMinimumWidth(140)

        # Customer filter — searchable combo box
        self._counterflow_customer_combo = QComboBox()
        self._counterflow_customer_combo.setEditable(True)
        self._counterflow_customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._counterflow_customer_combo.setMinimumWidth(160)
        
        # Configure search behavior
        self._counterflow_customer_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._counterflow_customer_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        
        if self._counterflow_customer_combo.lineEdit():
            self._counterflow_customer_combo.lineEdit().setPlaceholderText("Search customer...")
        
        self._counterflow_customer_combo.addItem("All Customers")
        counterflow_customers = self.counterflow_cust_mgr.counterflow_get_all_customers()
        for c in counterflow_customers:
            self._counterflow_customer_combo.addItem(
                c.counterflow_name,
                c.counterflow_customer_id
            )

        counterflow_filter_row1.addWidget(self._counterflow_from_date)
        counterflow_filter_row1.addWidget(self._counterflow_to_lbl)
        counterflow_filter_row1.addWidget(self._counterflow_to_date)
        counterflow_filter_row1.addWidget(self._counterflow_method_combo)
        counterflow_filter_row1.addWidget(self._counterflow_customer_combo)
        counterflow_filter_row1.addStretch()
        counterflow_layout.addLayout(counterflow_filter_row1)

        # ── Quick filters + action buttons ─────────────────────
        counterflow_filter_row2 = QHBoxLayout()
        counterflow_filter_row2.setSpacing(8)

        self._counterflow_quick_btns = {}
        for key, label in [
            ("today",      "Today"),
            ("week",       "Week"),
            ("month",      "Month"),
            ("last_month", "Last Month"),
            ("all",        "All Time"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("counterflowFilterBtn")
            btn.setCheckable(True)
            btn.clicked.connect(
                lambda checked, k=key: self._counterflow_apply_quick_filter(k)
            )
            self._counterflow_quick_btns[key] = btn
            counterflow_filter_row2.addWidget(btn)

        counterflow_filter_row2.addStretch()

        counterflow_apply_btn = QPushButton("Apply Filters")
        counterflow_apply_btn.setObjectName("counterflowOutlineBtn")
        counterflow_apply_btn.setMinimumHeight(42)
        counterflow_apply_btn.clicked.connect(self._counterflow_apply_filters)
        counterflow_filter_row2.addWidget(counterflow_apply_btn)

        self._counterflow_csv_btn = QPushButton("Export CSV")
        self._counterflow_csv_btn.setObjectName("counterflowOutlineBtn")
        self._counterflow_csv_btn.setMinimumHeight(42)
        self._counterflow_csv_btn.clicked.connect(self._counterflow_export_csv)
        self._counterflow_csv_btn.setIcon(QIcon.fromTheme("document-save"))
        counterflow_filter_row2.addWidget(self._counterflow_csv_btn)

        counterflow_layout.addLayout(counterflow_filter_row2)

        # ── Summary bar ────────────────────────────────────────
        counterflow_summary_row = QHBoxLayout()
        counterflow_summary_row.setSpacing(12)

        self._counterflow_showing_label = QLabel("Showing 0 records  |  Total amount: ₹0")
        self._counterflow_showing_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )
        counterflow_summary_row.addWidget(self._counterflow_showing_label)
        counterflow_summary_row.addStretch()

        self._counterflow_cash_summary   = self._counterflow_summary_pill("Cash",   "₹0", thm["cash_text"],    thm["cash_light"])
        self._counterflow_upi_summary    = self._counterflow_summary_pill("UPI",    "₹0", thm["upi_text"],     thm["upi_light"])
        self._counterflow_credit_summary = self._counterflow_summary_pill("Credit", "₹0", thm["warning_text"], thm["warning_light"])

        counterflow_summary_row.addWidget(self._counterflow_cash_summary)
        counterflow_summary_row.addWidget(self._counterflow_upi_summary)
        counterflow_summary_row.addWidget(self._counterflow_credit_summary)
        counterflow_layout.addLayout(counterflow_summary_row)

        # ── Results table ──────────────────────────────────────
        # ── Results table card ─────────────────────────────────
        self._counterflow_results_card = QFrame()
        self._counterflow_results_card.setStyleSheet(f"""
            QFrame {{
                background: {thm['bg_surface']};
                border: 1px solid {thm['card_border']};
                border-radius: 12px;
            }}
        """)
        results_card_layout = QVBoxLayout(self._counterflow_results_card)
        results_card_layout.setContentsMargins(1, 1, 1, 1)
        results_card_layout.setSpacing(0)

        self._counterflow_results_table = QTableWidget()
        self._counterflow_results_table.setColumnCount(7)
        self._counterflow_results_table.setHorizontalHeaderLabels(
            ["", "Invoice #", "Date", "Customer", "Total", "Method", "Items"]
        )
        self._counterflow_results_table.setShowGrid(True)
        self._counterflow_results_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._counterflow_results_table.verticalHeader().setVisible(False)
        self._counterflow_results_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_results_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counterflow_results_table.setColumnWidth(0, 35)
        self._counterflow_results_table.setColumnWidth(1, 135)
        self._counterflow_results_table.setColumnWidth(2, 155)
        self._counterflow_results_table.setColumnWidth(4, 125)
        self._counterflow_results_table.setColumnWidth(5, 125)
        self._counterflow_results_table.setColumnWidth(6, 95)
        
        # Consistent header rounding
        self._counterflow_results_table.horizontalHeader().setStyleSheet(f"""
            QHeaderView {{
                background: transparent;
                border: none;
                border-top-left-radius: 11px;
                border-top-right-radius: 11px;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 11px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 11px;
            }}
        """)
        self._counterflow_results_table.setStyleSheet("border: none; background: transparent;")
        
        self._counterflow_results_table.cellClicked.connect(
            self._counterflow_on_row_clicked
        )
        results_card_layout.addWidget(self._counterflow_results_table)
        counterflow_layout.addWidget(self._counterflow_results_card)

    def _counterflow_summary_pill(self, label, value, fg, bg) -> QLabel:
        thm = t.counterflow_theme()
        pill = QLabel(f"{label}: {value}")
        pill.setStyleSheet(f"""
            background: {thm['bg_surface']};
            color: {thm['text_primary']};
            border: 1px solid {thm['border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 16px;
            font-weight: 600;
        """)
        return pill

    def counterflow_refresh_theme(self):
        """CounterFlow — Restyle all inline-styled widgets and rebuild
        the results table after a dark/light mode toggle."""
        thm = t.counterflow_theme()
        # Summary label
        self._counterflow_showing_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 15px;"
        )
        # 'to' label
        self._counterflow_to_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 16px;"
        )
        # Summary pills
        pill_style = f"""
            background: {thm['bg_surface']};
            color: {thm['text_primary']};
            border: 1px solid {thm['border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 16px;
            font-weight: 600;
        """
        self._counterflow_cash_summary.setStyleSheet(pill_style)
        self._counterflow_upi_summary.setStyleSheet(pill_style)
        self._counterflow_credit_summary.setStyleSheet(pill_style)
        # Rebuild table to refresh payment badges with current theme
        self._counterflow_populate_table()

    def _counterflow_apply_quick_filter(self, key: str):
        """CounterFlow — Apply a quick date filter."""
        today = date.today()

        for k, btn in self._counterflow_quick_btns.items():
            btn.setChecked(k == key)

        if key == "today":
            start, end = today, today
        elif key == "week":
            start = today - timedelta(days=today.weekday())
            end   = today
        elif key == "month":
            start = today.replace(day=1)
            end   = today
        elif key == "last_month":
            counterflow_first_this = today.replace(day=1)
            counterflow_last_prev  = counterflow_first_this - timedelta(days=1)
            start = counterflow_last_prev.replace(day=1)
            end   = counterflow_last_prev
        else:
            start = date(2000, 1, 1)
            end   = today

        self._counterflow_from_date.setDate(
            QDate(start.year, start.month, start.day)
        )
        self._counterflow_to_date.setDate(
            QDate(end.year, end.month, end.day)
        )
        self._counterflow_apply_filters()

    def _counterflow_refresh_customer_combo(self):
        """CounterFlow — Repopulate the customer filter dropdown from the DB.

        Called at the top of every filter apply so that customers created
        during the session (via POS checkout or Customers screen) appear
        without requiring an app restart.
        """
        counterflow_current_id = self._counterflow_customer_combo.currentData()
        self._counterflow_customer_combo.blockSignals(True)
        self._counterflow_customer_combo.clear()
        self._counterflow_customer_combo.addItem("All Customers")
        for c in self.counterflow_cust_mgr.counterflow_get_all_customers():
            self._counterflow_customer_combo.addItem(
                c.counterflow_name,
                c.counterflow_customer_id
            )
        # Restore previous selection if the customer still exists
        counterflow_restore_idx = self._counterflow_customer_combo.findData(
            counterflow_current_id
        )
        self._counterflow_customer_combo.setCurrentIndex(
            max(0, counterflow_restore_idx)
        )
        
        # Ensure search settings are reapplied if needed (though usually persistent)
        self._counterflow_customer_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._counterflow_customer_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        
        self._counterflow_customer_combo.blockSignals(False)

    def _counterflow_apply_filters(self):
        """CounterFlow — Filter invoices and refresh table."""
        # Refresh the customer dropdown so newly-created customers are visible
        self._counterflow_refresh_customer_combo()

        counterflow_from = self._counterflow_from_date.date().toPyDate()
        counterflow_to   = self._counterflow_to_date.date().toPyDate()
        counterflow_method = self._counterflow_method_combo.currentText()
        counterflow_customer_idx = self._counterflow_customer_combo.currentIndex()

        counterflow_all = self.counterflow_reporter.counterflow_invoices_by_date_range(
            counterflow_from, counterflow_to
        )

        # Filter by method
        if counterflow_method != "All Methods":
            counterflow_all = [
                i for i in counterflow_all
                if i.counterflow_payment_method == counterflow_method
            ]

        # Filter by customer
        if counterflow_customer_idx > 0:
            counterflow_cust_id = self._counterflow_customer_combo.itemData(
                counterflow_customer_idx
            )
            counterflow_all = [
                i for i in counterflow_all
                if i.counterflow_customer_id == counterflow_cust_id
            ]

        self._counterflow_current_invoices = counterflow_all
        self._counterflow_populate_table()

    def _counterflow_populate_table(self):
        t.counterflow_theme()
        invoices = self._counterflow_current_invoices

        # Reset any open detail row — we're rebuilding from scratch
        self._counterflow_expanded_row = -1

        # Summary
        total = sum(i.counterflow_total_amount for i in invoices)
        cash  = sum(i.counterflow_total_amount for i in invoices if i.counterflow_payment_method == "CASH")
        upi   = sum(i.counterflow_total_amount for i in invoices if i.counterflow_payment_method == "UPI")
        credit = sum(i.counterflow_total_amount for i in invoices if i.counterflow_payment_method == "CREDIT")

        self._counterflow_showing_label.setText(
            f"Showing <b>{len(invoices)}</b> records  |  "
            f"Total amount: <b>₹{total:,.0f}</b>"
        )
        self._counterflow_cash_summary.setText(f"Cash:  ₹{cash:,.0f}")
        self._counterflow_upi_summary.setText(f"UPI:  ₹{upi:,.0f}")
        self._counterflow_credit_summary.setText(f"Credit:  ₹{credit:,.0f}")

        self._counterflow_results_table.setRowCount(len(invoices))
        for row, inv in enumerate(invoices):
            self._counterflow_results_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            # Expand arrow
            counterflow_arrow = self._cf_item("›")
            counterflow_arrow.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._counterflow_results_table.setItem(row, 0, counterflow_arrow)

            self._counterflow_results_table.setItem(
                row, 1, self._cf_item(inv.counterflow_invoice_number)
            )
            self._counterflow_results_table.setItem(
                row, 2,
                self._cf_item(inv.counterflow_created_at.strftime("%Y-%m-%d"))
            )
            customer_name = (
                inv.counterflow_customer.counterflow_name
                if inv.counterflow_customer else "Walk-in"
            )
            self._counterflow_results_table.setItem(
                row, 3, self._cf_item(customer_name)
            )
            self._counterflow_results_table.setItem(
                row, 4,
                self._cf_item(f"₹{inv.counterflow_total_amount:,.0f}")
            )
            # Badge
            badge = self._counterflow_payment_badge(inv.counterflow_payment_method)
            self._counterflow_results_table.setCellWidget(row, 5, badge)

            self._counterflow_results_table.setItem(
                row, 6,
                self._cf_item(str(len(inv.counterflow_items)))
            )

    def _counterflow_on_row_clicked(self, row, col):
        """CounterFlow — Toggle item detail row below clicked invoice row.

        Tracks a single expanded detail row and collapses it before
        opening another, preventing unlimited row insertion on every click.
        """
        if row < 0:
            return

        # If a detail row is already open, collapse it first.
        # Collapsing shifts all row indices below it up by one — account for that.
        if self._counterflow_expanded_row >= 0:
            self._counterflow_results_table.removeRow(self._counterflow_expanded_row)
            # If the user clicked the same invoice row that was already open, just close it.
            counterflow_collapsed_invoice_row = self._counterflow_expanded_row - 1
            self._counterflow_expanded_row = -1
            if row == counterflow_collapsed_invoice_row:
                return
            # Adjust the clicked row index if it was below the removed detail row
            if row > counterflow_collapsed_invoice_row:
                row -= 1

        # Safety guard after possible index adjustment
        if row < 0 or row >= len(self._counterflow_current_invoices):
            return

        inv = self._counterflow_current_invoices[row]

        # Build detail string
        counterflow_lines = []
        for item in inv.counterflow_items:
            counterflow_lines.append(
                f"  {item.counterflow_product.counterflow_name}  ×{item.counterflow_quantity}  "
                f"@ ₹{item.counterflow_unit_price:,.2f}  =  ₹{item.counterflow_line_total:,.2f}"
            )
        counterflow_detail = "\n".join(counterflow_lines)

        # Insert detail row directly below the clicked row
        counterflow_detail_row = row + 1
        self._counterflow_results_table.insertRow(counterflow_detail_row)
        self._counterflow_results_table.setRowHeight(
            counterflow_detail_row,
            24 * max(1, len(inv.counterflow_items)) + 16
        )

        counterflow_detail_cell = QTableWidgetItem(counterflow_detail)
        counterflow_detail_cell.setFlags(
            counterflow_detail_cell.flags() & ~Qt.ItemFlag.ItemIsEditable
        )
        thm = t.counterflow_theme()
        counterflow_detail_cell.setBackground(QColor(thm["bg_surface"]))
        counterflow_detail_cell.setForeground(QColor(thm["text_primary"]))
        self._counterflow_results_table.setItem(
            counterflow_detail_row, 1, counterflow_detail_cell
        )
        self._counterflow_results_table.setSpan(
            counterflow_detail_row, 1, 1, 6
        )

        # Remember which table row the open detail lives on
        self._counterflow_expanded_row = counterflow_detail_row

    def _counterflow_export_csv(self):
        """
        CounterFlow — Export filtered results to CSV file.
        Uses UTF-8-SIG for Excel compatibility.
        """
        if not self._counterflow_current_invoices:
            QMessageBox.information(
                self, "CounterFlow",
                "No records to export. Please apply filters first."
            )
            return

        # Prepare default filename with today's date
        counterflow_default_name = f"counterflow_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        counterflow_path, _ = QFileDialog.getSaveFileName(
            self, "CounterFlow — Export CSV (Excel Compatible)",
            counterflow_default_name,
            "CSV Files (*.csv)"
        )
        if not counterflow_path:
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            with open(counterflow_path, "w", newline="", encoding="utf-8-sig") as f:
                # Add sep=, for Excel to immediately recognize the delimiter
                f.write("sep=,\n")
                
                counterflow_writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                
                # Header row
                counterflow_writer.writerow([
                    "Invoice #", "Date", "Customer", "Payment Method",
                    "Product", "Quantity", "Unit Price", "Line Total",
                    "Invoice Grand Total"
                ])
                
                # Data rows (itemized)
                for inv in self._counterflow_current_invoices:
                    customer_name = inv.counterflow_customer.counterflow_name if inv.counterflow_customer else "Walk-in"
                    for item in inv.counterflow_items:
                        counterflow_writer.writerow([
                            inv.counterflow_invoice_number,
                            inv.counterflow_created_at.strftime("%Y-%m-%d %H:%M"),
                            customer_name,
                            inv.counterflow_payment_method,
                            item.counterflow_product.counterflow_name,
                            item.counterflow_quantity,
                            f"{item.counterflow_unit_price:.2f}",
                            f"{item.counterflow_line_total:.2f}",
                            f"{inv.counterflow_total_amount:.2f}",
                        ])
            
            QApplication.restoreOverrideCursor()
            QMessageBox.information(
                self, "CounterFlow — Export Complete",
                f"Successfully exported {len(self._counterflow_current_invoices)} records to CSV."
            )
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "CounterFlow — Export Failed", f"An error occurred: {str(e)}")

    def _counterflow_payment_badge(self, method: str) -> QWidget:
        thm = t.counterflow_theme()
        badge = QLabel(method)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if method == "UPI":
            bg, fg = thm["upi_light"],     thm["upi_text"]
        elif method == "CASH":
            bg, fg = thm["cash_light"],    thm["cash_text"]
        else:
            bg, fg = thm["warning_light"], thm["warning_text"]
        badge.setStyleSheet(f"""
            background: {bg};
            color: {thm['text_primary']};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 14px;
            font-weight: bold;
        """)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)
        wl.addWidget(badge)
        return wrapper

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
