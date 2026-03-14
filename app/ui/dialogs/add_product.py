"""
CounterFlow v1.0.0 — Add Product Dialog
=========================================
Standalone dialog for adding a new product
or editing an existing one. Used from the
Inventory screen. Validates all fields before
accepting.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QFrame, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app import theme as t


class CounterFlowAddProductDialog(QDialog):
    """
    CounterFlow — Add / Edit Product Dialog.

    Usage:
        dialog = CounterFlowAddProductDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.counterflow_get_data()

    Pass counterflow_product to pre-fill for editing.
    """

    def __init__(self, counterflow_product=None, parent=None):
        super().__init__(parent)
        self._counterflow_product = counterflow_product
        self._counterflow_is_edit = counterflow_product is not None

        self.setWindowTitle(
            "CounterFlow — Edit Product"
            if self._counterflow_is_edit
            else "CounterFlow — Add Product"
        )
        self.setMinimumWidth(440)
        self.setModal(True)
        self._counterflow_build()

        if self._counterflow_is_edit:
            self._counterflow_prefill()

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

        # ── Header ─────────────────────────────────────────────
        counterflow_header_label = QLabel(
            "Edit Product" if self._counterflow_is_edit else "Add New Product"
        )
        counterflow_header_font = QFont("Segoe UI", 17)
        counterflow_header_font.setWeight(QFont.Weight.Bold)
        counterflow_header_label.setFont(counterflow_header_font)
        counterflow_root.addWidget(counterflow_header_label)

        counterflow_sub = QLabel(
            "Update the product details below."
            if self._counterflow_is_edit
            else "Fill in the details to add a new product to inventory."
        )
        counterflow_sub.setStyleSheet(
            f"color: {thm['text_secondary']}; font-size: 12px; margin-bottom: 4px;"
        )
        counterflow_root.addWidget(counterflow_sub)
        counterflow_root.addSpacing(20)

        # ── Divider ────────────────────────────────────────────
        counterflow_root.addWidget(self._counterflow_divider())
        counterflow_root.addSpacing(20)

        # ── Fields ─────────────────────────────────────────────
        counterflow_fields = QVBoxLayout()
        counterflow_fields.setSpacing(14)

        # Barcode
        self._counterflow_barcode = self._counterflow_field(
            counterflow_fields,
            label="Barcode *",
            placeholder="Scan or type barcode",
            hint="Must be unique across all products."
        )
        if self._counterflow_is_edit:
            self._counterflow_barcode.setReadOnly(True)
            self._counterflow_barcode.setStyleSheet(
                f"background: {thm['table_header_bg']}; "
                f"color: {thm['text_secondary']};"
            )

        # Name
        self._counterflow_name = self._counterflow_field(
            counterflow_fields,
            label="Product Name *",
            placeholder="Enter product name",
        )

        # Price
        counterflow_price_label = QLabel("Price *")
        counterflow_price_label.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {thm['text_secondary']};"
        )
        counterflow_fields.addWidget(counterflow_price_label)

        self._counterflow_price = QDoubleSpinBox()
        self._counterflow_price.setRange(0.01, 9_999_999.00)
        self._counterflow_price.setPrefix("₹ ")
        self._counterflow_price.setDecimals(2)
        self._counterflow_price.setMinimumHeight(t.COUNTERFLOW_INPUT_HEIGHT)
        counterflow_fields.addWidget(self._counterflow_price)

        # Stock qty (only for new products)
        if not self._counterflow_is_edit:
            counterflow_qty_label = QLabel("Initial Stock Quantity")
            counterflow_qty_label.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {thm['text_secondary']};"
            )
            counterflow_fields.addWidget(counterflow_qty_label)

            self._counterflow_qty = QSpinBox()
            self._counterflow_qty.setRange(0, 99_999)
            self._counterflow_qty.setValue(0)
            self._counterflow_qty.setMinimumHeight(t.COUNTERFLOW_INPUT_HEIGHT)
            counterflow_fields.addWidget(self._counterflow_qty)
        else:
            self._counterflow_qty = None

        counterflow_root.addLayout(counterflow_fields)
        counterflow_root.addSpacing(24)

        # ── Action Buttons ─────────────────────────────────────
        counterflow_btn_row = QHBoxLayout()
        counterflow_btn_row.setSpacing(10)

        counterflow_cancel_btn = QPushButton("Cancel")
        counterflow_cancel_btn.setObjectName("counterflowOutlineBtn")
        counterflow_cancel_btn.setMinimumHeight(40)
        counterflow_cancel_btn.clicked.connect(self.reject)

        counterflow_save_btn = QPushButton(
            "Save Changes" if self._counterflow_is_edit else "Add Product"
        )
        counterflow_save_btn.setMinimumHeight(40)
        counterflow_save_btn.setMinimumWidth(140)
        counterflow_save_btn.clicked.connect(self._counterflow_validate_and_accept)

        counterflow_btn_row.addStretch()
        counterflow_btn_row.addWidget(counterflow_cancel_btn)
        counterflow_btn_row.addWidget(counterflow_save_btn)
        counterflow_root.addLayout(counterflow_btn_row)

    def _counterflow_field(
        self,
        layout: QVBoxLayout,
        label: str,
        placeholder: str = "",
        hint: str = "",
    ) -> QLineEdit:
        """CounterFlow — Helper to add a labeled input field."""
        thm = t.counterflow_theme()

        counterflow_label = QLabel(label)
        counterflow_label.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {thm['text_secondary']};"
        )
        layout.addWidget(counterflow_label)

        counterflow_input = QLineEdit()
        counterflow_input.setPlaceholderText(placeholder)
        counterflow_input.setMinimumHeight(t.COUNTERFLOW_INPUT_HEIGHT)
        layout.addWidget(counterflow_input)

        if hint:
            counterflow_hint = QLabel(hint)
            counterflow_hint.setStyleSheet(
                f"font-size: 11px; color: {thm['text_secondary']}; margin-top: -4px;"
            )
            layout.addWidget(counterflow_hint)

        return counterflow_input

    def _counterflow_divider(self) -> QFrame:
        thm = t.counterflow_theme()
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {thm['border']}; border: none;")
        return line

    def _counterflow_prefill(self):
        """CounterFlow — Pre-fill fields when editing."""
        p = self._counterflow_product
        self._counterflow_barcode.setText(p.counterflow_barcode)
        self._counterflow_name.setText(p.counterflow_name)
        self._counterflow_price.setValue(float(p.counterflow_price))

    def _counterflow_validate_and_accept(self):
        """CounterFlow — Validate inputs before accepting dialog."""
        counterflow_barcode = self._counterflow_barcode.text().strip()
        counterflow_name    = self._counterflow_name.text().strip()
        counterflow_price   = self._counterflow_price.value()

        if not counterflow_barcode:
            QMessageBox.warning(self, "CounterFlow", "Barcode cannot be empty.")
            self._counterflow_barcode.setFocus()
            return

        if not counterflow_name:
            QMessageBox.warning(self, "CounterFlow", "Product name cannot be empty.")
            self._counterflow_name.setFocus()
            return

        if counterflow_price <= 0:
            QMessageBox.warning(self, "CounterFlow", "Price must be greater than zero.")
            self._counterflow_price.setFocus()
            return

        self.accept()

    def counterflow_get_data(self) -> dict:
        """
        CounterFlow — Returns validated form data as a dict.
        Call only after dialog.exec() == Accepted.
        """
        counterflow_data = {
            "barcode": self._counterflow_barcode.text().strip(),
            "name":    self._counterflow_name.text().strip(),
            "price":   self._counterflow_price.value(),
        }
        if self._counterflow_qty is not None:
            counterflow_data["stock_qty"] = self._counterflow_qty.value()
        return counterflow_data
