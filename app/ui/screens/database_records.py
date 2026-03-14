"""
CounterFlow v1.0.0 — Database & Records Screen
================================================
Filter transactions by date range, payment method,
and customer. Quick filter buttons. Export to CSV.
Expandable rows show item detail. Summary bar.
Matches approved CounterFlow design exactly.
"""

import csv
import os
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDateEdit, QFileDialog,
    QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

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
        counterflow_title_font = QFont("Segoe UI", 20)
        counterflow_title_font.setWeight(QFont.Weight.Bold)
        counterflow_title.setFont(counterflow_title_font)
        counterflow_layout.addWidget(counterflow_title)

        # ── Date + Dropdown filters ────────────────────────────
        counterflow_filter_row1 = QHBoxLayout()
        counterflow_filter_row1.setSpacing(12)

        # From date
        counterflow_cal_icon = QLabel("📅")
        self._counterflow_from_date = QDateEdit()
        self._counterflow_from_date.setCalendarPopup(True)
        self._counterflow_from_date.setDate(
            QDate.currentDate().addDays(-30)
        )
        self._counterflow_from_date.setDisplayFormat("dd / MM / yyyy")
        self._counterflow_from_date.setMinimumWidth(140)

        self._counterflow_to_lbl = QLabel("to")
        self._counterflow_to_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 13px;"
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

        # Customer dropdown
        self._counterflow_customer_combo = QComboBox()
        self._counterflow_customer_combo.setMinimumWidth(160)
        self._counterflow_customer_combo.addItem("All Customers")
        counterflow_customers = self.counterflow_cust_mgr.counterflow_get_all_customers()
        for c in counterflow_customers:
            self._counterflow_customer_combo.addItem(
                c.counterflow_name,
                c.counterflow_customer_id
            )

        counterflow_filter_row1.addWidget(counterflow_cal_icon)
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
        counterflow_apply_btn.setMinimumHeight(36)
        counterflow_apply_btn.clicked.connect(self._counterflow_apply_filters)
        counterflow_filter_row2.addWidget(counterflow_apply_btn)

        counterflow_export_btn = QPushButton("⬇  Export CSV")
        counterflow_export_btn.setObjectName("counterflowOutlineBtn")
        counterflow_export_btn.setMinimumHeight(36)
        counterflow_export_btn.clicked.connect(self._counterflow_export_csv)
        counterflow_filter_row2.addWidget(counterflow_export_btn)

        counterflow_layout.addLayout(counterflow_filter_row2)

        # ── Summary bar ────────────────────────────────────────
        counterflow_summary_row = QHBoxLayout()
        counterflow_summary_row.setSpacing(12)

        self._counterflow_showing_label = QLabel("Showing 0 records  |  Total amount: ₹0")
        self._counterflow_showing_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
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
        self._counterflow_results_table = QTableWidget()
        self._counterflow_results_table.setColumnCount(7)
        self._counterflow_results_table.setHorizontalHeaderLabels(
            ["", "Invoice #", "Date", "Customer", "Total", "Method", "Items"]
        )
        self._counterflow_results_table.setShowGrid(False)
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
        self._counterflow_results_table.setColumnWidth(0, 30)
        self._counterflow_results_table.setColumnWidth(1, 100)
        self._counterflow_results_table.setColumnWidth(2, 120)
        self._counterflow_results_table.setColumnWidth(4, 90)
        self._counterflow_results_table.setColumnWidth(5, 90)
        self._counterflow_results_table.setColumnWidth(6, 60)
        self._counterflow_results_table.cellClicked.connect(
            self._counterflow_on_row_clicked
        )
        counterflow_layout.addWidget(self._counterflow_results_table)

    def _counterflow_summary_pill(self, label, value, fg, bg) -> QLabel:
        thm = t.counterflow_theme()
        pill = QLabel(f"{label}: {value}")
        pill.setStyleSheet(f"""
            background: {thm['bg_surface']};
            color: {thm['text_secondary']};
            border: 1px solid {thm['border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 13px;
        """)
        return pill

    def counterflow_refresh_theme(self):
        """CounterFlow — Restyle all inline-styled widgets and rebuild
        the results table after a dark/light mode toggle."""
        thm = t.counterflow_theme()
        # Summary label
        self._counterflow_showing_label.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px;"
        )
        # 'to' label
        self._counterflow_to_lbl.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 13px;"
        )
        # Summary pills
        pill_style = f"""
            background: {thm['bg_surface']};
            color: {thm['text_secondary']};
            border: 1px solid {thm['border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 13px;
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
        thm = t.counterflow_theme()
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
        counterflow_detail_cell.setBackground(QColor(thm["table_row_alt"]))
        counterflow_detail_cell.setForeground(QColor(thm["text_secondary"]))
        self._counterflow_results_table.setItem(
            counterflow_detail_row, 1, counterflow_detail_cell
        )
        self._counterflow_results_table.setSpan(
            counterflow_detail_row, 1, 1, 6
        )

        # Remember which table row the open detail lives on
        self._counterflow_expanded_row = counterflow_detail_row

    def _counterflow_export_csv(self):
        """CounterFlow — Export filtered results to CSV file."""
        if not self._counterflow_current_invoices:
            QMessageBox.information(
                self, "CounterFlow",
                "No records to export."
            )
            return

        counterflow_path, _ = QFileDialog.getSaveFileName(
            self, "CounterFlow — Export CSV",
            "counterflow_records.csv",
            "CSV Files (*.csv)"
        )
        if not counterflow_path:
            return

        try:
            with open(counterflow_path, "w", newline="", encoding="utf-8") as f:
                counterflow_writer = csv.writer(f)
                counterflow_writer.writerow([
                    "Invoice #", "Date", "Customer",
                    "Total", "Payment Method", "Items"
                ])
                for inv in self._counterflow_current_invoices:
                    counterflow_writer.writerow([
                        inv.counterflow_invoice_number,
                        inv.counterflow_created_at.strftime("%Y-%m-%d %H:%M"),
                        inv.counterflow_customer.counterflow_name if inv.counterflow_customer else "Walk-in",
                        inv.counterflow_total_amount,
                        inv.counterflow_payment_method,
                        len(inv.counterflow_items),
                    ])
            QMessageBox.information(
                self, "CounterFlow — Export Complete",
                f"Exported {len(self._counterflow_current_invoices)} records."
            )
        except Exception as e:
            QMessageBox.critical(self, "CounterFlow — Export Failed", str(e))

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
            color: {fg};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)
        wl.addWidget(badge)
        return wrapper

    def _cf_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item
