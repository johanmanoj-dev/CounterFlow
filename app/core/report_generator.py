"""
CounterFlow v1.0.0 — Report Generator
=======================================
Aggregates sales, inventory, and financial data
for CounterFlow's Dashboard and Financial Overview screens.

Class:
    CounterFlowReportGenerator — All analytics and summary queries
"""

from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    CounterFlowInvoice,
    CounterFlowInvoiceItem,
    CounterFlowProduct,
    CounterFlowCustomer,
    CounterFlowStockMovement,
)
from app.config import (
    COUNTERFLOW_PAYMENT_CASH,
    COUNTERFLOW_PAYMENT_UPI,
    COUNTERFLOW_PAYMENT_CREDIT,
    COUNTERFLOW_CURRENCY_SYMBOL,
)


# ──────────────────────────────────────────────────────────────
class CounterFlowReportGenerator:
    """
    CounterFlow — Report Generator.
    All queries are read-only. No data is ever modified here.
    Used by Dashboard, Financial Overview, and Sales History screens.
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session = counterflow_session

    # ── All-Time Summary ───────────────────────────────────────

    def counterflow_all_time_summary(self) -> dict:
        """
        CounterFlow — Aggregate totals across the entire invoice history.
        Uses SQL-level aggregation (SUM + CASE) to avoid loading all
        invoices into Python memory.
        """
        from sqlalchemy import case

        counterflow_row = (
            self.counterflow_session
            .query(
                func.coalesce(func.sum(CounterFlowInvoice.counterflow_total_amount), 0).label("total"),
                func.coalesce(func.sum(
                    case(
                        (CounterFlowInvoice.counterflow_payment_method == COUNTERFLOW_PAYMENT_CASH,
                         CounterFlowInvoice.counterflow_total_amount),
                        else_=0,
                    )
                ), 0).label("cash"),
                func.coalesce(func.sum(
                    case(
                        (CounterFlowInvoice.counterflow_payment_method == COUNTERFLOW_PAYMENT_UPI,
                         CounterFlowInvoice.counterflow_total_amount),
                        else_=0,
                    )
                ), 0).label("upi"),
                func.coalesce(func.sum(
                    case(
                        (CounterFlowInvoice.counterflow_payment_method == COUNTERFLOW_PAYMENT_CREDIT,
                         CounterFlowInvoice.counterflow_total_amount),
                        else_=0,
                    )
                ), 0).label("credit"),
                func.count(CounterFlowInvoice.counterflow_invoice_id).label("cnt"),
            )
            .one()
        )

        return {
            "counterflow_total_sales":   float(counterflow_row.total),
            "counterflow_cash_sales":    float(counterflow_row.cash),
            "counterflow_upi_sales":     float(counterflow_row.upi),
            "counterflow_credit_sales":  float(counterflow_row.credit),
            "counterflow_invoice_count": int(counterflow_row.cnt),
            "counterflow_display_total": f"{COUNTERFLOW_CURRENCY_SYMBOL}{float(counterflow_row.total):,.2f}",
        }

    # ── Daily Summary ──────────────────────────────────────────

    def counterflow_daily_summary(
        self,
        for_date: date = None
    ) -> dict:
        """
        CounterFlow — Generate a financial summary for a given date.
        Defaults to today if no date is provided.

        Returns dict with:
            counterflow_date, total_sales, cash_sales,
            upi_sales, credit_sales, invoice_count
        """
        counterflow_target_date = for_date or date.today()
        counterflow_start = datetime.combine(counterflow_target_date, datetime.min.time())
        counterflow_end   = datetime.combine(counterflow_target_date, datetime.max.time())

        counterflow_invoices = (
            self.counterflow_session
            .query(CounterFlowInvoice)
            .filter(
                CounterFlowInvoice.counterflow_created_at.between(
                    counterflow_start,
                    counterflow_end
                )
            )
            .all()
        )

        counterflow_total  = sum(i.counterflow_total_amount for i in counterflow_invoices)
        counterflow_cash   = sum(
            i.counterflow_total_amount for i in counterflow_invoices
            if i.counterflow_payment_method == COUNTERFLOW_PAYMENT_CASH
        )
        counterflow_upi    = sum(
            i.counterflow_total_amount for i in counterflow_invoices
            if i.counterflow_payment_method == COUNTERFLOW_PAYMENT_UPI
        )
        counterflow_credit = sum(
            i.counterflow_total_amount for i in counterflow_invoices
            if i.counterflow_payment_method == COUNTERFLOW_PAYMENT_CREDIT
        )

        return {
            "counterflow_date":          counterflow_target_date,
            "counterflow_total_sales":   counterflow_total,
            "counterflow_cash_sales":    counterflow_cash,
            "counterflow_upi_sales":     counterflow_upi,
            "counterflow_credit_sales":  counterflow_credit,
            "counterflow_invoice_count": len(counterflow_invoices),
            "counterflow_display_total": f"{COUNTERFLOW_CURRENCY_SYMBOL}{counterflow_total:,.2f}",
        }

    # ── Invoice Queries ────────────────────────────────────────

    def counterflow_recent_invoices(
        self,
        limit: int = 20
    ) -> list[CounterFlowInvoice]:
        """
        CounterFlow — Retrieve most recent invoices.
        Used in Dashboard recent transactions table
        and Sales History screen.
        """
        return (
            self.counterflow_session
            .query(CounterFlowInvoice)
            .order_by(CounterFlowInvoice.counterflow_created_at.desc())
            .limit(limit)
            .all()
        )

    def counterflow_invoices_by_date_range(
        self,
        start_date: date,
        end_date:   date,
    ) -> list[CounterFlowInvoice]:
        """CounterFlow — Retrieve invoices within a date range."""
        counterflow_start = datetime.combine(start_date, datetime.min.time())
        counterflow_end   = datetime.combine(end_date,   datetime.max.time())

        return (
            self.counterflow_session
            .query(CounterFlowInvoice)
            .filter(
                CounterFlowInvoice.counterflow_created_at.between(
                    counterflow_start,
                    counterflow_end
                )
            )
            .order_by(CounterFlowInvoice.counterflow_created_at.desc())
            .all()
        )

    # ── Product Analytics ──────────────────────────────────────

    def counterflow_top_selling_products(
        self,
        limit: int = 10
    ) -> list[dict]:
        """
        CounterFlow — Returns top selling products by units sold.
        Used in Financial Overview and Dashboard insights.
        """
        counterflow_results = (
            self.counterflow_session
            .query(
                CounterFlowProduct.counterflow_name,
                func.sum(CounterFlowInvoiceItem.counterflow_quantity).label("counterflow_units_sold"),
                func.sum(
                    CounterFlowInvoiceItem.counterflow_quantity *
                    CounterFlowInvoiceItem.counterflow_unit_price
                ).label("counterflow_revenue"),
            )
            .join(
                CounterFlowInvoiceItem,
                CounterFlowInvoiceItem.counterflow_product_id ==
                CounterFlowProduct.counterflow_product_id
            )
            .group_by(CounterFlowProduct.counterflow_product_id)
            .order_by(func.sum(CounterFlowInvoiceItem.counterflow_quantity * CounterFlowInvoiceItem.counterflow_unit_price).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "counterflow_name":       r.counterflow_name,
                "counterflow_units_sold": r.counterflow_units_sold,
                "counterflow_revenue":    r.counterflow_revenue,
                "counterflow_display_revenue": (
                    f"{COUNTERFLOW_CURRENCY_SYMBOL}{r.counterflow_revenue:,.2f}"
                ),
            }
            for r in counterflow_results
        ]

    # ── Credit Overview ────────────────────────────────────────

    def counterflow_outstanding_credit_summary(self) -> list[dict]:
        """
        CounterFlow — Returns all customers with outstanding credit balances.
        Used in Financial Overview credit table.
        """
        counterflow_customers = (
            self.counterflow_session
            .query(CounterFlowCustomer)
            .filter(CounterFlowCustomer.counterflow_credit_balance > 0)
            .order_by(CounterFlowCustomer.counterflow_credit_balance.desc())
            .all()
        )

        return [
            {
                "counterflow_customer_id":   c.counterflow_customer_id,
                "counterflow_name":          c.counterflow_name,
                "counterflow_mobile":        c.counterflow_mobile,
                "counterflow_balance":       c.counterflow_credit_balance,
                "counterflow_limit":         c.counterflow_credit_limit,
                "counterflow_usage_percent": round(
                    (c.counterflow_credit_balance / c.counterflow_credit_limit) * 100, 1
                ) if c.counterflow_credit_limit > 0 else 0,
                "counterflow_display_balance": (
                    f"{COUNTERFLOW_CURRENCY_SYMBOL}{c.counterflow_credit_balance:,.2f}"
                ),
            }
            for c in counterflow_customers
        ]

    def counterflow_total_outstanding_credit(self) -> float:
        """CounterFlow — Sum of all outstanding credit balances across all customers."""
        counterflow_result = (
            self.counterflow_session
            .query(func.sum(CounterFlowCustomer.counterflow_credit_balance))
            .scalar()
        )
        return counterflow_result or 0.0

    # ── Stock Movement Log ─────────────────────────────────────

    def counterflow_recent_stock_movements(
        self,
        limit: int = 50
    ) -> list[CounterFlowStockMovement]:
        """
        CounterFlow — Recent stock movement log.
        Used for inventory audit trail review.
        """
        return (
            self.counterflow_session
            .query(CounterFlowStockMovement)
            .order_by(CounterFlowStockMovement.counterflow_timestamp.desc())
            .limit(limit)
            .all()
        )
