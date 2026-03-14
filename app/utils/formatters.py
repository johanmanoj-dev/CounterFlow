"""
CounterFlow v1.0.0 — Display Formatters
=========================================
All formatting helpers for displaying values
cleanly in the CounterFlow UI — currency,
dates, times, phone numbers, invoice numbers.
Pure functions — no DB access, no side effects.
"""

from datetime import datetime, date, timedelta
from app.config import (
    COUNTERFLOW_CURRENCY_SYMBOL,
    COUNTERFLOW_INVOICE_PREFIX,
)


# ── Currency ───────────────────────────────────────────────────

def counterflow_format_currency(
    amount: float,
    show_symbol: bool = True,
    decimals:    int  = 2,
) -> str:
    """
    CounterFlow — Format a float as Indian currency string.

    Examples:
        counterflow_format_currency(24580.5)   → "₹24,580.50"
        counterflow_format_currency(0)         → "₹0.00"
        counterflow_format_currency(1000, False) → "1,000.00"
    """
    counterflow_symbol = COUNTERFLOW_CURRENCY_SYMBOL if show_symbol else ""
    return f"{counterflow_symbol}{amount:,.{decimals}f}"


def counterflow_format_currency_compact(amount: float) -> str:
    """
    CounterFlow — Format large currency values compactly.

    Examples:
        counterflow_format_currency_compact(24580)     → "₹24.6K"
        counterflow_format_currency_compact(1250000)   → "₹12.5L"
        counterflow_format_currency_compact(10000000)  → "₹1.0Cr"
    """
    sym = COUNTERFLOW_CURRENCY_SYMBOL
    if amount >= 10_000_000:
        return f"{sym}{amount / 10_000_000:.1f}Cr"
    elif amount >= 100_000:
        return f"{sym}{amount / 100_000:.1f}L"
    elif amount >= 1_000:
        return f"{sym}{amount / 1_000:.1f}K"
    else:
        return f"{sym}{amount:,.0f}"


# ── Date & Time ────────────────────────────────────────────────

def counterflow_format_date(dt: date | datetime) -> str:
    """
    CounterFlow — Format a date as DD Mon YYYY.

    Example:
        counterflow_format_date(date(2024, 3, 15)) → "15 Mar 2024"
    """
    return dt.strftime("%d %b %Y")


def counterflow_format_datetime(dt: datetime) -> str:
    """
    CounterFlow — Format a datetime as DD Mon YYYY HH:MM AM/PM.

    Example:
        "15 Mar 2024  03:45 PM"
    """
    return dt.strftime("%d %b %Y  %I:%M %p")


def counterflow_format_time_only(dt: datetime) -> str:
    """
    CounterFlow — Format just the time portion.

    Example:
        "03:45 PM"
    """
    return dt.strftime("%I:%M %p")


def counterflow_format_relative_time(dt: datetime) -> str:
    """
    CounterFlow — Format a datetime as a relative human-readable string.

    Examples:
        "Just now"       (< 60 seconds ago)
        "5 min ago"      (< 1 hour ago)
        "2 hr ago"       (< 24 hours ago)
        "Yesterday"      (1 day ago)
        "15 Mar"         (older)

    Note: compares against datetime.utcnow() because all CounterFlow
    timestamps are stored as UTC (SQLAlchemy default=datetime.utcnow).
    """
    now   = datetime.utcnow()   # match the UTC timestamps stored in the DB
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
    else:
        return dt.strftime("%d %b")


def counterflow_format_date_range_label(start: date, end: date) -> str:
    """
    CounterFlow — Format a date range as a readable label.

    Examples:
        "Today"                  (same day, today)
        "15 Mar – 20 Mar 2024"   (different days)
        "Mar 2024"               (full month)
    """
    today = date.today()
    if start == end:
        if start == today:
            return "Today"
        return counterflow_format_date(start)

    if start.year == end.year and start.month == end.month:
        if start.day == 1 and end.day >= 28:
            return start.strftime("%b %Y")

    return (
        f"{start.strftime('%d %b')} – "
        f"{end.strftime('%d %b %Y')}"
    )


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


# ── Stock ──────────────────────────────────────────────────────

def counterflow_format_stock_level(qty: int, threshold: int = 5) -> str:
    """
    CounterFlow — Return a human-readable stock level label.

    Examples:
        "Out of Stock"   (0)
        "Low (3)"        (<= threshold)
        "In Stock (42)"  (above threshold)
    """
    if qty == 0:
        return "Out of Stock"
    elif qty <= threshold:
        return f"Low ({qty})"
    else:
        return f"In Stock ({qty})"


def counterflow_stock_badge_level(qty: int, threshold: int = 5) -> str:
    """
    CounterFlow — Return badge color level for stock quantity.
    Used to determine which color badge to show.

    Returns:
        "red"    → out of stock or critically low
        "amber"  → low stock
        "green"  → healthy stock
    """
    if qty <= 0:
        return "red"
    elif qty <= threshold:
        return "amber"
    else:
        return "green"


# ── Credit ─────────────────────────────────────────────────────

def counterflow_format_credit_usage(balance: float, limit: float) -> str:
    """
    CounterFlow — Format credit usage as a percentage string.

    Example:
        counterflow_format_credit_usage(2500, 5000) → "50.0% used"
    """
    if limit <= 0:
        return "No limit set"
    counterflow_pct = (balance / limit) * 100
    return f"{counterflow_pct:.1f}% used"


def counterflow_credit_badge_level(balance: float, limit: float) -> str:
    """
    CounterFlow — Return badge color level for credit balance.

    Returns:
        "green"  → zero balance
        "amber"  → below 80% of limit
        "red"    → at or above 80% of limit
    """
    if balance == 0:
        return "green"
    if limit > 0 and (balance / limit) >= 0.8:
        return "red"
    return "amber"


# ── Payment Method ─────────────────────────────────────────────

def counterflow_format_payment_method(method: str) -> str:
    """
    CounterFlow — Return display label for a payment method code.

    Examples:
        "CASH"   → "Cash"
        "UPI"    → "UPI"
        "CREDIT" → "Credit"
    """
    return {
        "CASH":   "Cash",
        "UPI":    "UPI",
        "CREDIT": "Credit",
    }.get(method.upper(), method)
