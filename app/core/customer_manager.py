"""
CounterFlow v1.0.0 — Customer Manager
======================================
Handles all customer-related operations:
Lookup, creation, search, update, and
credit balance management.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import CounterFlowCustomer
from app.utils.validators import counterflow_validate_mobile
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
    ) -> Optional[CounterFlowCustomer]:
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
    ) -> Optional[CounterFlowCustomer]:
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

        return counterflow_customer, True

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
