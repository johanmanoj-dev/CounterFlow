"""
CounterFlow v1.0.0 — Staff Management Screen (Admin Only)
===========================================================
Allows the Admin to:
  - View all Staff accounts with status
  - Create new Staff accounts
  - Deactivate / Reactivate Staff accounts
  - Change Staff passwords
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QLineEdit, QMessageBox,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.core.auth import (
    CounterFlowAuthManager,
    CounterFlowPasswordError,
    CounterFlowDuplicateUserError,
    counterflow_auth_session,
)
from app.core.activity_logger import counterflow_log_action, CounterFlowActions
from app import theme as t


# ──────────────────────────────────────────────────────────────
class CounterFlowStaffScreen(QWidget):
    """
    CounterFlow — Admin-only Staff Management Screen.
    Lists all Staff, with actions to create / toggle / change password.
    """

    def __init__(self, counterflow_session, parent=None):
        super().__init__(parent)
        self.counterflow_session = counterflow_session
        self.counterflow_auth_manager = CounterFlowAuthManager(counterflow_session)

        self._counterflow_build()

    # ── Build ──────────────────────────────────────────────────

    def _counterflow_build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Staff Management")
        title.setObjectName("cfScreenTitle")
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)

        self.counterflow_add_btn = QPushButton("+ Add Staff Account")
        self.counterflow_add_btn.setObjectName("cfPrimaryBtn")
        self.counterflow_add_btn.setFixedHeight(40)
        self.counterflow_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.counterflow_add_btn.clicked.connect(self._counterflow_on_add_staff)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.counterflow_add_btn)
        layout.addLayout(header_row)

        # Info label
        info = QLabel(
            "Staff accounts can create bills, manage customers, and view inventory. "
            "Only Admins can delete customers, edit inventory, and access these settings."
        )
        info.setObjectName("cfInfoLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Table
        self.counterflow_table = QTableWidget()
        self.counterflow_table.setObjectName("cfTable")
        self.counterflow_table.setColumnCount(6)
        self.counterflow_table.setHorizontalHeaderLabels([
            "Username", "Display Name", "Status", "Created", "Control", "Change Password"
        ])
        self.counterflow_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.counterflow_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.counterflow_table.setAlternatingRowColors(True)
        self.counterflow_table.verticalHeader().setVisible(False)
        self.counterflow_table.setShowGrid(False)
        self.counterflow_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr = self.counterflow_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        
        self.counterflow_table.setColumnWidth(0, 140)
        self.counterflow_table.setColumnWidth(2, 100)
        self.counterflow_table.setColumnWidth(3, 130)
        self.counterflow_table.setColumnWidth(4, 130)
        self.counterflow_table.setColumnWidth(5, 180)
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counterflow_table.setRowHeight(0, 52)
        layout.addWidget(self.counterflow_table)

        self._counterflow_apply_style()
        self.counterflow_refresh()

    # ── Refresh ────────────────────────────────────────────────

    def counterflow_refresh(self):
        staff_list = self.counterflow_auth_manager.counterflow_get_all_staff()
        self.counterflow_table.setRowCount(len(staff_list))
        self.counterflow_table.setRowCount(0)

        for staff in staff_list:
            row = self.counterflow_table.rowCount()
            self.counterflow_table.insertRow(row)
            self.counterflow_table.setRowHeight(row, 52)

            # Username
            self.counterflow_table.setItem(row, 0, QTableWidgetItem(staff.counterflow_username))
            # Display Name
            self.counterflow_table.setItem(row, 1, QTableWidgetItem(staff.counterflow_display_name))
            # Status
            status_item = QTableWidgetItem("Active" if staff.counterflow_is_active else "Inactive")
            if staff.counterflow_is_active:
                status_item.setForeground(QColor("#22C55E"))
            else:
                status_item.setForeground(QColor("#EF4444"))
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.counterflow_table.setItem(row, 2, status_item)
            # Created at
            created = staff.counterflow_created_at.strftime("%d %b %Y") if staff.counterflow_created_at else "—"
            self.counterflow_table.setItem(row, 3, QTableWidgetItem(created))

            # Toggle button
            toggle_label = "Deactivate" if staff.counterflow_is_active else "Reactivate"
            toggle_btn = QPushButton(toggle_label)
            toggle_btn.setObjectName("cfDangerBtn" if staff.counterflow_is_active else "cfSuccessBtn")
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setFixedHeight(32)
            toggle_btn.clicked.connect(
                lambda checked, uid=staff.counterflow_user_id,
                uname=staff.counterflow_username,
                active=staff.counterflow_is_active: self._counterflow_toggle_staff(uid, active, uname)
            )
            self.counterflow_table.setCellWidget(row, 4, self._counterflow_center_widget(toggle_btn))

            # Change password button
            pw_btn = QPushButton("Change Password")
            pw_btn.setObjectName("cfSecondaryBtn")
            pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pw_btn.setFixedHeight(32)
            pw_btn.clicked.connect(
                lambda checked, uid=staff.counterflow_user_id,
                uname=staff.counterflow_username: self._counterflow_change_password(uid, uname)
            )
            self.counterflow_table.setCellWidget(row, 5, self._counterflow_center_widget(pw_btn))

    def _counterflow_center_widget(self, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        return container

    # ── Actions ────────────────────────────────────────────────

    def _counterflow_on_add_staff(self):
        dialog = _CounterFlowAddStaffDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, display_name, password = dialog.counterflow_get_values()
            try:
                staff = self.counterflow_auth_manager.counterflow_create_staff(
                    username=username,
                    display_name=display_name,
                    password=password,
                    admin_id=counterflow_auth_session.counterflow_user_id,
                )
                counterflow_log_action(
                    session=self.counterflow_session,
                    user_id=counterflow_auth_session.counterflow_user_id,
                    action_type=CounterFlowActions.STAFF_CREATED,
                    entity_type="user",
                    entity_id=staff.counterflow_user_id,
                    details=f"Username: {username} | Display: {display_name}",
                )
                self.counterflow_session.commit()
                QMessageBox.information(
                    self, "Success",
                    f"Staff account '{username}' created successfully."
                )
                self.counterflow_refresh()
            except (CounterFlowPasswordError, CounterFlowDuplicateUserError) as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Unexpected Error", str(e))

    def _counterflow_toggle_staff(self, user_id: int, currently_active: bool, username: str):
        action_word = "Deactivate" if currently_active else "Reactivate"
        reply = QMessageBox.question(
            self, f"Confirm {action_word}",
            f"Are you sure you want to {action_word.lower()} this staff account ('{username}')?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if currently_active:
                self.counterflow_auth_manager.counterflow_deactivate_staff(user_id)
                action_type = CounterFlowActions.STAFF_DEACTIVATED
            else:
                self.counterflow_auth_manager.counterflow_reactivate_staff(user_id)
                action_type = CounterFlowActions.STAFF_REACTIVATED
            counterflow_log_action(
                session=self.counterflow_session,
                user_id=counterflow_auth_session.counterflow_user_id,
                action_type=action_type,
                entity_type="user",
                entity_id=user_id,
                details=f"Target Staff: {username}",
            )
            self.counterflow_session.commit()
            self.counterflow_refresh()

    def _counterflow_change_password(self, user_id: int, username: str):
        dialog = _CounterFlowChangePasswordDialog(username, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_pw = dialog.counterflow_get_password()
            try:
                self.counterflow_auth_manager.counterflow_change_password(user_id, new_pw)
                counterflow_log_action(
                    session=self.counterflow_session,
                    user_id=counterflow_auth_session.counterflow_user_id,
                    action_type=CounterFlowActions.PASSWORD_CHANGED,
                    entity_type="user",
                    entity_id=user_id,
                    details=f"Password changed for: {username}",
                )
                self.counterflow_session.commit()
                QMessageBox.information(self, "Success", f"Password updated for '{username}'.")
            except CounterFlowPasswordError as e:
                QMessageBox.warning(self, "Password Error", str(e))

    # ── Style ──────────────────────────────────────────────────

    def _counterflow_apply_style(self):
        theme = t.counterflow_theme()
        self.setStyleSheet(f"""
            #cfScreenTitle {{ color: {theme['text_primary']}; font-weight: 700; }}
            #cfInfoLabel   {{ color: {theme['text_secondary']}; font-size: 13px; }}
            #cfPrimaryBtn  {{
                background: {theme['accent']}; color: #fff; border: none;
                border-radius: 8px; font-weight: 700; font-size: 13px; padding: 0 18px;
            }}
            #cfPrimaryBtn:hover {{ background: {theme['accent_hover']}; }}
            #cfDangerBtn   {{
                background: {theme['danger']}; color: #fff; border: none;
                border-radius: 6px; font-size: 12px; font-weight: 600; padding: 0 10px;
            }}
            #cfSuccessBtn  {{
                background: {theme['success']}; color: #fff; border: none;
                border-radius: 6px; font-size: 12px; font-weight: 600; padding: 0 10px;
            }}
            #cfSecondaryBtn {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 6px; font-size: 12px; padding: 0 10px;
            }}
            #cfSecondaryBtn:hover {{ border-color: {theme['accent']}; }}
        """)


# ──────────────────────────────────────────────────────────────
# ── Add Staff Dialog ──────────────────────────────────────────
# ──────────────────────────────────────────────────────────────

class _CounterFlowAddStaffDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Staff Account")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build()
        self._apply_style()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        title = QLabel("Create Staff Account")
        font = QFont(); font.setPointSize(15); font.setBold(True)
        title.setFont(font)
        title.setObjectName("cfDialogTitle")
        layout.addWidget(title)
        layout.addSpacing(4)

        self._display_name = self._field(layout, "Full Name", "e.g. Arjun Singh")
        self._username      = self._field(layout, "Username", "e.g. arjun (no spaces)")
        self._password      = self._field(layout, "Password", "Min 6 characters", pw=True)
        self._confirm       = self._field(layout, "Confirm Password", "Re-enter password", pw=True)

        self._error = QLabel("")
        self._error.setObjectName("cfAuthError")
        self._error.setWordWrap(True)
        self._error.setVisible(False)
        layout.addWidget(self._error)

        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("cfSecondaryBtn2")
        cancel.clicked.connect(self.reject)
        cancel.setFixedHeight(38)
        create = QPushButton("Create Account")
        create.setObjectName("cfPrimaryBtn")
        create.clicked.connect(self._on_submit)
        create.setFixedHeight(38)
        btn_row.addWidget(cancel)
        btn_row.addWidget(create)
        layout.addLayout(btn_row)
        self._confirm.returnPressed.connect(self._on_submit)

    def _field(self, layout, label_text, placeholder="", pw=False) -> QLineEdit:
        lbl = QLabel(label_text)
        lbl.setObjectName("cfFieldLabel")
        f = QFont(); f.setBold(True); f.setPointSize(10); lbl.setFont(f)
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(38)
        field.setObjectName("cfAuthField")
        if pw:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(lbl)
        layout.addWidget(field)
        return field

    def _on_submit(self):
        dn  = self._display_name.text().strip()
        un  = self._username.text().strip()
        pw  = self._password.text()
        cpw = self._confirm.text()
        if not dn or not un or not pw or not cpw:
            self._error.setText("⚠  All fields are required.")
            self._error.setVisible(True)
            return
        if " " in un:
            self._error.setText("⚠  Username must not contain spaces.")
            self._error.setVisible(True)
            return
        if pw != cpw:
            self._error.setText("⚠  Passwords do not match.")
            self._error.setVisible(True)
            self._confirm.clear()
            return
        self.accept()

    def counterflow_get_values(self):
        return (
            self._username.text().strip(),
            self._display_name.text().strip(),
            self._password.text(),
        )

    def _apply_style(self):
        theme = t.counterflow_theme()
        self.setStyleSheet(f"""
            QDialog {{ background: {theme['bg_main']}; }}
            #cfDialogTitle {{ color: {theme['text_primary']}; }}
            #cfFieldLabel  {{ color: {theme['text_primary']}; font-weight: 700; }}
            #cfAuthField   {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1.5px solid {theme['border']}; border-radius: 7px;
                padding: 0 10px; font-size: 13px;
            }}
            #cfAuthField:focus {{ border-color: {theme['accent']}; }}
            #cfPrimaryBtn  {{
                background: {theme['accent']}; color: #fff; border: none;
                border-radius: 8px; font-weight: 700; font-size: 13px;
            }}
            #cfSecondaryBtn2 {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 8px; font-size: 13px;
            }}
            #cfAuthError {{ color: {theme['danger']}; font-size: 12px; font-weight: 600; }}
        """)


# ──────────────────────────────────────────────────────────────
class _CounterFlowChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Change Password — {username}")
        self.setMinimumWidth(360)
        self._build()
        self._apply_style()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Set New Password")
        f = QFont(); f.setPointSize(14); f.setBold(True)
        title.setFont(f)
        title.setObjectName("cfDialogTitle")
        layout.addWidget(title)

        pw_lbl = QLabel("New Password")
        pw_lbl.setObjectName("cfFieldLabel")
        f2 = QFont(); f2.setBold(True); f2.setPointSize(10)
        pw_lbl.setFont(f2)
        self._pw = QLineEdit()
        self._pw.setPlaceholderText("Min 6 characters")
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setObjectName("cfAuthField")
        self._pw.setFixedHeight(38)

        self._error = QLabel("")
        self._error.setObjectName("cfAuthError")
        self._error.setVisible(False)

        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("cfSecondaryBtn2")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save")
        ok.setObjectName("cfPrimaryBtn")
        ok.clicked.connect(self._on_save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)

        layout.addWidget(pw_lbl)
        layout.addWidget(self._pw)
        layout.addWidget(self._error)
        layout.addLayout(btn_row)
        self._pw.returnPressed.connect(self._on_save)

    def _on_save(self):
        if len(self._pw.text()) < 6:
            self._error.setText("⚠  Password must be at least 6 characters.")
            self._error.setVisible(True)
            return
        self.accept()

    def counterflow_get_password(self) -> str:
        return self._pw.text()

    def _apply_style(self):
        theme = t.counterflow_theme()
        self.setStyleSheet(f"""
            QDialog {{ background: {theme['bg_main']}; }}
            #cfDialogTitle {{ color: {theme['text_primary']}; }}
            #cfFieldLabel  {{ color: {theme['text_primary']}; font-weight: 700; }}
            #cfAuthField   {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1.5px solid {theme['border']}; border-radius: 7px;
                padding: 0 10px; font-size: 13px;
            }}
            #cfAuthField:focus {{ border-color: {theme['accent']}; }}
            #cfPrimaryBtn  {{
                background: {theme['accent']}; color: #fff; border: none;
                border-radius: 8px; font-weight: 700; font-size: 13px;
            }}
            #cfSecondaryBtn2 {{
                background: {theme['bg_card']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 8px; font-size: 13px;
            }}
            #cfAuthError {{ color: {theme['danger']}; font-size: 12px; font-weight: 600; }}
        """)
