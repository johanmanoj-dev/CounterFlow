"""
CounterFlow v1.0.0 — Activity Logs Screen (Admin Only)
=========================================================
Displays the full immutable audit trail with filters.
Admins can filter by action type and by user.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.core.activity_logger import CounterFlowActivityLogManager, CounterFlowActions
from app.core.auth import CounterFlowAuthManager
from app.db.models import CounterFlowUser
from app import theme as t


# ── All loggable action types for the filter dropdown ─────────
_CF_ALL_ACTIONS = [
    ("All Actions", None),
    ("Bill Created",         CounterFlowActions.BILL_CREATED),
    ("Customer Created",     CounterFlowActions.CUSTOMER_CREATED),
    ("Customer Deleted",     CounterFlowActions.CUSTOMER_DELETED),
    ("Debt Cleared",         CounterFlowActions.DEBT_CLEARED),
    ("Inventory Added",      CounterFlowActions.INVENTORY_ADDED),
    ("Inventory Edited",     CounterFlowActions.INVENTORY_EDITED),
    ("Inventory Deleted",    CounterFlowActions.INVENTORY_DELETED),
    ("Stock Restocked",      CounterFlowActions.STOCK_RESTOCKED),
    ("Admin Login",          CounterFlowActions.ADMIN_LOGIN),
    ("Staff Login",          CounterFlowActions.STAFF_LOGIN),
    ("Staff Created",        CounterFlowActions.STAFF_CREATED),
    ("Staff Deactivated",    CounterFlowActions.STAFF_DEACTIVATED),
    ("Staff Reactivated",    CounterFlowActions.STAFF_REACTIVATED),
    ("Password Changed",     CounterFlowActions.PASSWORD_CHANGED),
]

# Action type → badge color
_CF_ACTION_COLORS = {
    "BILL_CREATED":       "#3B82F6",
    "CUSTOMER_CREATED":   "#22C55E",
    "CUSTOMER_DELETED":   "#EF4444",
    "DEBT_CLEARED":       "#F59E0B",
    "INVENTORY_ADDED":    "#22C55E",
    "INVENTORY_EDITED":   "#8B5CF6",
    "INVENTORY_DELETED":  "#EF4444",
    "STOCK_RESTOCKED":    "#06B6D4",
    "ADMIN_LOGIN":        "#6366F1",
    "STAFF_LOGIN":        "#6366F1",
    "STAFF_CREATED":      "#22C55E",
    "STAFF_DEACTIVATED":  "#EF4444",
    "STAFF_REACTIVATED":  "#22C55E",
    "PASSWORD_CHANGED":   "#F59E0B",
    "LOGOUT":             "#94A3B8",
}


class CounterFlowActivityLogsScreen(QWidget):
    """
    CounterFlow — Activity Logs Screen (Admin Only).
    Shows a filterable, read-only table of all audit log entries.
    """

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session = counterflow_session
        self.counterflow_log_manager  = CounterFlowActivityLogManager(counterflow_session)
        self.counterflow_auth_manager = CounterFlowAuthManager(counterflow_session)
        self._counterflow_user_map: dict[int, str] = {}

        self._counterflow_build()
        self._counterflow_apply_style()

    # ── Build ──────────────────────────────────────────────────

    def _counterflow_build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Activity Logs")
        title.setObjectName("cfScreenTitle")
        font = QFont(); font.setPointSize(20); font.setBold(True)
        title.setFont(font)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("cfSecondaryBtn")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.counterflow_refresh)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        filter_lbl = QLabel("Filter by action:")
        filter_lbl.setObjectName("cfFilterLabel")

        self.counterflow_action_filter = QComboBox()
        self.counterflow_action_filter.setObjectName("cfComboBox")
        self.counterflow_action_filter.setFixedHeight(36)
        self.counterflow_action_filter.setMinimumWidth(200)
        for display, _ in _CF_ALL_ACTIONS:
            self.counterflow_action_filter.addItem(display)
        self.counterflow_action_filter.currentIndexChanged.connect(self.counterflow_refresh)

        user_lbl = QLabel("Filter by user:")
        user_lbl.setObjectName("cfFilterLabel")

        self.counterflow_user_filter = QComboBox()
        self.counterflow_user_filter.setObjectName("cfComboBox")
        self.counterflow_user_filter.setFixedHeight(36)
        self.counterflow_user_filter.setMinimumWidth(180)
        self.counterflow_user_filter.currentIndexChanged.connect(self.counterflow_refresh)

        filter_row.addWidget(filter_lbl)
        filter_row.addWidget(self.counterflow_action_filter)
        filter_row.addSpacing(12)
        filter_row.addWidget(user_lbl)
        filter_row.addWidget(self.counterflow_user_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Table
        self.counterflow_table = QTableWidget()
        self.counterflow_table.setObjectName("cfTable")
        self.counterflow_table.setColumnCount(6)
        self.counterflow_table.setHorizontalHeaderLabels([
            "Timestamp", "Action", "User", "Entity Type", "Entity ID", "Details"
        ])
        self.counterflow_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.counterflow_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.counterflow_table.setAlternatingRowColors(True)
        self.counterflow_table.verticalHeader().setVisible(False)
        self.counterflow_table.setShowGrid(False)
        self.counterflow_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr = self.counterflow_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        
        self.counterflow_table.setColumnWidth(0, 180)
        self.counterflow_table.setColumnWidth(3, 140)
        self.counterflow_table.setColumnWidth(4, 120)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.counterflow_table)

        # Populate user filter (done once)
        self._counterflow_populate_user_filter()

    def _counterflow_populate_user_filter(self):
        """Build user list for the filter dropdown."""
        self.counterflow_user_filter.blockSignals(True)
        self.counterflow_user_filter.clear()
        self.counterflow_user_filter.addItem("All Users", None)

        from app.db.models import CounterFlowUser
        users = self.counterflow_session.query(CounterFlowUser).all()
        self._counterflow_user_map = {}
        for u in users:
            self._counterflow_user_map[u.counterflow_user_id] = (
                f"{u.counterflow_display_name} ({u.counterflow_username})"
            )
            self.counterflow_user_filter.addItem(
                f"{u.counterflow_display_name} ({u.counterflow_username})",
                u.counterflow_user_id
            )
        self.counterflow_user_filter.blockSignals(False)

    # ── Refresh ────────────────────────────────────────────────

    def counterflow_refresh(self):
        # Determine filters
        action_idx = self.counterflow_action_filter.currentIndex()
        _, selected_action = _CF_ALL_ACTIONS[action_idx]

        selected_user_id = self.counterflow_user_filter.currentData()

        logs = self.counterflow_log_manager.counterflow_get_filtered_logs(
            action_type=selected_action,
            user_id=selected_user_id,
            limit=500,
        )

        self.counterflow_table.setRowCount(0)
        for log in logs:
            row = self.counterflow_table.rowCount()
            self.counterflow_table.insertRow(row)
            self.counterflow_table.setRowHeight(row, 44)

            # Timestamp
            ts = log.counterflow_timestamp.strftime("%d %b %Y  %H:%M:%S") if log.counterflow_timestamp else "—"
            self.counterflow_table.setItem(row, 0, QTableWidgetItem(ts))

            # Action badge
            action_item = QTableWidgetItem(log.counterflow_action_type)
            color = _CF_ACTION_COLORS.get(log.counterflow_action_type, "#94A3B8")
            action_item.setForeground(QColor(color))
            action_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.counterflow_table.setItem(row, 1, action_item)

            # User
            user_display = self._counterflow_user_map.get(log.counterflow_user_id, f"User #{log.counterflow_user_id}")
            self.counterflow_table.setItem(row, 2, QTableWidgetItem(user_display))

            # Entity type
            self.counterflow_table.setItem(row, 3, QTableWidgetItem(log.counterflow_entity_type or "—"))

            # Entity ID
            eid = str(log.counterflow_entity_id) if log.counterflow_entity_id else "—"
            eid_item = QTableWidgetItem(eid)
            eid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.counterflow_table.setItem(row, 4, eid_item)

            # Details
            self.counterflow_table.setItem(row, 5, QTableWidgetItem(log.counterflow_details or ""))

    # ── Style ──────────────────────────────────────────────────

    def _counterflow_apply_style(self):
        theme = t.counterflow_theme()
        self.setStyleSheet(f"""
            #cfScreenTitle  {{ color: {theme['text_primary']}; font-weight: 700; }}
            #cfFilterLabel  {{ color: {theme['text_secondary']}; font-size: 13px; font-weight: 600; }}
            #cfSecondaryBtn {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 8px; font-size: 13px;
                padding: 0 14px;
            }}
            #cfSecondaryBtn:hover {{ border-color: {theme['accent']}; }}
            #cfComboBox {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 7px;
                padding: 0 10px; font-size: 13px;
            }}
        """)
