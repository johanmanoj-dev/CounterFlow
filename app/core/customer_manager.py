"""
CounterFlow v1.0.0 — Customer Manager
======================================
Handles all customer-related operations:
Lookup, creation, search, update, and
credit balance management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import CounterFlowCustomer
from app.utils.validators import counterflow_validate_mobile
from app.core.activity_logger import counterflow_log_action, CounterFlowActions
from app.core.auth import counterflow_auth_session
from app.config import (
    COUNTERFLOW_DEFAULT_CREDIT_LIMIT,
    COUNTERFLOW_DEBUG,
)


# ──────────────────────────────────────────────────────────────
class CounterFlowCustomerManager:
    """
    CounterFlow — Customer Manager.
    Mobile-first customer lookup and credit management.
    Designed for speed at the checkout counter.
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session = counterflow_session

    # ── Lookup ─────────────────────────────────────────────────

    def counterflow_get_by_mobile(
        self,
        mobile: str
    ) -> CounterFlowCustomer | None:
        """
        CounterFlow — Look up a customer by mobile number.
        Primary lookup during POS checkout.
        Returns None if customer is not found.
        """
        return (
            self.counterflow_session
            .query(CounterFlowCustomer)
            .filter_by(counterflow_mobile=mobile.strip())
            .first()
        )

    def counterflow_get_by_id(
        self,
        customer_id: int
    ) -> CounterFlowCustomer | None:
        """CounterFlow — Look up a customer by primary key."""
        return self.counterflow_session.get(CounterFlowCustomer, customer_id)

    def counterflow_get_all_customers(self) -> list[CounterFlowCustomer]:
        """CounterFlow — Retrieve all customers ordered by name."""
        return (
            self.counterflow_session
            .query(CounterFlowCustomer)
            .order_by(CounterFlowCustomer.counterflow_name)
            .all()
        )

    def counterflow_search_customers(self, query: str) -> list[CounterFlowCustomer]:
        """CounterFlow — Search customers by name or mobile number."""
        counterflow_pattern = f"%{query.strip()}%"
        return (
            self.counterflow_session
            .query(CounterFlowCustomer)
            .filter(
                CounterFlowCustomer.counterflow_name.ilike(counterflow_pattern) |
                CounterFlowCustomer.counterflow_mobile.ilike(counterflow_pattern)
            )
            .order_by(CounterFlowCustomer.counterflow_name)
            .all()
        )

    # ── Create ─────────────────────────────────────────────────

    def counterflow_get_or_create(
        self,
        mobile: str,
        name:   str = "CounterFlow Customer",
    ) -> tuple[CounterFlowCustomer, bool]:
        """
        CounterFlow — Find customer by mobile or create a new one.
        Returns (customer, was_created).
        was_created=True means this is a brand new customer.
        This is the primary method called at POS checkout.
        """
        counterflow_customer = self.counterflow_get_by_mobile(mobile)

        if counterflow_customer:
            if COUNTERFLOW_DEBUG:
                print(
                    f"[CounterFlow] Existing customer found: "
                    f"{counterflow_customer.counterflow_name}"
                )
            return counterflow_customer, False

        # Create new customer
        counterflow_customer = CounterFlowCustomer(
            counterflow_mobile=mobile.strip(),
            counterflow_name=name.strip(),
            counterflow_credit_limit=COUNTERFLOW_DEFAULT_CREDIT_LIMIT,
            counterflow_credit_balance=0.0,
        )
        self.counterflow_session.add(counterflow_customer)
        self.counterflow_session.flush()

        if COUNTERFLOW_DEBUG:
            print(
                f"[CounterFlow] New customer created: "
                f"{counterflow_customer.counterflow_name} "
                f"({counterflow_customer.counterflow_mobile})"
            )

        # Audit log
        if counterflow_auth_session.counterflow_is_authenticated:
            counterflow_log_action(
                session=self.counterflow_session,
                user_id=counterflow_auth_session.counterflow_user_id,
                action_type=CounterFlowActions.CUSTOMER_CREATED,
                entity_type="customer",
                entity_id=counterflow_customer.counterflow_customer_id,
                details=f"Name: {counterflow_customer.counterflow_name} | Mobile: {counterflow_customer.counterflow_mobile}",
            )

        return counterflow_customer, True

    # ── Delete ─────────────────────────────────────────────────

    def counterflow_delete_customer(
        self,
        customer_id:  int,
        clear_debt:   bool = False,
    ) -> str:
        """
        CounterFlow — Permanently delete a customer record (Admin only).

        Args:
            customer_id: Primary key of the customer to remove.
            clear_debt:  If True, zero the credit balance before deleting
                         (for "delete and forgive debt").
                         If False and the customer has an outstanding balance,
                         the balance is simply lost — caller must confirm this.

        Returns the customer name for confirmation/audit messages.
        Raises ValueError if customer not found.
        """
        customer = self.counterflow_session.get(CounterFlowCustomer, customer_id)
        if customer is None:
            raise ValueError(f"[CounterFlow] Customer ID {customer_id} not found.")

        customer_name   = customer.counterflow_name
        customer_mobile = customer.counterflow_mobile
        balance_at_delete = customer.counterflow_credit_balance

        if clear_debt and balance_at_delete > 0:
            customer.counterflow_credit_balance = 0.0

        detail_parts = [
            f"Name: {customer_name}",
            f"Mobile: {customer_mobile}",
            f"Balance at deletion: ₹{balance_at_delete:,.2f}",
            "Debt cleared before deletion" if clear_debt and balance_at_delete > 0
            else "Deleted with outstanding debt" if balance_at_delete > 0
            else "No outstanding debt",
        ]

        self.counterflow_session.delete(customer)

        if counterflow_auth_session.counterflow_is_authenticated:
            counterflow_log_action(
                session=self.counterflow_session,
                user_id=counterflow_auth_session.counterflow_user_id,
                action_type=CounterFlowActions.CUSTOMER_DELETED,
                entity_type="customer",
                entity_id=customer_id,
                details=" | ".join(detail_parts),
            )

        if COUNTERFLOW_DEBUG:
            print(f"[CounterFlow] Customer deleted: {customer_name} (id={customer_id})")

        return customer_name

    # ── Credit Operations ──────────────────────────────────────

    def counterflow_add_credit(
        self,
        customer_id: int,
        amount:      float,
    ):
        """
        CounterFlow — Increase a customer's outstanding credit balance.
        Called when a CREDIT payment method is used at checkout.
        Only called by CounterFlowBillingFinalizer.
        """
        counterflow_customer = self.counterflow_get_by_id(customer_id)
        if not counterflow_customer:
            raise ValueError(f"[CounterFlow] Customer ID {customer_id} not found.")
        if amount <= 0:
            raise ValueError("[CounterFlow] Credit amount must be greater than zero.")

        counterflow_customer.counterflow_credit_balance += amount

        if COUNTERFLOW_DEBUG:
            print(
                f"[CounterFlow] Credit added ₹{amount:,.2f} to "
                f"{counterflow_customer.counterflow_name}. "
                f"New balance: ₹{counterflow_customer.counterflow_credit_balance:,.2f}"
            )

    def counterflow_record_credit_payment(
        self,
        customer_id: int,
        amount:      float,
    ) -> CounterFlowCustomer:
        """
        CounterFlow — Record a credit repayment from a customer.
        Reduces the outstanding credit balance.
        Balance cannot go below zero.
        """
        counterflow_customer = self.counterflow_get_by_id(customer_id)
        if not counterflow_customer:
            raise ValueError(f"[CounterFlow] Customer ID {customer_id} not found.")
        if amount <= 0:
            raise ValueError("[CounterFlow] Payment amount must be greater than zero.")

        counterflow_customer.counterflow_credit_balance = max(
            0.0,
            counterflow_customer.counterflow_credit_balance - amount
        )

        if COUNTERFLOW_DEBUG:
            print(
                f"[CounterFlow] Credit payment ₹{amount:,.2f} recorded for "
                f"{counterflow_customer.counterflow_name}. "
                f"Remaining balance: ₹{counterflow_customer.counterflow_credit_balance:,.2f}"
            )

        # Audit log
        if counterflow_auth_session.counterflow_is_authenticated:
            counterflow_log_action(
                session=self.counterflow_session,
                user_id=counterflow_auth_session.counterflow_user_id,
                action_type=CounterFlowActions.DEBT_CLEARED,
                entity_type="customer",
                entity_id=counterflow_customer.counterflow_customer_id,
                details=f"Amount cleared: ₹{amount:,.2f} | Remaining: ₹{counterflow_customer.counterflow_credit_balance:,.2f}",
            )

        return counterflow_customer

    def counterflow_check_credit_limit(
        self,
        customer:    CounterFlowCustomer,
        bill_amount: float,
    ) -> tuple[bool, float]:
        """
        CounterFlow — Check if a credit purchase would exceed the limit.
        Returns (would_exceed, amount_over_limit).
        would_exceed=True means the purchase should be warned/blocked.
        """
        counterflow_projected = customer.counterflow_credit_balance + bill_amount
        counterflow_over      = counterflow_projected - customer.counterflow_credit_limit

        return (
            counterflow_projected > customer.counterflow_credit_limit,
            max(0.0, counterflow_over)
        )

    # ── Validation ─────────────────────────────────────────────

    def counterflow_mobile_exists(self, mobile: str) -> bool:
        """CounterFlow — Check if a mobile number is already registered."""
        return (
            self.counterflow_session
            .query(CounterFlowCustomer)
            .filter_by(counterflow_mobile=mobile.strip())
            .first()
        ) is not None

    # ── CounterFlow Validation ─────────────────────────────────

    @staticmethod
    def counterflow_validate_mobile(mobile: str) -> tuple:
        """
        CounterFlow — Delegates to the authoritative validator
        in app.utils.validators.
        """
        return counterflow_validate_mobile(mobile)
