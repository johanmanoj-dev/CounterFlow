"""
CounterFlow v1.0.0 — Input Validators
=======================================
All input validation logic used across the
CounterFlow UI and business logic layers.
Pure functions — no DB access, no side effects.
"""

import re


# ── Mobile ─────────────────────────────────────────────────────

def counterflow_validate_mobile(mobile: str) -> tuple[bool, str]:
    """
    CounterFlow — Validate an Indian mobile number.
    Accepts 10-digit numbers, optionally prefixed with +91 or 0.

    Returns:
        (True, cleaned_10_digit_number)  — if valid
        (False, error_message)           — if invalid
    """
    counterflow_cleaned = (
        mobile.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("+91", "")
        .lstrip("0")
    )

    if not counterflow_cleaned.isdigit():
        return False, "Mobile number must contain only digits."

    if len(counterflow_cleaned) != 10:
        return False, f"Mobile number must be 10 digits (got {len(counterflow_cleaned)})."

    if counterflow_cleaned[0] not in "6789":
        return False, "Mobile number must start with 6, 7, 8, or 9."

    return True, counterflow_cleaned


# ── Product Fields ─────────────────────────────────────────────

def counterflow_validate_barcode(barcode: str) -> tuple[bool, str]:
    """
    CounterFlow — Validate a product barcode string.
    Barcodes must be 1–100 characters, no special chars.

    Returns:
        (True, cleaned_barcode)  — if valid
        (False, error_message)   — if invalid
    """
    counterflow_cleaned = barcode.strip()

    if not counterflow_cleaned:
        return False, "Barcode cannot be empty."

    if len(counterflow_cleaned) > 100:
        return False, "Barcode must not exceed 100 characters."

    if not re.match(r'^[A-Za-z0-9\-_. ]+$', counterflow_cleaned):
        return False, "Barcode contains invalid characters."

    return True, counterflow_cleaned


def counterflow_validate_product_name(name: str) -> tuple[bool, str]:
    """
    CounterFlow — Validate a product name.
    Must be 1–255 characters, non-empty after stripping.

    Returns:
        (True, cleaned_name)   — if valid
        (False, error_message) — if invalid
    """
    counterflow_cleaned = name.strip()

    if not counterflow_cleaned:
        return False, "Product name cannot be empty."

    if len(counterflow_cleaned) > 255:
        return False, "Product name must not exceed 255 characters."

    return True, counterflow_cleaned


def counterflow_validate_price(price: float) -> tuple[bool, str]:
    """
    CounterFlow — Validate a product price.
    Must be a positive number greater than zero.

    Returns:
        (True, price)          — if valid
        (False, error_message) — if invalid
    """
    if price is None:
        return False, "Price cannot be empty."

    if not isinstance(price, (int, float)):
        return False, "Price must be a number."

    if price <= 0:
        return False, "Price must be greater than zero."

    if price > 9_999_999:
        return False, "Price exceeds maximum allowed value."

    return True, round(float(price), 2)


def counterflow_validate_quantity(qty: int) -> tuple[bool, str]:
    """
    CounterFlow — Validate a stock quantity or bill quantity.
    Must be a non-negative integer.

    Returns:
        (True, qty)            — if valid
        (False, error_message) — if invalid
    """
    if qty is None:
        return False, "Quantity cannot be empty."

    if not isinstance(qty, int):
        return False, "Quantity must be a whole number."

    if qty < 0:
        return False, "Quantity cannot be negative."

    if qty > 99_999:
        return False, "Quantity exceeds maximum allowed value."

    return True, qty


# ── Financial ──────────────────────────────────────────────────

def counterflow_validate_credit_limit(limit: float) -> tuple[bool, str]:
    """
    CounterFlow — Validate a customer credit limit.
    Must be zero or a positive number.

    Returns:
        (True, limit)          — if valid
        (False, error_message) — if invalid
    """
    if limit is None:
        return False, "Credit limit cannot be empty."

    if not isinstance(limit, (int, float)):
        return False, "Credit limit must be a number."

    if limit < 0:
        return False, "Credit limit cannot be negative."

    if limit > 9_999_999:
        return False, "Credit limit exceeds maximum allowed value."

    return True, round(float(limit), 2)


def counterflow_validate_payment_amount(amount: float) -> tuple[bool, str]:
    """
    CounterFlow — Validate a credit repayment amount.
    Must be a positive number greater than zero.

    Returns:
        (True, amount)         — if valid
        (False, error_message) — if invalid
    """
    if amount is None:
        return False, "Amount cannot be empty."

    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number."

    if amount <= 0:
        return False, "Amount must be greater than zero."

    if amount > 9_999_999:
        return False, "Amount exceeds maximum allowed value."

    return True, round(float(amount), 2)


# ── Customer Name ──────────────────────────────────────────────

def counterflow_validate_customer_name(name: str) -> tuple[bool, str]:
    """
    CounterFlow — Validate a customer name.
    Must be 1–255 characters, non-empty after stripping.

    Returns:
        (True, cleaned_name)   — if valid
        (False, error_message) — if invalid
    """
    counterflow_cleaned = name.strip()

    if not counterflow_cleaned:
        return False, "Customer name cannot be empty."

    if len(counterflow_cleaned) > 255:
        return False, "Customer name must not exceed 255 characters."

    return True, counterflow_cleaned


# ── Date Range ─────────────────────────────────────────────────

def counterflow_validate_date_range(
    start_date,
    end_date,
) -> tuple[bool, str]:
    """
    CounterFlow — Validate that start_date is not after end_date.
    Accepts Python date objects.

    Returns:
        (True, "")             — if valid range
        (False, error_message) — if invalid
    """
    if start_date is None or end_date is None:
        return False, "Both start and end dates are required."

    if start_date > end_date:
        return False, "Start date cannot be after end date."

    return True, ""
