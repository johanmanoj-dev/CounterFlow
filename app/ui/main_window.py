"""
CounterFlow v1.0.0 — Main Application Window
==============================================
The root QMainWindow that hosts the sidebar
and all 7 screens inside a QStackedWidget.
Wires sidebar nav signals to screen switching.
Handles dark mode propagation to all screens.
Handles bill-finalized refresh across screens.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent

from app import theme as t
from app.config import (
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_VERSION,
)
from app.ui.components.sidebar import CounterFlowSidebar

# ── Screens ────────────────────────────────────────────────────
from app.ui.screens.dashboard         import CounterFlowDashboardScreen
from app.ui.screens.pos_billing       import CounterFlowPOSScreen
from app.ui.screens.inventory         import CounterFlowInventoryScreen
from app.ui.screens.customers         import CounterFlowCustomersScreen
from app.ui.screens.sales_history     import CounterFlowSalesHistoryScreen
from app.ui.screens.financial_overview import CounterFlowFinancialScreen
from app.ui.screens.database_records  import CounterFlowDatabaseScreen


# ── Screen key → index mapping ─────────────────────────────────
COUNTERFLOW_SCREEN_INDEX = {
    "counterflow_dashboard":        0,
    "counterflow_new_bill":         1,
    "counterflow_inventory":        2,
    "counterflow_customers":        3,
    "counterflow_sales_history":    4,
    "counterflow_financials":       5,
    "counterflow_database_records": 6,
}


class CounterFlowMainWindow(QMainWindow):
    """
    CounterFlow — Root Application Window.

    Layout:
        QMainWindow
        └── central_widget (QHBoxLayout)
            ├── CounterFlowSidebar        (fixed width left panel)
            └── QStackedWidget            (all 7 screens)

    The sidebar emits counterflow_page_changed(key) →
    main window switches the stacked widget to the matching screen.
    """

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session = counterflow_session
        self._counterflow_screens = {}

        self._counterflow_setup_window()
        self._counterflow_build()
        self._counterflow_apply_theme()

        # Start on dashboard
        self._counterflow_sidebar.counterflow_set_active("counterflow_dashboard")
        QTimer.singleShot(200, self._counterflow_initial_refresh)

    # ── Setup ──────────────────────────────────────────────────

    def _counterflow_setup_window(self):
        """CounterFlow — Configure the main window properties."""
        self.setWindowTitle(
            f"{COUNTERFLOW_APP_NAME} — Retail Management & Billing  "
            f"v{COUNTERFLOW_VERSION}"
        )
        self.setMinimumSize(1100, 680)
        self.resize(1280, 760)

    def _counterflow_build(self):
        """CounterFlow — Build the full window layout."""

        # ── Central widget ─────────────────────────────────────
        counterflow_central = QWidget()
        counterflow_central.setObjectName("counterflowCentral")
        self.setCentralWidget(counterflow_central)

        counterflow_root = QHBoxLayout(counterflow_central)
        counterflow_root.setContentsMargins(0, 0, 0, 0)
        counterflow_root.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────
        self._counterflow_sidebar = CounterFlowSidebar()
        self._counterflow_sidebar.counterflow_page_changed.connect(
            self._counterflow_on_page_changed
        )
        self._counterflow_sidebar.counterflow_dark_mode_toggled.connect(
            self._counterflow_on_dark_mode_toggled
        )
        counterflow_root.addWidget(self._counterflow_sidebar)

        # ── Stacked screens ────────────────────────────────────
        self._counterflow_stack = QStackedWidget()
        counterflow_root.addWidget(self._counterflow_stack)

        # ── Instantiate all screens ────────────────────────────
        self._counterflow_build_screens()

    def _counterflow_build_screens(self):
        """CounterFlow — Create all 7 screens and add to stack."""
        sess = self.counterflow_session

        # Order MUST match COUNTERFLOW_SCREEN_INDEX values
        counterflow_screen_list = [
            ("counterflow_dashboard",        CounterFlowDashboardScreen(sess)),
            ("counterflow_new_bill",         CounterFlowPOSScreen(sess)),
            ("counterflow_inventory",        CounterFlowInventoryScreen(sess)),
            ("counterflow_customers",        CounterFlowCustomersScreen(sess)),
            ("counterflow_sales_history",    CounterFlowSalesHistoryScreen(sess)),
            ("counterflow_financials",       CounterFlowFinancialScreen(sess)),
            ("counterflow_database_records", CounterFlowDatabaseScreen(sess)),
        ]

        for counterflow_key, counterflow_screen in counterflow_screen_list:
            self._counterflow_stack.addWidget(counterflow_screen)
            self._counterflow_screens[counterflow_key] = counterflow_screen

        # Wire bill finalized signal from POS → refresh other screens
        self._counterflow_screens["counterflow_new_bill"] \
            .counterflow_bill_finalized.connect(
                self._counterflow_on_bill_finalized
            )

    # ── Navigation ─────────────────────────────────────────────

    def _counterflow_on_page_changed(self, key: str):
        """CounterFlow — Switch visible screen when sidebar nav is clicked."""
        counterflow_index = COUNTERFLOW_SCREEN_INDEX.get(key, 0)
        self._counterflow_stack.setCurrentIndex(counterflow_index)

        # Refresh the screen being switched to
        counterflow_screen = self._counterflow_screens.get(key)
        if counterflow_screen and hasattr(counterflow_screen, "counterflow_refresh"):
            counterflow_screen.counterflow_refresh()

    def _counterflow_initial_refresh(self):
        """CounterFlow — Refresh dashboard on first load."""
        counterflow_screen = self._counterflow_screens.get("counterflow_dashboard")
        if counterflow_screen:
            counterflow_screen.counterflow_refresh()

    # ── Bill Finalized ─────────────────────────────────────────

    def _counterflow_on_bill_finalized(self):
        """
        CounterFlow — Called after a bill is successfully finalized.
        Refreshes dashboard, sales history, financials, and inventory
        so data is current across all screens.
        """
        for counterflow_key in [
            "counterflow_dashboard",
            "counterflow_sales_history",
            "counterflow_financials",
            "counterflow_inventory",
            "counterflow_customers",
        ]:
            counterflow_screen = self._counterflow_screens.get(counterflow_key)
            if counterflow_screen and hasattr(counterflow_screen, "counterflow_refresh"):
                counterflow_screen.counterflow_refresh()

    # ── Dark Mode ──────────────────────────────────────────────

    def _counterflow_on_dark_mode_toggled(self, is_dark: bool):
        """
        CounterFlow — Apply dark/light theme across the entire app.
        Rebuilds the stylesheet and notifies all screens.
        """
        t.counterflow_set_dark(is_dark)
        self._counterflow_apply_theme()
        self._counterflow_sidebar.counterflow_refresh_theme()

        # Refresh theme on screens that support it
        for counterflow_screen in self._counterflow_screens.values():
            if hasattr(counterflow_screen, "counterflow_refresh_theme"):
                counterflow_screen.counterflow_refresh_theme()

    def _counterflow_apply_theme(self):
        """CounterFlow — Apply the current theme stylesheet to the app."""
        self.setStyleSheet(t.counterflow_build_stylesheet())

    # ── Window Events ──────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent):
        """CounterFlow — Clean up DB session on window close."""
        try:
            if self.counterflow_session:
                self.counterflow_session.close()
        except Exception:
            pass
        event.accept()
