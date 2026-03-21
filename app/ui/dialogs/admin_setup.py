"""
CounterFlow v1.0.0 — First-Run Admin Setup Dialog
===================================================
Shown ONLY once on the very first launch of CounterFlow,
when no users exist in the database.
Guides the shop owner through creating the primary Admin account.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.auth import (
    CounterFlowAuthManager,
    CounterFlowPasswordError,
    CounterFlowDuplicateUserError,
)
from app import theme as t


class CounterFlowAdminSetupDialog(QDialog):
    """
    CounterFlow — First-run Admin account creation dialog.

    Validates:
      - All fields filled
      - Password meets policy (min 6 chars)
      - Password and confirm-password match

    On success: creates the Admin user and closes with Accepted.
    Cannot be dismissed without completing setup.
    """

    def __init__(self, auth_manager: CounterFlowAuthManager, parent=None):
        super().__init__(parent)
        self.counterflow_auth_manager = auth_manager
        self.counterflow_created_user = None

        self.setWindowTitle("CounterFlow — First-Time Setup")
        self.setMinimumWidth(480)
        self.setModal(True)
        # Prevent closing without completing
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._counterflow_build()
        self._counterflow_apply_style()

    # ── Build UI ───────────────────────────────────────────────

    def _counterflow_build(self):
        theme = t.counterflow_theme()
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ─────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("cfAuthHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(36, 32, 36, 28)
        header_layout.setSpacing(8)

        title = QLabel("Welcome to CounterFlow")
        title.setObjectName("cfAuthTitle")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "This is your first launch. Set up the Admin account\n"
            "for the shop owner before you can continue."
        )
        subtitle.setObjectName("cfAuthSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        # ── Form ───────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setObjectName("cfAuthForm")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(40, 32, 40, 36)
        form_layout.setSpacing(16)

        self.counterflow_display_name_input = self._counterflow_labeled_field(
            form_layout, "Full Name (Display Name)", placeholder="e.g. Ravi Kumar"
        )
        self.counterflow_username_input = self._counterflow_labeled_field(
            form_layout, "Username", placeholder="e.g. admin (lowercase, no spaces)"
        )
        self.counterflow_password_input = self._counterflow_labeled_field(
            form_layout, "Password", placeholder="Minimum 6 characters", is_password=True
        )
        self.counterflow_confirm_input = self._counterflow_labeled_field(
            form_layout, "Confirm Password", placeholder="Re-enter password", is_password=True
        )

        # ── Error label ────────────────────────────────────────
        self.counterflow_error_label = QLabel("")
        self.counterflow_error_label.setObjectName("cfAuthError")
        self.counterflow_error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counterflow_error_label.setWordWrap(True)
        self.counterflow_error_label.setVisible(False)
        form_layout.addWidget(self.counterflow_error_label)

        # ── Submit button ──────────────────────────────────────
        self.counterflow_submit_btn = QPushButton("Create Admin Account")
        self.counterflow_submit_btn.setObjectName("cfAuthSubmit")
        self.counterflow_submit_btn.setFixedHeight(46)
        self.counterflow_submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.counterflow_submit_btn.clicked.connect(self._counterflow_on_submit)
        form_layout.addWidget(self.counterflow_submit_btn)

        layout.addWidget(form_frame)

        # Enter key triggers submit
        self.counterflow_confirm_input.returnPressed.connect(self._counterflow_on_submit)

    def _counterflow_labeled_field(
        self,
        layout,
        label_text: str,
        placeholder: str = "",
        is_password: bool = False,
    ) -> QLineEdit:
        container = QVBoxLayout()
        container.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("cfFieldLabel")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        label.setFont(font)

        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(42)
        field.setObjectName("cfAuthField")
        if is_password:
            field.setEchoMode(QLineEdit.EchoMode.Password)

        container.addWidget(label)
        container.addWidget(field)
        layout.addLayout(container)
        return field

    # ── Submit Logic ───────────────────────────────────────────

    def _counterflow_on_submit(self):
        display_name = self.counterflow_display_name_input.text().strip()
        username     = self.counterflow_username_input.text().strip()
        password     = self.counterflow_password_input.text()
        confirm      = self.counterflow_confirm_input.text()

        # Field validation
        if not display_name or not username or not password or not confirm:
            self._counterflow_show_error("All fields are required.")
            return

        if " " in username:
            self._counterflow_show_error("Username must not contain spaces.")
            return

        if password != confirm:
            self._counterflow_show_error("Passwords do not match. Please re-enter.")
            self.counterflow_confirm_input.clear()
            self.counterflow_confirm_input.setFocus()
            return

        try:
            user = self.counterflow_auth_manager.counterflow_create_admin(
                username=username,
                display_name=display_name,
                password=password,
            )
            self.counterflow_created_user = user
            self.accept()

        except CounterFlowPasswordError as e:
            self._counterflow_show_error(str(e))
        except CounterFlowDuplicateUserError as e:
            self._counterflow_show_error(str(e))
        except Exception as e:
            self._counterflow_show_error(f"Unexpected error: {e}")

    def _counterflow_show_error(self, message: str):
        self.counterflow_error_label.setText(f"⚠  {message}")
        self.counterflow_error_label.setVisible(True)

    # ── Style ──────────────────────────────────────────────────

    def _counterflow_apply_style(self):
        theme = t.counterflow_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background: {theme['bg_main']};
            }}
            #cfAuthHeader {{
                background: {theme['accent']};
                border-radius: 0px;
            }}
            #cfAuthTitle {{
                color: #FFFFFF;
                font-size: 20px;
                font-weight: 700;
            }}
            #cfAuthSubtitle {{
                color: rgba(255,255,255,0.85);
                font-size: 13px;
            }}
            #cfAuthForm {{
                background: {theme['bg_main']};
            }}
            #cfFieldLabel {{
                color: {theme['text_primary']};
                font-size: 11px;
                font-weight: 700;
            }}
            #cfAuthField {{
                background: {theme['bg_card']};
                color: {theme['text_primary']};
                border: 1.5px solid {theme['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 14px;
            }}
            #cfAuthField:focus {{
                border-color: {theme['accent']};
            }}
            #cfAuthSubmit {{
                background: {theme['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
                margin-top: 8px;
            }}
            #cfAuthSubmit:hover {{
                background: {theme['accent_hover']};
            }}
            #cfAuthError {{
                color: {theme['danger']};
                font-size: 12px;
                font-weight: 600;
                padding: 4px;
            }}
        """)
