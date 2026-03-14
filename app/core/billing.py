"""
CounterFlow v1.0.0 — Billing Session
======================================
Manages a live in-memory POS billing session.
No database writes happen here.
Stock is NOT touched during this phase.
Everything commits only when CounterFlowBillingFinalizer runs.

Classes:
    CounterFlowBillItem     — Single product line in an active bill
    CounterFlowBillingSession — The entire live bill before finalization
"""

from dataclasses import dataclass, field
from typing import List, Optional
from app.db.models import CounterFlowProduct
from app.config import (
    COUNTERFLOW_MAX_BILL_ITEMS,
    COUNTERFLOW_CURRENCY_SYMBOL,
)


# ──────────────────────────────────────────────────────────────
@dataclass
class CounterFlowBillItem:
    """
    CounterFlow — Single line item in an active billing session.
    Holds a product reference and the quantity being purchased.
    line_total is computed dynamically from quantity × price.
    """
    counterflow_product:  CounterFlowProduct
    counterflow_quantity: int = 1

    @property
    def counterflow_line_total(self) -> float:
        """CounterFlow computed total for this line item."""
        return self.counterflow_product.counterflow_price * self.counterflow_quantity

    @property
    def counterflow_display_line(self) -> str:
        """CounterFlow human-readable summary of this line item."""
        return (
            f"{self.counterflow_product.counterflow_name} × "
            f"{self.counterflow_quantity} = "
            f"{COUNTERFLOW_CURRENCY_SYMBOL}{self.counterflow_line_total:,.2f}"
        )

    def __repr__(self):
        return (
            f"<CounterFlowBillItem("
            f"product='{self.counterflow_product.counterflow_name}', "
            f"qty={self.counterflow_quantity}, "
            f"total={self.counterflow_line_total})>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowBillingSession:
    """
    CounterFlow — Active POS Billing Session.

    Holds all scanned items in memory during a transaction.
    Rules:
      - Inventory is NEVER modified here
      - Items can be added, removed, or quantity-adjusted freely
      - Session is cleared after finalization or cancellation
      - Duplicate products increment quantity, not add new rows
    """

    def __init__(self):
        self._counterflow_items: List[CounterFlowBillItem] = []
        self.counterflow_customer_id: Optional[int] = None
        self.counterflow_customer_mobile: Optional[str] = None
        self.counterflow_customer_name: Optional[str] = None

    # ── Item Management ────────────────────────────────────────

    def counterflow_add_item(
        self,
        product: CounterFlowProduct,
        quantity: int = 1
    ) -> bool:
        """
        CounterFlow — Add a scanned product to the active bill.
        If product already exists in bill, increments its quantity.
        Returns False if bill item limit is reached.
        """
        # Check for existing item first
        for item in self._counterflow_items:
            if item.counterflow_product.counterflow_product_id == product.counterflow_product_id:
                item.counterflow_quantity += quantity
                return True

        # Check bill item limit
        if len(self._counterflow_items) >= COUNTERFLOW_MAX_BILL_ITEMS:
            return False

        self._counterflow_items.append(
            CounterFlowBillItem(
                counterflow_product=product,
                counterflow_quantity=quantity
            )
        )
        return True

    def counterflow_remove_item(self, product_id: int) -> bool:
        """
        CounterFlow — Remove a product from the active bill by product ID.
        Returns True if item was found and removed, False otherwise.
        """
        original_count = len(self._counterflow_items)
        self._counterflow_items = [
            item for item in self._counterflow_items
            if item.counterflow_product.counterflow_product_id != product_id
        ]
        return len(self._counterflow_items) < original_count

    def counterflow_update_quantity(self, product_id: int, quantity: int) -> bool:
        """
        CounterFlow — Update quantity of an item in the active bill.
        If quantity <= 0, the item is removed entirely.
        Returns True if item was found, False otherwise.
        """
        if quantity <= 0:
            return self.counterflow_remove_item(product_id)

        for item in self._counterflow_items:
            if item.counterflow_product.counterflow_product_id == product_id:
                item.counterflow_quantity = quantity
                return True
        return False

    def counterflow_get_item(self, product_id: int) -> Optional[CounterFlowBillItem]:
        """CounterFlow — Retrieve a specific bill item by product ID."""
        for item in self._counterflow_items:
            if item.counterflow_product.counterflow_product_id == product_id:
                return item
        return None

    # ── Customer Binding ───────────────────────────────────────

    def counterflow_bind_customer(
        self,
        customer_id: int,
        mobile: str,
        name: str
    ):
        """CounterFlow — Attach a customer profile to this billing session."""
        self.counterflow_customer_id     = customer_id
        self.counterflow_customer_mobile = mobile
        self.counterflow_customer_name   = name

    def counterflow_clear_customer(self):
        """CounterFlow — Detach customer from this billing session."""
        self.counterflow_customer_id     = None
        self.counterflow_customer_mobile = None
        self.counterflow_customer_name   = None

    # ── Session Properties ─────────────────────────────────────

    @property
    def counterflow_items(self) -> List[CounterFlowBillItem]:
        """CounterFlow — All items currently in the active bill."""
        return self._counterflow_items

    @property
    def counterflow_total(self) -> float:
        """CounterFlow — Grand total of the active bill."""
        return sum(item.counterflow_line_total for item in self._counterflow_items)

    @property
    def counterflow_item_count(self) -> int:
        """CounterFlow — Total quantity of all items in the bill."""
        return sum(item.counterflow_quantity for item in self._counterflow_items)

    @property
    def counterflow_unique_product_count(self) -> int:
        """CounterFlow — Number of unique product lines in the bill."""
        return len(self._counterflow_items)

    @property
    def counterflow_is_empty(self) -> bool:
        """CounterFlow — True if the bill has no items."""
        return len(self._counterflow_items) == 0

    @property
    def counterflow_has_customer(self) -> bool:
        """CounterFlow — True if a customer is attached to this session."""
        return self.counterflow_customer_id is not None

    @property
    def counterflow_display_total(self) -> str:
        """CounterFlow — Formatted total string for display."""
        return f"{COUNTERFLOW_CURRENCY_SYMBOL}{self.counterflow_total:,.2f}"

    # ── Session Control ────────────────────────────────────────

    def counterflow_clear(self):
        """
        CounterFlow — Reset the billing session completely.
        Called after finalization or cancellation.
        """
        self._counterflow_items = []
        self.counterflow_customer_id     = None
        self.counterflow_customer_mobile = None
        self.counterflow_customer_name   = None

    def counterflow_summary(self) -> dict:
        """
        CounterFlow — Returns a summary dict of the current session.
        Useful for logging and debugging.
        """
        return {
            "counterflow_total":         self.counterflow_total,
            "counterflow_item_count":    self.counterflow_item_count,
            "counterflow_unique_items":  self.counterflow_unique_product_count,
            "counterflow_customer_id":   self.counterflow_customer_id,
            "counterflow_customer_name": self.counterflow_customer_name,
            "counterflow_items": [
                {
                    "name":       item.counterflow_product.counterflow_name,
                    "qty":        item.counterflow_quantity,
                    "unit_price": item.counterflow_product.counterflow_price,
                    "line_total": item.counterflow_line_total,
                }
                for item in self._counterflow_items
            ],
        }

    def __repr__(self):
        return (
            f"<CounterFlowBillingSession("
            f"items={self.counterflow_unique_product_count}, "
            f"total={self.counterflow_display_total}, "
            f"customer={self.counterflow_customer_name})>"
        )
