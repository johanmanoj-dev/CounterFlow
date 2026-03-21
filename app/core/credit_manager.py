"""
CounterFlow v1.0.0 — Billing Finalizer & Credit Manager
=========================================================
The most critical module in CounterFlow.
Handles the atomic finalization of a billing session:

    1. Save CounterFlowInvoice
    2. Save CounterFlowInvoiceItems
    3. Deduct stock via CounterFlowInventoryManager
    4. Update customer credit if CREDIT payment
    5. Commit everything as ONE database transaction

If ANY step fails, the entire transaction rolls back.
No partial data is ever written to the CounterFlow database.

Classes:
    CounterFlowCreditLimitError     — Raised when credit limit is exceeded
    CounterFlowEmptyBillError       — Raised when finalizing an empty bill
    CounterFlowBillingFinalizer     — Atomic bill finalization
"""

from sqlalchemy.orm import Session

from app.db.models import CounterFlowInvoice, CounterFlowInvoiceItem
from app.core.billing import CounterFlowBillingSession
from app.core.inventory_manager import CounterFlowInventoryManager
from app.core.customer_manager import CounterFlowCustomerManager
from app.core.activity_logger import counterflow_log_action, CounterFlowActions
from app.core.auth import counterflow_auth_session
from app.config import (
    COUNTERFLOW_PAYMENT_CREDIT,
    COUNTERFLOW_PAYMENT_METHODS,
    COUNTERFLOW_DEBUG,
)


# ── CounterFlow Custom Exceptions ─────────────────────────────

class CounterFlowCreditLimitError(Exception):
    """
    CounterFlow — Raised when a credit purchase would exceed
    the customer's configured credit limit.
    Carries full context for the UI to display a warning dialog.
    """

    def __init__(
        self,
        counterflow_customer,
        counterflow_bill_amount: float,
        counterflow_over_by:     float,
    ):
        self.counterflow_customer     = counterflow_customer
        self.counterflow_bill_amount  = counterflow_bill_amount
        self.counterflow_over_by      = counterflow_over_by

        super().__init__(
            f"[CounterFlow] Credit limit exceeded for "
            f"'{counterflow_customer.counterflow_name}'. "
            f"Current balance: ₹{counterflow_customer.counterflow_credit_balance:,.2f} | "
            f"Limit: ₹{counterflow_customer.counterflow_credit_limit:,.2f} | "
            f"Bill: ₹{counterflow_bill_amount:,.2f} | "
            f"Over by: ₹{counterflow_over_by:,.2f}"
        )


class CounterFlowEmptyBillError(Exception):
    """
    CounterFlow — Raised when attempting to finalize an empty billing session.
    """
    def __init__(self):
        super().__init__(
            "[CounterFlow] Cannot finalize an empty bill. "
            "Please add at least one product before checkout."
        )


