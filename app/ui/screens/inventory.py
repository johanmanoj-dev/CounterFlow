"""
CounterFlow v1.0.0 — Inventory Screen
=======================================
Product list with search, add, and restock.
Stock qty shown as colored badge (green/amber/red).
Matches approved CounterFlow design exactly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QSpinBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.inventory_manager import CounterFlowInventoryManager
from app.core.auth import counterflow_auth_session
from app.ui.dialogs.add_product import CounterFlowAddProductDialog
from app import theme as t
from app.config import COUNTERFLOW_LOW_STOCK_THRESHOLD, COUNTERFLOW_STOCK_WARNING_THRESHOLD


# ── Restock Dialog ─────────────────────────────────────────────
class CounterFlowRestockDialog(QDialog):
    """CounterFlow — Restock product popup."""

    def __init__(self, product_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CounterFlow — Restock")
        self.setMinimumWidth(400)
        self._counterflow_build(product_name)

    def _counterflow_build(self, product_name: str):
        thm = t.counterflow_theme()
        self.setStyleSheet(f"background: {thm['bg_surface']};")

        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(32, 28, 32, 32)
        counterflow_layout.setSpacing(20)

        # Title
        counterflow_title = QLabel("Restock Product")
        counterflow_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counterflow_title.setStyleSheet(
            f"font-size: 20px; font-weight: 700; "
            f"color: {thm['text_primary']}; margin-bottom: 12px;"
        )
        counterflow_layout.addWidget(counterflow_title)

        # ── Side-by-Side Rows ──────────────────────────────────
        
        # Row 1: Product Name
        counterflow_product_row = QHBoxLayout()
        counterflow_product_label = QLabel("Product:")
        counterflow_product_label.setStyleSheet(f"color: {thm['text_secondary']}; font-weight: 600; font-size: 15px;")
        
        counterflow_product_val = QLabel(product_name)
        counterflow_product_val.setStyleSheet(f"color: {thm['text_primary']}; font-weight: 700; font-size: 15px;")
        
        counterflow_product_row.addWidget(counterflow_product_label)
        counterflow_product_row.addSpacing(12)
        counterflow_product_row.addWidget(counterflow_product_val)
        counterflow_product_row.addStretch()
        counterflow_layout.addLayout(counterflow_product_row)

        # Row 2: Quantity Input
        counterflow_qty_row = QHBoxLayout()
        counterflow_qty_label = QLabel("Quantity to Add:")
        counterflow_qty_label.setStyleSheet(f"color: {thm['text_secondary']}; font-weight: 600; font-size: 15px;")
        
        self._counterflow_qty = QSpinBox()
        self._counterflow_qty.setRange(1, 99999)
        self._counterflow_qty.setValue(1)
        self._counterflow_qty.setFixedWidth(100)
        self._counterflow_qty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        counterflow_qty_row.addWidget(counterflow_qty_label)
        counterflow_qty_row.addSpacing(12)
        counterflow_qty_row.addWidget(self._counterflow_qty)
        counterflow_qty_row.addStretch()
        counterflow_layout.addLayout(counterflow_qty_row)

        counterflow_layout.addSpacing(12)

        # Buttons
        counterflow_btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        counterflow_btns.setCenterButtons(False) # Left align matching the form
        counterflow_btns.accepted.connect(self.accept)
        counterflow_btns.rejected.connect(self.reject)
        counterflow_layout.addWidget(counterflow_btns)

    def counterflow_get_quantity(self) -> int:
        return self._counterflow_qty.value()

    def counterflow_get_reason(self) -> str:
        """CounterFlow — Returns a sensible default since reason is removed."""
        return "CounterFlow restock"


# ── Main Screen ────────────────────────────────────────────────
class CounterFlowInventoryScreen(QWidget):
    """CounterFlow — Inventory Management Screen."""

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session = counterflow_session
        self.counterflow_inv_mgr = CounterFlowInventoryManager(counterflow_session)
        self._counterflow_build()
        self.counterflow_refresh()

    def _counterflow_build(self):
        t.counterflow_theme()
        counterflow_layout = QVBoxLayout(self)
        counterflow_layout.setContentsMargins(32, 14, 32, 28)
        counterflow_layout.setSpacing(20)

        # ── Header ─────────────────────────────────────────────
        counterflow_header = QHBoxLayout()

        counterflow_title = QLabel("Inventory")
        counterflow_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        counterflow_title.setFixedHeight(46)
        counterflow_title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        counterflow_header.addWidget(counterflow_title)
        counterflow_header.addStretch()

        self._counterflow_search = QLineEdit()
        self._counterflow_search.setPlaceholderText("  ⌕  Search products...")
        self._counterflow_search.setMinimumWidth(240)
        self._counterflow_search.setMinimumHeight(46)
        
        counterflow_search_font = self._counterflow_search.font()
        counterflow_search_font.setPixelSize(17)
        self._counterflow_search.setFont(counterflow_search_font)
        self._counterflow_search.textChanged.connect(self.counterflow_refresh)
        counterflow_header.addWidget(self._counterflow_search)

        counterflow_add_btn = QPushButton("+ Add Product")
        counterflow_add_btn.setMinimumHeight(46)
        counterflow_add_btn.clicked.connect(self._counterflow_add_product)
        counterflow_header.addWidget(counterflow_add_btn)

        counterflow_restock_btn = QPushButton("↺  Restock")
        counterflow_restock_btn.setObjectName("counterflowOutlineBtn")
        counterflow_restock_btn.setMinimumHeight(46)
        counterflow_restock_btn.clicked.connect(self._counterflow_restock)
        counterflow_header.addWidget(counterflow_restock_btn)

        # ── Admin-only: Remove Product button ──────────────────
        if counterflow_auth_session.counterflow_is_admin:
            self._counterflow_remove_btn = QPushButton("🗑  Remove Product")
            self._counterflow_remove_btn.setObjectName("counterflowDangerBtn")
            self._counterflow_remove_btn.setMinimumHeight(46)
            self._counterflow_remove_btn.clicked.connect(self._counterflow_remove_product)
            counterflow_header.addWidget(self._counterflow_remove_btn)

        counterflow_layout.addLayout(counterflow_header)

        # ── Table ──────────────────────────────────────────────
        self._counterflow_table = QTableWidget()
        self._counterflow_table.setColumnCount(5)
        self._counterflow_table.setHorizontalHeaderLabels(
            ["ID", "Barcode", "Name", "Price", "Stock"]
        )
        self._counterflow_table.setShowGrid(True)
        self._counterflow_table.setAlternatingRowColors(False)
        self._counterflow_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._counterflow_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._counterflow_table.verticalHeader().setVisible(False)
        self._counterflow_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._counterflow_table.setColumnWidth(0, 85)
        self._counterflow_table.setColumnWidth(1, 195)
        self._counterflow_table.setColumnWidth(3, 135)
        self._counterflow_table.setColumnWidth(4, 115)
        # Double-clicking a row opens the restock dialog directly.
        self._counterflow_table.doubleClicked.connect(self._counterflow_restock)
        counterflow_layout.addWidget(self._counterflow_table)

    def counterflow_refresh(self):
        """CounterFlow — Reload inventory table from DB."""
        counterflow_query = (
            self._counterflow_search.text().strip()
            if hasattr(self, "_counterflow_search") else ""
        )
        counterflow_products = (
            self.counterflow_inv_mgr.counterflow_search_products(counterflow_query)
            if counterflow_query
            else self.counterflow_inv_mgr.counterflow_get_all_products()
        )

        self._counterflow_table.setRowCount(len(counterflow_products))
        for row, p in enumerate(counterflow_products):
            self._counterflow_table.setRowHeight(
                row, t.COUNTERFLOW_TABLE_ROW_HEIGHT
            )
            self._counterflow_table.setItem(
                row, 0, self._cf_item(str(p.counterflow_product_id))
            )
            self._counterflow_table.setItem(
                row, 1, self._cf_item(p.counterflow_barcode)
            )
            self._counterflow_table.setItem(
                row, 2, self._cf_item(p.counterflow_name)
            )
            self._counterflow_table.setItem(
                row, 3, self._cf_item(f"₹{p.counterflow_price:,.2f}")
            )
            # Stock badge
            counterflow_badge = self._counterflow_stock_badge(p.counterflow_stock_qty)
            self._counterflow_table.setCellWidget(row, 4, counterflow_badge)

    def _counterflow_stock_badge(self, qty: int) -> QWidget:
        thm = t.counterflow_theme()
        if qty <= COUNTERFLOW_LOW_STOCK_THRESHOLD:
            badge_bg = thm["stock_red_bg"]
            badge_fg = thm["stock_red"]
        elif qty <= COUNTERFLOW_STOCK_WARNING_THRESHOLD:
            badge_bg = thm["stock_amber_bg"]
            badge_fg = thm["stock_amber"]
        else:
            badge_bg = thm["stock_green_bg"]
            badge_fg = thm["stock_green"]

        badge = QLabel(str(qty))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(36, 24)
        badge.setStyleSheet(f"""
            background: {badge_bg};
            color: {badge_fg};
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
        """)
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(8, 0, 8, 0)
        wl.addWidget(badge)
        return wrapper

    def _counterflow_add_product(self):
        # Must use parent=self as a keyword argument. Passing self positionally
        # would bind it to counterflow_product (the first param), triggering edit
        # mode on the screen object and crashing in _counterflow_prefill().
        counterflow_dialog = CounterFlowAddProductDialog(parent=self)
        if counterflow_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        counterflow_data = counterflow_dialog.counterflow_get_data()

        if not counterflow_data["barcode"] or not counterflow_data["name"]:
            QMessageBox.warning(
                self, "CounterFlow",
                "Barcode and Name are required fields."
            )
            return
        try:
            self.counterflow_inv_mgr.counterflow_add_product(**counterflow_data)
            self.counterflow_session.commit()
            self.counterflow_refresh()
        except ValueError as e:
            # Always rollback — keeps session clean even if ValueError
            # was raised after a partial flush inside the manager.
            self.counterflow_session.rollback()
            QMessageBox.warning(self, "CounterFlow", str(e))
        except Exception as e:
            self.counterflow_session.rollback()
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def _counterflow_restock(self):
        counterflow_row = self._counterflow_table.currentRow()
        if counterflow_row < 0:
            QMessageBox.warning(
                self, "CounterFlow",
                "Please select a product row first.\n"
                "You can also double-click a product to restock it directly."
            )
            return

        counterflow_product_id   = int(
            self._counterflow_table.item(counterflow_row, 0).text()
        )
        counterflow_product_name = self._counterflow_table.item(
            counterflow_row, 2
        ).text()

        counterflow_dialog = CounterFlowRestockDialog(counterflow_product_name, self)
        if counterflow_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.counterflow_inv_mgr.counterflow_restock(
                product_id=counterflow_product_id,
                quantity=counterflow_dialog.counterflow_get_quantity(),
                reason=counterflow_dialog.counterflow_get_reason(),
            )
            self.counterflow_session.commit()
            self.counterflow_refresh()
            # Re-select and scroll to the updated row so the cashier can
            # confirm the new stock number without hunting for the product.
            self._counterflow_table.selectRow(counterflow_row)
            self._counterflow_table.scrollTo(
                self._counterflow_table.model().index(counterflow_row, 0)
            )
        except Exception as e:
            self.counterflow_session.rollback()
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def _counterflow_remove_product(self):
        """CounterFlow — Admin-only: soft-delete selected product."""
        counterflow_row = self._counterflow_table.currentRow()
        if counterflow_row < 0:
            QMessageBox.warning(
                self, "CounterFlow",
                "Please select a product row first."
            )
            return

        counterflow_product_id   = int(self._counterflow_table.item(counterflow_row, 0).text())
        counterflow_product_name = self._counterflow_table.item(counterflow_row, 2).text()

        reply = QMessageBox.warning(
            self,
            "CounterFlow — Remove Product",
            f"Remove  \"{counterflow_product_name}\"  from inventory?\n\n"
            f"The product will be hidden from all screens and the POS scanner.\n"
            f"Existing invoices and sales history are NOT affected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.counterflow_inv_mgr.counterflow_delete_product(counterflow_product_id)
            self.counterflow_session.commit()
            self.counterflow_refresh()
            QMessageBox.information(
                self, "CounterFlow — Product Removed",
                f"\"{counterflow_product_name}\" has been removed from inventory."
            )
        except Exception as e:
            self.counterflow_session.rollback()
            QMessageBox.critical(self, "CounterFlow — Error", str(e))

    def counterflow_refresh_theme(self):
        """CounterFlow — Rebuild table after theme change so stock badges
        pick up dark-mode-aware accent colours."""
        self.counterflow_refresh()

    def _cf_item(self, text: str, align=Qt.AlignmentFlag.AlignCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(align)
        return item
