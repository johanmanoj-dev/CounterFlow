"""
CounterFlow v1.0.0 — Inventory Manager
========================================
Handles all stock-related operations for CounterFlow.
Every inventory change — in or out — is logged to
CounterFlowStockMovement for full audit trail.

Class:
    CounterFlowInventoryManager — All inventory operations
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import CounterFlowProduct, CounterFlowStockMovement
from app.config import (
    COUNTERFLOW_STOCK_IN,
    COUNTERFLOW_STOCK_OUT,
    COUNTERFLOW_LOW_STOCK_THRESHOLD,
    COUNTERFLOW_DEBUG,
)


# ──────────────────────────────────────────────────────────────
class CounterFlowInventoryManager:
    """
    CounterFlow — Inventory Manager.
    All product and stock operations go through this class.
    Never modifies inventory without logging a StockMovement.
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session = counterflow_session

    # ── Product Lookup ─────────────────────────────────────────

    def counterflow_get_by_barcode(
        self,
        barcode: str
    ) -> CounterFlowProduct | None:
        """
        CounterFlow — Look up a product by its barcode.
        Primary lookup method during POS barcode scanning.
        Returns None if barcode is not found or product is inactive.
        """
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter_by(
                counterflow_barcode=barcode.strip(),
                counterflow_is_active=True
            )
            .first()
        )

    def counterflow_get_by_id(
        self,
        product_id: int
    ) -> CounterFlowProduct | None:
        """CounterFlow — Look up an active product by its primary key."""
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter_by(
                counterflow_product_id=product_id,
                counterflow_is_active=True
            )
            .first()
        )

    def counterflow_search_products(self, query: str) -> list[CounterFlowProduct]:
        """
        CounterFlow — Search products by name or barcode.
        Used in the inventory search bar and manual product lookup.
        """
        counterflow_pattern = f"%{query.strip()}%"
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter(
                CounterFlowProduct.counterflow_is_active == True,
                (
                    CounterFlowProduct.counterflow_name.ilike(counterflow_pattern) |
                    CounterFlowProduct.counterflow_barcode.ilike(counterflow_pattern)
                )
            )
            .order_by(CounterFlowProduct.counterflow_name)
            .all()
        )

    def counterflow_get_all_products(self) -> list[CounterFlowProduct]:
        """CounterFlow — Retrieve all active products ordered by name."""
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter_by(counterflow_is_active=True)
            .order_by(CounterFlowProduct.counterflow_name)
            .all()
        )

    def counterflow_get_low_stock_products(
        self,
        threshold: int | None = None
    ) -> list[CounterFlowProduct]:
        """
        CounterFlow — Returns products at or below the low stock threshold.
        Used to populate the low stock alert on the dashboard.
        """
        counterflow_threshold = threshold or COUNTERFLOW_LOW_STOCK_THRESHOLD
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter(
                CounterFlowProduct.counterflow_is_active == True,
                CounterFlowProduct.counterflow_stock_qty <= counterflow_threshold
            )
            .order_by(CounterFlowProduct.counterflow_stock_qty)
            .all()
        )

    def counterflow_barcode_exists(self, barcode: str) -> bool:
        """CounterFlow — Check if a barcode already exists in the database."""
        return (
            self.counterflow_session
            .query(CounterFlowProduct)
            .filter_by(
                counterflow_barcode=barcode.strip(),
                counterflow_is_active=True,
            )
            .first()
        ) is not None

    # ── Product Management ─────────────────────────────────────

    def counterflow_add_product(
        self,
        barcode:   str,
        name:      str,
        price:     float,
        stock_qty: int = 0,
    ) -> CounterFlowProduct:
        """
        CounterFlow — Add a new product to inventory.
        If initial stock_qty > 0, logs an IN stock movement.
        Raises ValueError if barcode already exists.
        """
        if self.counterflow_barcode_exists(barcode):
            raise ValueError(
                f"[CounterFlow] Barcode '{barcode}' already exists in inventory."
            )

        counterflow_product = CounterFlowProduct(
            counterflow_barcode=barcode.strip(),
            counterflow_name=name.strip(),
            counterflow_price=price,
            counterflow_stock_qty=stock_qty,
        )
        self.counterflow_session.add(counterflow_product)
        self.counterflow_session.flush()

        # Log initial stock as an IN movement
        if stock_qty > 0:
            self._counterflow_log_movement(
                product_id=counterflow_product.counterflow_product_id,
                movement_type=COUNTERFLOW_STOCK_IN,
                quantity=stock_qty,
                reason="CounterFlow initial stock entry",
            )

        if COUNTERFLOW_DEBUG:
            print(f"[CounterFlow] Product added: {counterflow_product}")

        return counterflow_product

    # ── Stock Operations ───────────────────────────────────────

    def counterflow_restock(
        self,
        product_id: int,
        quantity:   int,
        reason:     str = "CounterFlow restock",
    ) -> CounterFlowProduct:
        """
        CounterFlow — Add stock to an existing product.
        Always logs a CounterFlowStockMovement IN record.
        """
        counterflow_product = self.counterflow_get_by_id(product_id)
        if not counterflow_product:
            raise ValueError(f"[CounterFlow] Product ID {product_id} not found.")
        if quantity <= 0:
            raise ValueError("[CounterFlow] Restock quantity must be greater than zero.")

        counterflow_product.counterflow_stock_qty  += quantity

        self._counterflow_log_movement(
            product_id=product_id,
            movement_type=COUNTERFLOW_STOCK_IN,
            quantity=quantity,
            reason=reason,
        )

        if COUNTERFLOW_DEBUG:
            print(
                f"[CounterFlow] Restocked {quantity} units of "
                f"'{counterflow_product.counterflow_name}'. "
                f"New stock: {counterflow_product.counterflow_stock_qty}"
            )

        return counterflow_product

    def counterflow_deduct_stock(
        self,
        product_id: int,
        quantity:   int,
        invoice_id: int,
    ) -> CounterFlowProduct:
        """
        CounterFlow — Deduct stock after a bill is finalized.
        ONLY called by CounterFlowBillingFinalizer during atomic commit.
        Raises ValueError if stock is insufficient.
        Always logs a CounterFlowStockMovement OUT record.
        """
        counterflow_product = self.counterflow_get_by_id(product_id)
        if not counterflow_product:
            raise ValueError(f"[CounterFlow] Product ID {product_id} not found.")

        if counterflow_product.counterflow_stock_qty < quantity:
            raise ValueError(
                f"[CounterFlow] Insufficient stock for "
                f"'{counterflow_product.counterflow_name}'. "
                f"Available: {counterflow_product.counterflow_stock_qty}, "
                f"Requested: {quantity}"
            )

        counterflow_product.counterflow_stock_qty  -= quantity

        self._counterflow_log_movement(
            product_id=product_id,
            movement_type=COUNTERFLOW_STOCK_OUT,
            quantity=quantity,
            reason=f"CounterFlow Sale — Invoice CF-{invoice_id:05d}",
            reference_id=invoice_id,
        )

        return counterflow_product

    # ── Internal Helpers ───────────────────────────────────────

    def _counterflow_log_movement(
        self,
        product_id:    int,
        movement_type: str,
        quantity:      int,
        reason:        str | None  = None,
        reference_id:  int | None  = None,
    ):
        """
        CounterFlow — Internal method to create a StockMovement record.
        Never call directly — use counterflow_restock or counterflow_deduct_stock.
        """
        counterflow_movement = CounterFlowStockMovement(
            counterflow_product_id=product_id,
            counterflow_movement_type=movement_type,
            counterflow_quantity=quantity,
            counterflow_reason=reason,
            counterflow_reference_id=reference_id,
        )
        self.counterflow_session.add(counterflow_movement)
