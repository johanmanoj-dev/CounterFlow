"""
CounterFlow v1.0.0 — Main Application Window
==============================================
Role-aware root window. After authentication:
  - ALL users  see: Dashboard, New Bill, Inventory, Customers,
                    Sales History, Financials, Database & Records
  - ADMIN only sees: Staff Management, Activity Logs

The sidebar adapts its nav items based on the logged-in role.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QLabel, QGraphicsOpacityEffect, QMessageBox, QApplication
)
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QPixmap

from app import theme as t
from app.config import COUNTERFLOW_APP_NAME, COUNTERFLOW_VERSION
from app.core.auth import counterflow_auth_session
from app.core.activity_logger import counterflow_log_action, CounterFlowActions
from app.ui.components.sidebar import CounterFlowSidebar

# Screens -- shared
from app.ui.screens.dashboard         import CounterFlowDashboardScreen
from app.ui.screens.pos_billing       import CounterFlowPOSScreen
from app.ui.screens.inventory         import CounterFlowInventoryScreen
from app.ui.screens.customers         import CounterFlowCustomersScreen
from app.ui.screens.sales_history     import CounterFlowSalesHistoryScreen
from app.ui.screens.financial_overview import CounterFlowFinancialScreen
from app.ui.screens.database_records  import CounterFlowDatabaseScreen

# Screens -- Admin only
from app.ui.screens.staff_management  import CounterFlowStaffScreen
from app.ui.screens.activity_logs     import CounterFlowActivityLogsScreen


# Screen key -> stack index (base 7 are always present)
COUNTERFLOW_SCREEN_INDEX = {
    "counterflow_dashboard":        0,
    "counterflow_new_bill":         1,
    "counterflow_inventory":        2,
    "counterflow_customers":        3,
    "counterflow_sales_history":    4,
    "counterflow_financials":       5,
    "counterflow_database_records": 6,
    # Admin-only
    "counterflow_staff_management": 7,
    "counterflow_activity_logs":    8,
}


class CounterFlowMainWindow(QMainWindow):
    """
    CounterFlow -- Root Application Window.

    Checks counterflow_auth_session.counterflow_is_admin to decide
    whether to add Admin-only screens/nav items.
    """

    # Emitted after the user confirms logout — main.py listens to
    # this to show the login screen again without restarting the app.
    counterflow_logout_completed = pyqtSignal()

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session = counterflow_session
        self._counterflow_screens = {}

        self._counterflow_setup_window()
        self._counterflow_build()
        self._counterflow_apply_theme()

        self._counterflow_sidebar.counterflow_set_active("counterflow_dashboard")
        QTimer.singleShot(200, self._counterflow_initial_refresh)

    # ------------------------------------------------------------------
    def _counterflow_setup_window(self):
        is_admin = counterflow_auth_session.counterflow_is_admin
        role_str = "Admin" if is_admin else "Staff"
        user_name = counterflow_auth_session.counterflow_display_name
        self.setWindowTitle(
            f"{COUNTERFLOW_APP_NAME}  v{COUNTERFLOW_VERSION}"
            f"  —  {user_name}  [{role_str}]"
        )
        self.setMinimumSize(1100, 680)
        self.resize(1280, 760)

    def _counterflow_build(self):
        counterflow_central = QWidget()
        counterflow_central.setObjectName("counterflowCentral")
        self.setCentralWidget(counterflow_central)

        counterflow_root = QHBoxLayout(counterflow_central)
        counterflow_root.setContentsMargins(0, 0, 0, 0)
        counterflow_root.setSpacing(0)

        # Sidebar (passes role so it can show/hide admin nav items)
        self._counterflow_sidebar = CounterFlowSidebar(
            is_admin=counterflow_auth_session.counterflow_is_admin
        )
        self._counterflow_sidebar.counterflow_page_changed.connect(
            self._counterflow_on_page_changed
        )
        self._counterflow_sidebar.counterflow_dark_mode_toggled.connect(
            self._counterflow_on_dark_mode_toggled
        )
        self._counterflow_sidebar.counterflow_logout_requested.connect(
            self._counterflow_on_logout
        )
        counterflow_root.addWidget(self._counterflow_sidebar)

        self._counterflow_stack = QStackedWidget()
        counterflow_root.addWidget(self._counterflow_stack)

        self._counterflow_build_screens()

    def _counterflow_build_screens(self):
        sess = self.counterflow_session

        # Always-present screens (indices 0-6)
        base_screens = [
            ("counterflow_dashboard",        CounterFlowDashboardScreen(sess)),
            ("counterflow_new_bill",         CounterFlowPOSScreen(sess)),
            ("counterflow_inventory",        CounterFlowInventoryScreen(sess)),
            ("counterflow_customers",        CounterFlowCustomersScreen(sess)),
            ("counterflow_sales_history",    CounterFlowSalesHistoryScreen(sess)),
            ("counterflow_financials",       CounterFlowFinancialScreen(sess)),
            ("counterflow_database_records", CounterFlowDatabaseScreen(sess)),
        ]

        for key, screen in base_screens:
            self._counterflow_stack.addWidget(screen)
            self._counterflow_screens[key] = screen

        # Admin-only screens (indices 7-8)
        if counterflow_auth_session.counterflow_is_admin:
            admin_screens = [
                ("counterflow_staff_management", CounterFlowStaffScreen(sess)),
                ("counterflow_activity_logs",    CounterFlowActivityLogsScreen(sess)),
            ]
            for key, screen in admin_screens:
                self._counterflow_stack.addWidget(screen)
                self._counterflow_screens[key] = screen

        # Wire bill-finalized refresh
        self._counterflow_screens["counterflow_new_bill"] \
            .counterflow_bill_finalized.connect(self._counterflow_on_bill_finalized)

    # -- Navigation ----------------------------------------------------
    def _counterflow_on_page_changed(self, key: str):
        idx = COUNTERFLOW_SCREEN_INDEX.get(key, 0)
        self._counterflow_stack.setCurrentIndex(idx)
        screen = self._counterflow_screens.get(key)
        if screen and hasattr(screen, "counterflow_refresh"):
            screen.counterflow_refresh()

    def _counterflow_initial_refresh(self):
        screen = self._counterflow_screens.get("counterflow_dashboard")
        if screen:
            screen.counterflow_refresh()

    # -- Bill Finalized -------------------------------------------------
    def _counterflow_on_bill_finalized(self):
        for key in [
            "counterflow_dashboard",
            "counterflow_sales_history",
            "counterflow_financials",
            "counterflow_inventory",
            "counterflow_customers",
        ]:
            screen = self._counterflow_screens.get(key)
            if screen and hasattr(screen, "counterflow_refresh"):
                screen.counterflow_refresh()

    # -- Dark Mode ------------------------------------------------------
    def _counterflow_on_dark_mode_toggled(self, is_dark: bool):
        pixmap = self.grab()
        self._theme_overlay = QLabel(self)
        self._theme_overlay.setPixmap(pixmap)
        self._theme_overlay.resize(self.size())
        self._theme_overlay.move(0, 0)
        self._theme_overlay.show()
        self._theme_overlay.raise_()

        self._theme_opacity = QGraphicsOpacityEffect(self._theme_overlay)
        self._theme_overlay.setGraphicsEffect(self._theme_opacity)

        t.counterflow_set_dark(is_dark)
        self._counterflow_apply_theme()
        self._counterflow_sidebar.counterflow_refresh_theme()

        for screen in self._counterflow_screens.values():
            if hasattr(screen, "counterflow_refresh_theme"):
                screen.counterflow_refresh_theme()

        self._theme_anim = QPropertyAnimation(self._theme_opacity, b"opacity", self)
        self._theme_anim.setDuration(350)
        self._theme_anim.setStartValue(1.0)
        self._theme_anim.setEndValue(0.0)
        self._theme_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._theme_anim.finished.connect(self._theme_overlay.deleteLater)
        self._theme_anim.start()

    def _counterflow_apply_theme(self):
        self.setStyleSheet(t.counterflow_build_stylesheet())

    # -- Logout --------------------------------------------------------
    def _counterflow_on_logout(self):
        """
        CounterFlow — Confirm then perform logout.
        Logs the LOGOUT action, clears the auth session,
        hides this window, and signals main.py to show login again.
        """
        user_name = counterflow_auth_session.counterflow_display_name
        reply = QMessageBox.question(
            self,
            "CounterFlow — Logout",
            f"Log out of CounterFlow?\n\nYou are signed in as  {user_name}.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Write logout audit entry
        try:
            counterflow_log_action(
                session=self.counterflow_session,
                user_id=counterflow_auth_session.counterflow_user_id,
                action_type=CounterFlowActions.ADMIN_LOGOUT,
                entity_type="user",
                entity_id=counterflow_auth_session.counterflow_user_id,
                details=f"User '{counterflow_auth_session.counterflow_display_name}' logged out.",
            )
            self.counterflow_session.commit()
        except Exception:
            pass

        # Clear in-memory session state
        counterflow_auth_session.counterflow_logout()

        # Hide this window and tell main.py to show the login screen.
        # Order matters: emit the signal BEFORE quit() so _logged_out
        # is True by the time exec() returns in main.py.
        self.hide()
        self.counterflow_logout_completed.emit()
        # Exit the event loop — without this, exec() in main.py never
        # returns and the login screen is never shown.
        QApplication.instance().quit()

    # -- Window Events --------------------------------------------------
    def closeEvent(self, event: QCloseEvent):
        try:
            if self.counterflow_session:
                self.counterflow_session.close()
        except Exception:
            pass
        event.accept()