class CounterFlowInvalidPaymentError(Exception):
    """
    CounterFlow — Raised when an invalid payment method is provided.
    """
    def __init__(self, counterflow_method: str):
        super().__init__(
            f"[CounterFlow] Invalid payment method '{counterflow_method}'. "
            f"Valid options: {COUNTERFLOW_PAYMENT_METHODS}"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowBillingFinalizer:
    """
    CounterFlow — Billing Finalizer.

    The single point of truth for completing a sale in CounterFlow.
    Orchestrates all managers in one atomic database transaction.

    Usage:
        finalizer = CounterFlowBillingFinalizer(session)
        invoice   = finalizer.counterflow_finalize(
            billing_session  = active_session,
            payment_method   = "CASH",
            customer_mobile  = "9876543210",
            customer_name    = "Ravi Kumar",
        )
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session  = counterflow_session
        self.counterflow_inventory = CounterFlowInventoryManager(counterflow_session)
        self.counterflow_customers = CounterFlowCustomerManager(counterflow_session)

    def counterflow_finalize(
        self,
        billing_session:         CounterFlowBillingSession,
        payment_method:          str,
        customer_mobile:         str  = None,
        customer_name:           str  = "CounterFlow Customer",
        force_credit_override:   bool = False,
    ) -> CounterFlowInvoice:
        """
        CounterFlow — Atomic bill finalization.

        Steps (all-or-nothing):
            1. Validate bill is not empty
            2. Validate payment method
            3. Resolve customer (lookup or create)
            4. Check credit limit if CREDIT payment
            5. Create CounterFlowInvoice record
            6. Create CounterFlowInvoiceItem records
            7. Deduct stock for each item
            8. Update customer credit balance if CREDIT
            9. Commit entire transaction

        Args:
            billing_session:       The active CounterFlowBillingSession
            payment_method:        "CASH", "UPI", or "CREDIT"
            customer_mobile:       Customer mobile number (optional for walk-in)
            customer_name:         Customer name for new customer creation
            force_credit_override: Skip credit limit check (owner override)

        Returns:
            Finalized CounterFlowInvoice object

        Raises:
            CounterFlowEmptyBillError       — Bill has no items
            CounterFlowInvalidPaymentError  — Invalid payment method
            CounterFlowCreditLimitError     — Credit limit would be exceeded
            ValueError                      — Insufficient stock
        """

        # ── Step 1: Validate Bill ──────────────────────────────
        if billing_session.counterflow_is_empty:
            raise CounterFlowEmptyBillError()

        # ── Step 2: Validate Payment Method ───────────────────
        if payment_method not in COUNTERFLOW_PAYMENT_METHODS:
            raise CounterFlowInvalidPaymentError(payment_method)

        # ── Steps 3–9: Single atomic transaction ──────────────
        # Steps 3 & 4 are inside the try/except so that if a new customer
        # was flushed (Step 3) and CounterFlowCreditLimitError is raised
        # (Step 4), the rollback will undo the uncommitted flush, preventing
        # phantom customer rows from leaking into the database on cancel.
        try:
            # ── Step 3: Resolve Customer ───────────────────────
            counterflow_customer_id = None

            if customer_mobile and customer_mobile.strip():
                counterflow_customer, counterflow_was_created = (
                    self.counterflow_customers.counterflow_get_or_create(
                        mobile=customer_mobile,
                        name=customer_name,
                    )
                )
                counterflow_customer_id = counterflow_customer.counterflow_customer_id

                # ── Step 4: Credit Limit Check ─────────────────
                if payment_method == COUNTERFLOW_PAYMENT_CREDIT and not force_credit_override:
                    counterflow_exceeds, counterflow_over_by = (
                        self.counterflow_customers.counterflow_check_credit_limit(
                            customer=counterflow_customer,
                            bill_amount=billing_session.counterflow_total,
                        )
                    )
                    if counterflow_exceeds:
                        raise CounterFlowCreditLimitError(
                            counterflow_customer=counterflow_customer,
                            counterflow_bill_amount=billing_session.counterflow_total,
                            counterflow_over_by=counterflow_over_by,
                        )

            # ── Step 5: Create Invoice ─────────────────────────
            counterflow_invoice = CounterFlowInvoice(
                counterflow_customer_id=counterflow_customer_id,
                counterflow_total_amount=billing_session.counterflow_total,
                counterflow_payment_method=payment_method,
            )
            self.counterflow_session.add(counterflow_invoice)
            self.counterflow_session.flush()  # Generates invoice ID

            # ── Step 6 & 7: Invoice Items + Stock Deduction ────
            for counterflow_bill_item in billing_session.counterflow_items:
                # Create line item (price snapshot)
                counterflow_item = CounterFlowInvoiceItem(
                    counterflow_invoice_id=counterflow_invoice.counterflow_invoice_id,
                    counterflow_product_id=counterflow_bill_item.counterflow_product.counterflow_product_id,
                    counterflow_quantity=counterflow_bill_item.counterflow_quantity,
                    counterflow_unit_price=counterflow_bill_item.counterflow_product.counterflow_price,
                )
                self.counterflow_session.add(counterflow_item)

                # Deduct stock atomically
                self.counterflow_inventory.counterflow_deduct_stock(
                    product_id=counterflow_bill_item.counterflow_product.counterflow_product_id,
                    quantity=counterflow_bill_item.counterflow_quantity,
                    invoice_id=counterflow_invoice.counterflow_invoice_id,
                )

            # ── Step 8: Update Credit Balance ──────────────────
            if payment_method == COUNTERFLOW_PAYMENT_CREDIT and counterflow_customer_id:
                self.counterflow_customers.counterflow_add_credit(
                    customer_id=counterflow_customer_id,
                    amount=billing_session.counterflow_total,
                )

            # ── Step 8b: Audit Log ─────────────────────────────
            if counterflow_auth_session.counterflow_is_authenticated:
                counterflow_log_action(
                    session=self.counterflow_session,
                    user_id=counterflow_auth_session.counterflow_user_id,
                    action_type=CounterFlowActions.BILL_CREATED,
                    entity_type="invoice",
                    entity_id=counterflow_invoice.counterflow_invoice_id,
                    details=(
                        f"Total: ₹{billing_session.counterflow_total:,.2f} | "
                        f"Method: {payment_method} | "
                        f"Items: {len(billing_session.counterflow_items)}"
                    ),
                )

            # ── Step 9: Commit ─────────────────────────────────
            self.counterflow_session.commit()

            if COUNTERFLOW_DEBUG:
                print(
                    f"[CounterFlow] Invoice {counterflow_invoice.counterflow_invoice_number} "
                    f"finalized. Total: ₹{counterflow_invoice.counterflow_total_amount:,.2f} "
                    f"via {payment_method}"
                )

            return counterflow_invoice

        except Exception as counterflow_error:
            self.counterflow_session.rollback()
            if COUNTERFLOW_DEBUG:
                print(f"[CounterFlow] Finalization failed, rolled back: {counterflow_error}")
            raise
