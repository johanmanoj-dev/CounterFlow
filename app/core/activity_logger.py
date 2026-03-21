"""
CounterFlow v1.0.0 — Activity Logger (Audit Trail)
====================================================
Append-only audit logging for all critical CounterFlow actions.
Every write is a new INSERT — existing log rows are never modified.

Usage (from any core module or screen):
    from app.core.activity_logger import counterflow_log_action

    counterflow_log_action(
        session     = db_session,
        user_id     = counterflow_auth_session.counterflow_user_id,
        action_type = "BILL_CREATED",
        entity_type = "invoice",
        entity_id   = invoice.counterflow_invoice_id,
        details     = f"Amount: ₹{total:.2f} | Method: CASH",
    )

Defined action_type constants are collected in CounterFlowActions
for consistent naming across all callers.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import CounterFlowActivityLog


# ──────────────────────────────────────────────────────────────
class CounterFlowActions:
    """
    CounterFlow — Canonical action type strings.
    Import and use these constants instead of raw strings
    to ensure consistent log entries across the codebase.
    """
    # Billing
    BILL_CREATED        = "BILL_CREATED"

    # Customer
    CUSTOMER_CREATED    = "CUSTOMER_CREATED"
    CUSTOMER_DELETED    = "CUSTOMER_DELETED"
    DEBT_CLEARED        = "DEBT_CLEARED"

    # Inventory
    INVENTORY_ADDED     = "INVENTORY_ADDED"
    INVENTORY_EDITED    = "INVENTORY_EDITED"
    INVENTORY_DELETED   = "INVENTORY_DELETED"
    STOCK_RESTOCKED     = "STOCK_RESTOCKED"

    # Auth
    ADMIN_LOGIN         = "ADMIN_LOGIN"
    STAFF_LOGIN         = "STAFF_LOGIN"
    ADMIN_LOGOUT        = "LOGOUT"

    # Staff management
    STAFF_CREATED       = "STAFF_CREATED"
    STAFF_DEACTIVATED   = "STAFF_DEACTIVATED"
    STAFF_REACTIVATED   = "STAFF_REACTIVATED"
    PASSWORD_CHANGED    = "PASSWORD_CHANGED"


# ──────────────────────────────────────────────────────────────
def counterflow_log_action(
    session:     Session,
    user_id:     int,
    action_type: str,
    entity_type: str  | None = None,
    entity_id:   int  | None = None,
    details:     str  | None = None,
) -> CounterFlowActivityLog:
    """
    CounterFlow — Append a single immutable audit log entry.
    The entry is added to the session but NOT flushed — it is committed
    atomically with the surrounding business transaction by the caller.
    This prevents mid-transaction flush failures from corrupting session state.

    Args:
        session:     Active SQLAlchemy session.
        user_id:     ID of the user performing the action.
        action_type: One of CounterFlowActions constants (e.g. "BILL_CREATED").
        entity_type: What was affected (e.g. "invoice", "customer", "product").
        entity_id:   Primary key of the affected entity.
        details:     Optional human-readable context string.

    Returns:
        The newly created CounterFlowActivityLog instance (not yet flushed).
    """
    if user_id is None:
        return None  # Guard: never log with a null user_id

    log_entry = CounterFlowActivityLog(
        counterflow_timestamp=datetime.now(),
        counterflow_action_type=action_type,
        counterflow_user_id=user_id,
        counterflow_entity_type=entity_type,
        counterflow_entity_id=entity_id,
        counterflow_details=details,
    )
    session.add(log_entry)
    # No flush here — caller's commit() writes everything atomically.
    return log_entry


# ──────────────────────────────────────────────────────────────
class CounterFlowActivityLogManager:
    """
    CounterFlow — Query interface for the activity log.
    Used by the Admin Logs screen to fetch and filter records.
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session = counterflow_session

    def counterflow_get_all_logs(
        self,
        limit: int = 500,
    ) -> list[CounterFlowActivityLog]:
        """CounterFlow — Return the most recent N log entries."""
        return (
            self.counterflow_session
            .query(CounterFlowActivityLog)
            .order_by(CounterFlowActivityLog.counterflow_timestamp.desc())
            .limit(limit)
            .all()
        )

    def counterflow_get_logs_by_action(
        self,
        action_type: str,
        limit: int = 200,
    ) -> list[CounterFlowActivityLog]:
        """CounterFlow — Filter logs by action type."""
        return (
            self.counterflow_session
            .query(CounterFlowActivityLog)
            .filter_by(counterflow_action_type=action_type)
            .order_by(CounterFlowActivityLog.counterflow_timestamp.desc())
            .limit(limit)
            .all()
        )

    def counterflow_get_logs_by_user(
        self,
        user_id: int,
        limit: int = 200,
    ) -> list[CounterFlowActivityLog]:
        """CounterFlow — Filter logs by user ID."""
        return (
            self.counterflow_session
            .query(CounterFlowActivityLog)
            .filter_by(counterflow_user_id=user_id)
            .order_by(CounterFlowActivityLog.counterflow_timestamp.desc())
            .limit(limit)
            .all()
        )

    def counterflow_get_filtered_logs(
        self,
        action_type: str | None = None,
        user_id:     int | None = None,
        limit:       int        = 500,
    ) -> list[CounterFlowActivityLog]:
        """CounterFlow — Return logs with optional filters applied."""
        q = self.counterflow_session.query(CounterFlowActivityLog)
        if action_type:
            q = q.filter(CounterFlowActivityLog.counterflow_action_type == action_type)
        if user_id:
            q = q.filter(CounterFlowActivityLog.counterflow_user_id == user_id)
        return (
            q.order_by(CounterFlowActivityLog.counterflow_timestamp.desc())
            .limit(limit)
            .all()
        )
