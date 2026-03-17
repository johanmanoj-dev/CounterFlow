"""
CounterFlow v1.0.0 — Database Engine & Session Management
==========================================================
Handles the SQLite connection, session factory,
and database initialization for CounterFlow.

Usage:
    counterflow_init_db()          → creates all tables on first run
    counterflow_get_session()      → returns a working DB session
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from app.db.models import CounterFlowBase
from app.config import (
    COUNTERFLOW_DB_URL,
    COUNTERFLOW_DB_ECHO_SQL,
    COUNTERFLOW_DEBUG,
)


# ── CounterFlow SQLite Performance Pragma ─────────────────────
@event.listens_for(Engine, "connect")
def counterflow_set_sqlite_pragma(dbapi_connection, connection_record):
    """
    CounterFlow SQLite optimizations applied on every connection.
    WAL mode improves concurrent read performance.
    Foreign keys must be explicitly enabled in SQLite.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


# ── CounterFlow Database Engine ────────────────────────────────
counterflow_engine = create_engine(
    COUNTERFLOW_DB_URL,
    connect_args={"check_same_thread": False},
    echo=COUNTERFLOW_DB_ECHO_SQL,
)

# ── CounterFlow Session Factory ────────────────────────────────
CounterFlowSessionLocal = sessionmaker(
    bind=counterflow_engine,
    autocommit=False,
    autoflush=False,
)


# ──────────────────────────────────────────────────────────────
def counterflow_init_db():
    """
    CounterFlow database initialization.
    Creates all CounterFlow tables if they do not already exist.
    Safe to call on every app startup — existing data is never dropped.
    """
    CounterFlowBase.metadata.create_all(bind=counterflow_engine)
    if COUNTERFLOW_DEBUG:
        print(f"[CounterFlow] Database initialized at {COUNTERFLOW_DB_URL}")


def counterflow_get_session() -> Session:
    """
    Returns a new CounterFlow database session.
    Caller is responsible for committing and closing the session.

    Example:
        session = counterflow_get_session()
        try:
            ...
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()
    """
    return CounterFlowSessionLocal()


def counterflow_verify_connection() -> bool:
    """
    CounterFlow startup health check.
    Verifies the SQLite database is reachable.
    Returns True if connection is healthy, False otherwise.
    """
    try:
        with counterflow_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        if COUNTERFLOW_DEBUG:
            print("[CounterFlow] Database connection verified ✓")
        return True
    except Exception as counterflow_db_error:
        print(f"[CounterFlow] Database connection failed: {counterflow_db_error}")
        return False

