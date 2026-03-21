"""
CounterFlow v1.0.0 — Application Entry Point
==============================================
Launch sequence:
    1. QApplication created
    2. Splash screen shown during DB init (min 1.8 s)
    3. Splash closed — auth dialog opens cleanly
    4. AUTH FLOW:
       a) No users  -> Admin Setup (first run ever)
       b) Users     -> Login dialog (Admin or Staff)
    5. Main window shown (role-adapted)
    6. On Logout: login dialog re-shown, new window built for new user

Run:
    python main.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from app.config import (
    counterflow_ensure_dirs,
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_VERSION,
    COUNTERFLOW_ICONS_DIR,
)
from app.db.database import (
    counterflow_init_db,
    counterflow_verify_connection,
    counterflow_get_session,
)
from app.ui.components.splash_screen import CounterFlowSplashScreen
from app.ui.main_window import CounterFlowMainWindow
from app import theme as t

from app.core.auth import CounterFlowAuthManager, counterflow_auth_session
from app.core.activity_logger import counterflow_log_action, CounterFlowActions
from app.ui.dialogs.admin_setup import CounterFlowAdminSetupDialog
from app.ui.dialogs.login import CounterFlowLoginDialog

_COUNTERFLOW_SPLASH_MIN_SECS = 1.8


def counterflow_run():
    """CounterFlow — Main entry point."""

    # ── Qt Application ─────────────────────────────────────────
    counterflow_app = QApplication(sys.argv)
    counterflow_app.setApplicationName(COUNTERFLOW_APP_NAME)
    counterflow_app.setApplicationVersion(COUNTERFLOW_VERSION)
    counterflow_app.setOrganizationName("CN-6")

    icon_path = os.path.join(COUNTERFLOW_ICONS_DIR, "counterflow.ico")
    if os.path.exists(icon_path):
        counterflow_app.setWindowIcon(QIcon(icon_path))

    counterflow_app.setStyleSheet(t.counterflow_build_stylesheet())

    # ── Splash Screen ──────────────────────────────────────────
    counterflow_splash = CounterFlowSplashScreen()
    counterflow_splash.show()
    counterflow_app.processEvents()
    _splash_start = time.monotonic()

    # ── Step 1: Directories ────────────────────────────────────
    try:
        counterflow_ensure_dirs()
    except Exception as e:
        counterflow_splash.close()
        _counterflow_fatal_error("CounterFlow — Startup Error",
                                  f"Failed to create required directories:\n\n{e}")
        return 1

    # ── Step 2: Database init ──────────────────────────────────
    try:
        counterflow_init_db()
    except Exception as e:
        counterflow_splash.close()
        _counterflow_fatal_error("CounterFlow — Database Error",
                                  f"Failed to initialize database:\n\n{e}\n\n"
                                  "Check write access to the application folder.")
        return 1

    # ── Step 3: Verify connection ──────────────────────────────
    if not counterflow_verify_connection():
        counterflow_splash.close()
        _counterflow_fatal_error("CounterFlow — Connection Error",
                                  "Could not connect to the CounterFlow database.\n\n"
                                  "The file may be locked or corrupted.")
        return 1

    # ── Step 4: Open session ───────────────────────────────────
    try:
        counterflow_session = counterflow_get_session()
    except Exception as e:
        counterflow_splash.close()
        _counterflow_fatal_error("CounterFlow — Session Error",
                                  f"Failed to open database session:\n\n{e}")
        return 1

    # ── Hold splash for minimum visible duration ───────────────
    _elapsed = time.monotonic() - _splash_start
    _remaining = _COUNTERFLOW_SPLASH_MIN_SECS - _elapsed
    if _remaining > 0:
        _deadline = time.monotonic() + _remaining
        while time.monotonic() < _deadline:
            counterflow_app.processEvents()
            time.sleep(0.05)

    # ── Close splash BEFORE auth dialogs ──────────────────────
    counterflow_splash.close()
    counterflow_app.processEvents()

    # ── Auth manager (reused across logout/re-login cycles) ────
    auth_manager = CounterFlowAuthManager(counterflow_session)

    # ── Main loop: auth → window → optional re-login ──────────
    # Wrapping in a loop lets logout bring back the login screen
    # without killing the process.
    while True:
        # ── AUTH FLOW ─────────────────────────────────────────
        if not auth_manager.counterflow_has_any_user():
            # First run — create Admin account
            setup_dialog = CounterFlowAdminSetupDialog(auth_manager)
            if setup_dialog.exec() != CounterFlowAdminSetupDialog.DialogCode.Accepted:
                counterflow_session.close()
                return 0

            admin_user = setup_dialog.counterflow_created_user
            counterflow_auth_session.counterflow_login(admin_user)
            counterflow_log_action(
                session=counterflow_session,
                user_id=admin_user.counterflow_user_id,
                action_type=CounterFlowActions.ADMIN_LOGIN,
                entity_type="user",
                entity_id=admin_user.counterflow_user_id,
                details="First-run Admin account created and logged in.",
            )
            counterflow_session.commit()

        else:
            # Normal launch / re-login after logout
            login_dialog = CounterFlowLoginDialog(auth_manager)
            if login_dialog.exec() != CounterFlowLoginDialog.DialogCode.Accepted:
                # User closed the login window — exit the app
                counterflow_session.close()
                return 0

            user = counterflow_auth_session.counterflow_current_user
            action_type = (
                CounterFlowActions.ADMIN_LOGIN
                if user.counterflow_role == "ADMIN"
                else CounterFlowActions.STAFF_LOGIN
            )
            counterflow_log_action(
                session=counterflow_session,
                user_id=user.counterflow_user_id,
                action_type=action_type,
                entity_type="user",
                entity_id=user.counterflow_user_id,
                details=f"Logged in as {user.counterflow_role.title()}",
            )
            counterflow_session.commit()

        # ── Build and show main window ─────────────────────────
        try:
            counterflow_window = CounterFlowMainWindow(
                counterflow_session=counterflow_session,
            )
        except Exception as e:
            _counterflow_fatal_error("CounterFlow — Window Error",
                                      f"Failed to create main window:\n\n{e}")
            counterflow_session.close()
            return 1

        # Track whether the user logged out (vs. closed the window)
        _logged_out = False

        def _on_logout():
            nonlocal _logged_out
            _logged_out = True

        counterflow_window.counterflow_logout_completed.connect(_on_logout)

        counterflow_window.show()
        counterflow_window.raise_()
        counterflow_window.activateWindow()

        counterflow_app.exec()

        if not _logged_out:
            # Window was closed normally — exit the app
            break

        # User logged out — destroy the window and loop back to login
        counterflow_window.deleteLater()
        counterflow_app.processEvents()
        # Continue the while loop → login dialog shown again

    # ── Clean shutdown ─────────────────────────────────────────
    try:
        counterflow_session.close()
    except Exception:
        pass

    return 0


def _counterflow_fatal_error(title: str, message: str):
    err_box = QMessageBox()
    err_box.setWindowTitle(title)
    err_box.setText(message)
    err_box.setIcon(QMessageBox.Icon.Critical)
    err_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    err_box.exec()


if __name__ == "__main__":
    sys.exit(counterflow_run())
