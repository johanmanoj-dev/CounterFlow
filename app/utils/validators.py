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
