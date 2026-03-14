"""
CounterFlow v1.0.0 — Application Entry Point
==============================================
The single file you run to start CounterFlow.

Launch sequence:
    1. QApplication created
    2. Splash screen shown immediately
    3. Database directories verified
    4. Database initialized (tables created if needed)
    5. DB connection verified
    6. Session opened
    7. Main window created (hidden)
    8. Splash fades out → main window appears

Run:
    python main.py
"""

import sys
import os

# ── Ensure CounterFlow root is on sys.path ─────────────────────
# Required when running as a packaged EXE via PyInstaller
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from app.config import (
    counterflow_ensure_dirs,
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_VERSION,
    COUNTERFLOW_ICONS_DIR,
)
from app.db.database import (
    CounterFlowDatabase,
    counterflow_init_db,
    counterflow_verify_connection,
    counterflow_get_session,
)
from app.ui.components.splash_screen import CounterFlowSplashScreen
from app.ui.main_window import CounterFlowMainWindow
from app import theme as t


def counterflow_run():
    """
    CounterFlow — Main entry point.
    Sets up the Qt application and launches the main window.
    """

    # ── Qt Application ─────────────────────────────────────────
    counterflow_app = QApplication(sys.argv)
    counterflow_app.setApplicationName(COUNTERFLOW_APP_NAME)
    counterflow_app.setApplicationVersion(COUNTERFLOW_VERSION)
    counterflow_app.setOrganizationName("CN-6")

    # ── App icon ───────────────────────────────────────────────
    counterflow_icon_path = os.path.join(COUNTERFLOW_ICONS_DIR, "counterflow.ico")
    if os.path.exists(counterflow_icon_path):
        counterflow_app.setWindowIcon(QIcon(counterflow_icon_path))

    # ── Initial stylesheet (light mode default) ────────────────
    counterflow_app.setStyleSheet(t.counterflow_build_stylesheet())

    # ── Splash Screen ──────────────────────────────────────────
    counterflow_splash = CounterFlowSplashScreen()
    counterflow_splash.show()
    counterflow_app.processEvents()

    # ── Step 1: Ensure directories ─────────────────────────────
    try:
        counterflow_ensure_dirs()
    except Exception as counterflow_err:
        _counterflow_fatal_error(
            "CounterFlow — Startup Error",
            f"Failed to create required directories:\n\n{counterflow_err}"
        )
        return 1

    # ── Step 2: Initialize database ────────────────────────────
    try:
        counterflow_init_db()
    except Exception as counterflow_err:
        _counterflow_fatal_error(
            "CounterFlow — Database Error",
            f"Failed to initialize database:\n\n{counterflow_err}\n\n"
            f"Check that you have write access to the application folder."
        )
        return 1

    # ── Step 3: Verify connection ──────────────────────────────
    if not counterflow_verify_connection():
        _counterflow_fatal_error(
            "CounterFlow — Connection Error",
            "Could not connect to the CounterFlow database.\n\n"
            "The database file may be locked or corrupted.\n"
            "Try closing any other running instances of CounterFlow."
        )
        return 1

    # ── Step 4: Open session ───────────────────────────────────
    try:
        counterflow_session = counterflow_get_session()
    except Exception as counterflow_err:
        _counterflow_fatal_error(
            "CounterFlow — Session Error",
            f"Failed to open database session:\n\n{counterflow_err}"
        )
        return 1

    # ── Step 5: Create main window ─────────────────────────────
    try:
        counterflow_window = CounterFlowMainWindow(
            counterflow_session=counterflow_session
        )
    except Exception as counterflow_err:
        _counterflow_fatal_error(
            "CounterFlow — Window Error",
            f"Failed to create main window:\n\n{counterflow_err}"
        )
        return 1

    # ── Step 6: Dismiss splash → show window ───────────────────
    counterflow_splash.counterflow_finish(counterflow_window)
    counterflow_window.show()
    counterflow_window.raise_()
    counterflow_window.activateWindow()

    # ── Step 7: Run event loop ─────────────────────────────────
    counterflow_exit_code = counterflow_app.exec()

    # ── Step 8: Clean shutdown ─────────────────────────────────
    try:
        counterflow_session.close()
    except Exception:
        pass

    return counterflow_exit_code


def _counterflow_fatal_error(title: str, message: str):
    """
    CounterFlow — Show a fatal error dialog and exit.
    Used when the app cannot start due to a critical failure.
    """
    counterflow_err_box = QMessageBox()
    counterflow_err_box.setWindowTitle(title)
    counterflow_err_box.setText(message)
    counterflow_err_box.setIcon(QMessageBox.Icon.Critical)
    counterflow_err_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    counterflow_err_box.exec()


# ── Entry ──────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(counterflow_run())
