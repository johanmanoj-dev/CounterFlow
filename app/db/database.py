"""
CounterFlow v1.0.0 — Database Engine & Session Management
==========================================================
Handles the SQLite connection, session factory,
and database initialization for CounterFlow.

Usage:
    counterflow_init_db()          → creates all tables on first run
    counterflow_get_session()      → returns a working DB session
    CounterFlowDatabase.instance() → singleton access anywhere in app
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from app.db.models import CounterFlowBase
from app.config import (
    COUNTERFLOW_DB_URL,
    COUNTERFLOW_DB_ECHO_SQL,
    COUNTERFLOW_DEBUG,
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_VERSION,
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


# ──────────────────────────────────────────────────────────────
class CounterFlowDatabase:
    """
    CounterFlow Database Singleton.
    Provides a single shared session throughout the app lifetime.
    Access via CounterFlowDatabase.instance()
    """
    _counterflow_instance = None
    _counterflow_session: Session = None

    @classmethod
    def counterflow_initialize(cls):
        """Initialize CounterFlow DB — call once at app startup."""
        counterflow_init_db()
        counterflow_verify_connection()
        cls._counterflow_session = counterflow_get_session()
        cls._counterflow_instance = cls()
        if COUNTERFLOW_DEBUG:
            print(f"[CounterFlow] {COUNTERFLOW_APP_NAME} v{COUNTERFLOW_VERSION} DB ready")

    @classmethod
    def instance(cls) -> "CounterFlowDatabase":
        """Returns the CounterFlow database singleton."""
        if cls._counterflow_instance is None:
            raise RuntimeError(
                "[CounterFlow] Database not initialized. "
                "Call CounterFlowDatabase.counterflow_initialize() first."
            )
        return cls._counterflow_instance

    @property
    def session(self) -> Session:
        """The active CounterFlow database session."""
        return self._counterflow_session

    def counterflow_close(self):
        """Cleanly close the CounterFlow database session on app exit."""
        if self._counterflow_session:
            self._counterflow_session.close()
            if COUNTERFLOW_DEBUG:
                print("[CounterFlow] Database session closed.")
