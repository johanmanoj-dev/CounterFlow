# CounterFlow

A desktop retail management and billing system for small businesses.

## Features
- 🧾 **POS Billing** — Barcode scanner support, real-time invoice building
- 📦 **Inventory Management** — Stock tracking, barcode lookup, restock logging
- 👥 **Customer Management** — Mobile-number based profiles, credit accounts
- 💰 **Credit System** — Credit limits, balance tracking, payment recording
- 📋 **Sales History** — Full invoice history with line-item drill-down
- 📊 **Financial Overview** — Daily totals, outstanding credit, top products

## Tech Stack
- **Language:** Python 3.11+
- **UI:** PyQt6
- **Database:** SQLite (via SQLAlchemy ORM)
- **Reports:** ReportLab

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

## Project Structure
```
CounterFlow/
├── main.py                      # Entry point
├── requirements.txt
├── counterflow.db               # SQLite DB (auto-created on first run)
└── app/
    ├── config.py                # App settings
    ├── theme.py                 # Colors, fonts, stylesheet
    ├── db/
    │   ├── models.py            # SQLAlchemy ORM models
    │   └── database.py          # DB connection & session
    ├── core/
    │   ├── billing.py           # In-memory billing session
    │   ├── inventory_manager.py # Stock operations
    │   ├── customer_manager.py  # Customer CRUD & credit
    │   ├── credit_manager.py    # Atomic transaction finalizer
    │   └── report_generator.py  # Analytics queries
    └── ui/
        ├── components/
        │   ├── sidebar.py       # Navigation sidebar
        │   └── stat_card.py     # Dashboard stat cards
        └── screens/
            ├── dashboard.py
            ├── pos_billing.py
            ├── inventory.py
            ├── customers.py
            ├── sales_history.py
            └── financial_overview.py
```

## Key Design Decisions
- **Deferred inventory deduction** — Stock only decreases on bill finalization, never during scanning
- **Atomic transactions** — Invoice + stock updates + credit changes commit together or not at all
- **Mobile-first customers** — Phone number is the customer key; new customers auto-created at checkout
- **No network required** — Entirely local SQLite, works offline
