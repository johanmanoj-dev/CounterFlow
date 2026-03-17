"""
CounterFlow v1.0.0 — Display Formatters
=========================================
All formatting helpers for displaying values
cleanly in the CounterFlow UI — currency,
dates, times, phone numbers, invoice numbers.
Pure functions — no DB access, no side effects.
"""

from datetime import datetime
from app.config import (
    COUNTERFLOW_CURRENCY_SYMBOL,
    COUNTERFLOW_INVOICE_PREFIX,
)


# ── Currency ───────────────────────────────────────────────────


def counterflow_format_relative_time(dt: datetime) -> str:
    """
    CounterFlow — Format a datetime as a relative human-readable string.

    Examples:
        "Just now"       (< 60 seconds ago)
        "5 min ago"      (< 1 hour ago)
        "2 hr ago"       (< 24 hours ago)
        "Yesterday"      (1 day ago)
        "15 Mar"         (older)

    Note: compares against datetime.now() because all CounterFlow
    timestamps are stored as local time.
    """
    now   = datetime.now()   # match the local timestamps stored in the DB
    delta = now - dt
    secs  = int(delta.total_seconds())

    if secs < 60:
        return "Just now"
    elif secs < 3600:
        counterflow_mins = secs // 60
        return f"{counterflow_mins} min ago"
    elif secs < 86400:
        counterflow_hrs = secs // 3600
        return f"{counterflow_hrs} hr ago"
    elif secs < 172800:
        return "Yesterday"
# ── Invoice ────────────────────────────────────────────────────

def counterflow_format_invoice_number(invoice_id: int) -> str:
    """
    CounterFlow — Format an invoice ID as the display invoice number.

    Example:
        counterflow_format_invoice_number(42) → "CF-00042"
    """
    return f"{COUNTERFLOW_INVOICE_PREFIX}-{invoice_id:05d}"


# ── Mobile ─────────────────────────────────────────────────────

def counterflow_format_mobile(mobile: str) -> str:
    """
    CounterFlow — Format a 10-digit mobile for display.

    Example:
        counterflow_format_mobile("9876543210") → "98765 43210"
    """
    counterflow_cleaned = mobile.strip().replace(" ", "")
    if len(counterflow_cleaned) == 10:
        return f"{counterflow_cleaned[:5]} {counterflow_cleaned[5:]}"
    return mobile
