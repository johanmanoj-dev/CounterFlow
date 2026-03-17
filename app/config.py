"""
CounterFlow v1.0.0 — Application Configuration
================================================
Central configuration file for the CounterFlow
retail management and billing system.
All constants, paths, and settings live here.
"""

import os

# ── CounterFlow Application Identity ──────────────────────────
COUNTERFLOW_APP_NAME        = "CounterFlow"
COUNTERFLOW_VERSION         = "1.0.0"

# ── CounterFlow Directory Paths ────────────────────────────────
COUNTERFLOW_BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTERFLOW_ASSETS_DIR      = os.path.join(COUNTERFLOW_BASE_DIR, "assets")
COUNTERFLOW_ICONS_DIR       = os.path.join(COUNTERFLOW_ASSETS_DIR, "icons")
COUNTERFLOW_FONTS_DIR       = os.path.join(COUNTERFLOW_ASSETS_DIR, "fonts")

# ── CounterFlow Database ───────────────────────────────────────
COUNTERFLOW_DB_FILENAME     = "counterflow.db"
COUNTERFLOW_DB_PATH         = os.path.join(COUNTERFLOW_BASE_DIR, COUNTERFLOW_DB_FILENAME)
COUNTERFLOW_DB_URL          = f"sqlite:///{COUNTERFLOW_DB_PATH}"

# ── CounterFlow Business Rules ─────────────────────────────────
COUNTERFLOW_DEFAULT_CREDIT_LIMIT    = 5000.0    # Default credit limit per customer (₹)
COUNTERFLOW_LOW_STOCK_THRESHOLD     = 5          # Alert when stock falls at or below this (red)
COUNTERFLOW_STOCK_WARNING_THRESHOLD = 20         # Amber badge when stock at or below this
COUNTERFLOW_CREDIT_NEAR_LIMIT_PCT   = 0.8        # 80 % — credit balance turns red at this ratio
COUNTERFLOW_MAX_BILL_ITEMS          = 100        # Max unique products in one bill
COUNTERFLOW_CURRENCY_SYMBOL         = "₹"

# ── CounterFlow Invoice Settings ──────────────────────────────
COUNTERFLOW_INVOICE_PREFIX          = "CF"       # Invoice numbers: CF-0001, CF-0002...
COUNTERFLOW_INVOICE_OUTPUT_DIR      = os.path.join(COUNTERFLOW_BASE_DIR, "invoices")

# ── CounterFlow Payment Methods ────────────────────────────────
COUNTERFLOW_PAYMENT_CASH            = "CASH"
COUNTERFLOW_PAYMENT_UPI             = "UPI"
COUNTERFLOW_PAYMENT_CREDIT          = "CREDIT"
COUNTERFLOW_PAYMENT_METHODS         = [
    COUNTERFLOW_PAYMENT_CASH,
    COUNTERFLOW_PAYMENT_UPI,
    COUNTERFLOW_PAYMENT_CREDIT,
]

# ── CounterFlow Stock Movement Types ──────────────────────────
COUNTERFLOW_STOCK_IN                = "IN"
COUNTERFLOW_STOCK_OUT               = "OUT"

# ── CounterFlow Debug ─────────────────────────────────────────
COUNTERFLOW_DEBUG                   = False      # Set True during development
COUNTERFLOW_DB_ECHO_SQL             = False      # Set True to log all SQL queries


def counterflow_ensure_dirs():
    """
    CounterFlow startup check — ensures all required
    directories exist before the app launches.
    """
    dirs = [
        COUNTERFLOW_ASSETS_DIR,
        COUNTERFLOW_ICONS_DIR,
        COUNTERFLOW_FONTS_DIR,
        COUNTERFLOW_INVOICE_OUTPUT_DIR,
    ]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
    if COUNTERFLOW_DEBUG:
        print(f"[CounterFlow] Directories verified at {COUNTERFLOW_BASE_DIR}")
