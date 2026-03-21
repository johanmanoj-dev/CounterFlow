"""
CounterFlow v1.0.0 — Database Models
=====================================
SQLAlchemy ORM table definitions for the CounterFlow
retail management system.

Tables:
    CounterFlowUser             — Authenticated users (Admin / Staff)
    CounterFlowActivityLog      — Immutable audit trail for all critical actions
    CounterFlowProduct          — Product catalog
    CounterFlowStockMovement    — Inventory audit trail
    CounterFlowCustomer         — Customer profiles and credit accounts
    CounterFlowInvoice          — Finalized sales bills
    CounterFlowInvoiceItem      — Line items within each invoice
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, Enum, Text, Boolean, MetaData
)
from sqlalchemy.orm import relationship, DeclarativeBase


# ── CounterFlow ORM Base ───────────────────────────────────────
class CounterFlowBase(DeclarativeBase):
    """Modern SQLAlchemy 2.0 declarative base for all CounterFlow models."""
    metadata = MetaData(naming_convention={
        "ix":  "counterflow_ix_%(column_0_label)s",
        "uq":  "counterflow_uq_%(table_name)s_%(column_0_name)s",
        "fk":  "counterflow_fk_%(table_name)s_%(column_0_name)s",
        "pk":  "counterflow_pk_%(table_name)s",
    })


# ──────────────────────────────────────────────────────────────
class CounterFlowUser(CounterFlowBase):
    """
    CounterFlow — User Table
    Stores Admin and Staff user accounts.
    Passwords are stored ONLY as bcrypt hashes — never in plain text.
    admin_id links a Staff account back to the Admin who created it.
    """
    __tablename__ = "counterflow_users"

    counterflow_user_id      = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_username     = Column(String(100), unique=True, nullable=False, index=True)
    counterflow_display_name = Column(String(255), nullable=False)
    counterflow_role         = Column(
        Enum("ADMIN", "STAFF", name="counterflow_role_enum"),
        nullable=False
    )
    # bcrypt hash — never plain text
    counterflow_password_hash = Column(String(255), nullable=False)
    # For STAFF accounts: which Admin created them
    counterflow_admin_id     = Column(
        Integer,
        ForeignKey("counterflow_users.counterflow_user_id"),
        nullable=True
    )
    counterflow_is_active    = Column(Boolean, default=True, nullable=False)
    counterflow_created_at   = Column(DateTime, default=datetime.now)

    # Self-referential: staff → their admin
    counterflow_admin        = relationship(
        "CounterFlowUser",
        remote_side="CounterFlowUser.counterflow_user_id",
        backref="counterflow_staff_members"
    )
    # Logs authored by this user
    counterflow_activity_logs = relationship(
        "CounterFlowActivityLog",
        back_populates="counterflow_user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<CounterFlowUser("
            f"id={self.counterflow_user_id}, "
            f"username='{self.counterflow_username}', "
            f"role={self.counterflow_role})>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowActivityLog(CounterFlowBase):
    """
    CounterFlow — Activity Log Table (Append-Only Audit Trail)
    Records every critical action performed by any user.
    This table is NEVER updated or deleted — only inserted into.

    action_type examples:
        BILL_CREATED, DEBT_CLEARED, CUSTOMER_CREATED,
        CUSTOMER_DELETED, INVENTORY_ADDED, INVENTORY_EDITED,
        STAFF_CREATED, STAFF_DEACTIVATED, ADMIN_LOGIN, STAFF_LOGIN
    """
    __tablename__ = "counterflow_activity_logs"

    counterflow_log_id      = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_timestamp   = Column(DateTime, default=datetime.now, nullable=False, index=True)
    counterflow_action_type = Column(String(60), nullable=False, index=True)
    counterflow_user_id     = Column(
        Integer,
        ForeignKey("counterflow_users.counterflow_user_id"),
        nullable=False
    )
    # What entity was affected (e.g. "customer", "product", "invoice")
    counterflow_entity_type = Column(String(60), nullable=True)
    counterflow_entity_id   = Column(Integer, nullable=True)
    # Optional JSON/text blob with extra context (amount, changes, etc.)
    counterflow_details     = Column(Text, nullable=True)

    counterflow_user = relationship(
        "CounterFlowUser",
        back_populates="counterflow_activity_logs"
    )

    def __repr__(self):
        return (
            f"<CounterFlowActivityLog("
            f"id={self.counterflow_log_id}, "
            f"action={self.counterflow_action_type}, "
            f"user_id={self.counterflow_user_id})>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowProduct(CounterFlowBase):
    """
    CounterFlow — Product Table
    Represents every item the shop stocks and sells.
    Barcode is the primary lookup key during POS scanning.
    """
    __tablename__ = "counterflow_products"

    counterflow_product_id      = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_barcode         = Column(String(100), unique=True, nullable=False, index=True)
    counterflow_name            = Column(String(255), nullable=False)
    counterflow_price           = Column(Float, nullable=False)
    counterflow_stock_qty       = Column(Integer, default=0, nullable=False)
    counterflow_is_active       = Column(Boolean, default=True)
    counterflow_created_at      = Column(DateTime, default=datetime.now)
    counterflow_updated_at      = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    counterflow_stock_movements = relationship(
        "CounterFlowStockMovement",
        back_populates="counterflow_product",
        cascade="all, delete-orphan"
    )
    counterflow_invoice_items   = relationship(
        "CounterFlowInvoiceItem",
        back_populates="counterflow_product"
    )

    def __repr__(self):
        return (
            f"<CounterFlowProduct("
            f"id={self.counterflow_product_id}, "
            f"name='{self.counterflow_name}', "
            f"stock={self.counterflow_stock_qty})>"
        )



# ──────────────────────────────────────────────────────────────
class CounterFlowStockMovement(CounterFlowBase):
    """
    CounterFlow — Stock Movement Table
    Audit log for every inventory change.
    IN  = stock added (restock, manual adjustment)
    OUT = stock removed (sale finalized)
    Every deduction is traceable back to an invoice.
    """
    __tablename__ = "counterflow_stock_movements"

    counterflow_movement_id     = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_product_id      = Column(
        Integer,
        ForeignKey("counterflow_products.counterflow_product_id"),
        nullable=False
    )
    counterflow_movement_type   = Column(
        Enum("IN", "OUT", name="counterflow_movement_type_enum"),
        nullable=False
    )
    counterflow_quantity        = Column(Integer, nullable=False)
    counterflow_reason          = Column(String(255), nullable=True)
    counterflow_reference_id    = Column(Integer, nullable=True)   # invoice id for OUT
    counterflow_timestamp       = Column(DateTime, default=datetime.now)

    # Relationship
    counterflow_product = relationship(
        "CounterFlowProduct",
        back_populates="counterflow_stock_movements"
    )

    def __repr__(self):
        return (
            f"<CounterFlowStockMovement("
            f"type={self.counterflow_movement_type}, "
            f"qty={self.counterflow_quantity}, "
            f"product_id={self.counterflow_product_id})>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowCustomer(CounterFlowBase):
    """
    CounterFlow — Customer Table
    Mobile number is the unique customer identifier.
    New customers are auto-created at checkout if not found.
    Credit balance tracks outstanding unpaid amounts.
    """
    __tablename__ = "counterflow_customers"

    counterflow_customer_id     = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_mobile          = Column(String(15), unique=True, nullable=False, index=True)
    counterflow_name            = Column(String(255), nullable=False)
    counterflow_credit_balance  = Column(Float, default=0.0, nullable=False)
    counterflow_credit_limit    = Column(Float, default=5000.0, nullable=False)
    counterflow_created_at      = Column(DateTime, default=datetime.now)

    # Relationship
    counterflow_invoices = relationship(
        "CounterFlowInvoice",
        back_populates="counterflow_customer"
    )

    def __repr__(self):
        return (
            f"<CounterFlowCustomer("
            f"id={self.counterflow_customer_id}, "
            f"name='{self.counterflow_name}', "
            f"mobile='{self.counterflow_mobile}')>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowInvoice(CounterFlowBase):
    """
    CounterFlow — Invoice Table
    One record per finalized bill.
    customer_id is nullable — NULL means walk-in customer.
    payment_method records how the bill was settled.
    """
    __tablename__ = "counterflow_invoices"

    counterflow_invoice_id      = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_customer_id     = Column(
        Integer,
        ForeignKey("counterflow_customers.counterflow_customer_id"),
        nullable=True
    )
    counterflow_total_amount    = Column(Float, nullable=False)
    counterflow_payment_method  = Column(
        Enum("CASH", "UPI", "CREDIT", name="counterflow_payment_method_enum"),
        nullable=False
    )
    counterflow_notes           = Column(Text, nullable=True)
    counterflow_created_at      = Column(DateTime, default=datetime.now)

    # Relationships
    counterflow_customer = relationship(
        "CounterFlowCustomer",
        back_populates="counterflow_invoices"
    )
    counterflow_items = relationship(
        "CounterFlowInvoiceItem",
        back_populates="counterflow_invoice",
        cascade="all, delete-orphan"
    )

    @property
    def counterflow_invoice_number(self) -> str:
        """Returns formatted invoice number e.g. CF-00042"""
        return f"CF-{self.counterflow_invoice_id:05d}"

    def __repr__(self):
        return (
            f"<CounterFlowInvoice("
            f"id={self.counterflow_invoice_id}, "
            f"total={self.counterflow_total_amount}, "
            f"method={self.counterflow_payment_method})>"
        )


# ──────────────────────────────────────────────────────────────
class CounterFlowInvoiceItem(CounterFlowBase):
    """
    CounterFlow — Invoice Item Table
    One record per product line in a finalized invoice.
    unit_price is a snapshot of the price at time of sale —
    changing the product price later won't affect old invoices.
    """
    __tablename__ = "counterflow_invoice_items"

    counterflow_item_id         = Column(Integer, primary_key=True, autoincrement=True)
    counterflow_invoice_id      = Column(
        Integer,
        ForeignKey("counterflow_invoices.counterflow_invoice_id"),
        nullable=False
    )
    counterflow_product_id      = Column(
        Integer,
        ForeignKey("counterflow_products.counterflow_product_id"),
        nullable=False
    )
    counterflow_quantity        = Column(Integer, nullable=False)
    counterflow_unit_price      = Column(Float, nullable=False)   # price snapshot at sale time

    # Relationships
    counterflow_invoice = relationship(
        "CounterFlowInvoice",
        back_populates="counterflow_items"
    )
    counterflow_product = relationship(
        "CounterFlowProduct",
        back_populates="counterflow_invoice_items"
    )

    @property
    def counterflow_line_total(self) -> float:
        """CounterFlow computed line total for this item."""
        return self.counterflow_quantity * self.counterflow_unit_price

    def __repr__(self):
        return (
            f"<CounterFlowInvoiceItem("
            f"invoice={self.counterflow_invoice_id}, "
            f"product={self.counterflow_product_id}, "
            f"qty={self.counterflow_quantity})>"
        )
