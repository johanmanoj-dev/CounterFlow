"""
CounterFlow v1.0.0 — Login Dialog
===================================
Shown on every launch after the initial Admin setup.
Presents two options: Admin Login and Staff Login.
Authenticates credentials and sets the global auth session.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QStackedWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from app.core.auth import (
    CounterFlowAuthManager,
    CounterFlowAuthError,
    counterflow_auth_session,
)
from app import theme as t
from app.config import COUNTERFLOW_ICONS_DIR
import os


class CounterFlowLoginDialog(QDialog):
    """
    CounterFlow — Login screen dialog.

    Layout:
        Left panel  — Branding / logo / welcome message
        Right panel — Role selection then credential form

    Flow:
        1. User selects "Admin Login" or "Staff Login"
        2. Enters username + password
        3. On success: dialog closes with Accepted,
           counterflow_auth_session is populated
        4. On failure: inline error message, fields can be retried
    """

    counterflow_login_successful = pyqtSignal(str)   # emits role string

    def __init__(self, auth_manager: CounterFlowAuthManager, parent=None):
        super().__init__(parent)
        self.counterflow_auth_manager = auth_manager
        self._counterflow_selected_role: str | None = None

        self.setWindowTitle("CounterFlow — Login")
        self.setMinimumWidth(860)
        self.setMinimumHeight(520)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._counterflow_build()
        self._counterflow_apply_style()

    # ── Build UI ───────────────────────────────────────────────

    def _counterflow_build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left Branding Panel ────────────────────────────────
        self._counterflow_brand_panel = self._counterflow_build_brand_panel()
        root.addWidget(self._counterflow_brand_panel, stretch=2)

        # ── Right Form Panel ───────────────────────────────────
        right_panel = QFrame()
        right_panel.setObjectName("cfLoginRight")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(48, 48, 48, 48)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Stack: page 0 = role selection, page 1 = credential form
        self._counterflow_stack = QStackedWidget()
        self._counterflow_role_page  = self._counterflow_build_role_page()
        self._counterflow_form_page  = self._counterflow_build_form_page()
        self._counterflow_stack.addWidget(self._counterflow_role_page)
        self._counterflow_stack.addWidget(self._counterflow_form_page)

        right_layout.addWidget(self._counterflow_stack)
        root.addWidget(right_panel, stretch=3)

    def _counterflow_build_brand_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("cfLoginBrand")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(COUNTERFLOW_ICONS_DIR, "counterflow_logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pix)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_name = QLabel("CounterFlow")
        app_name.setObjectName("cfBrandName")
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        app_name.setFont(font)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tagline = QLabel("Retail Management & Billing")
        tagline.setObjectName("cfBrandTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(logo_label)
        layout.addWidget(app_name)
        layout.addWidget(tagline)
        layout.addStretch()

        powered = QLabel("by CN-6")
        powered.setObjectName("cfBrandPowered")
        powered.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(powered)

        return panel

    def _counterflow_build_role_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        heading = QLabel("Select Login Type")
        heading.setObjectName("cfLoginHeading")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        heading.setFont(font)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Who is logging in today?")
        sub.setObjectName("cfLoginSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(heading)
        layout.addWidget(sub)
        layout.addSpacing(16)

        # Role buttons
        for role_key, role_label, role_icon, role_desc in [
            ("ADMIN", "Admin Login",  "      ", "Full access — shop owner / manager"),
            ("STAFF", "Staff Login",  "      ", "Operational access — billing & customers"),
        ]:
            btn = self._counterflow_build_role_btn(role_key, role_label, role_icon, role_desc)
            layout.addWidget(btn)

        layout.addStretch()
        return page

    def _counterflow_build_role_btn(
        self, role_key: str, label: str, icon: str, desc: str
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName(f"cfRoleCard_{role_key}")
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame.setFixedHeight(90)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 14, 20, 14)
        frame_layout.setSpacing(4)

        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("cfRoleIcon")
        font = QFont()
        font.setPointSize(20)
        icon_lbl.setFont(font)

        lbl = QLabel(label)
        lbl.setObjectName("cfRoleLabel")
        font2 = QFont()
        font2.setPointSize(14)
        font2.setBold(True)
        lbl.setFont(font2)

        top_row.addWidget(icon_lbl)
        top_row.addWidget(lbl)
        top_row.addStretch()

        desc_lbl = QLabel(desc)
        desc_lbl.setObjectName("cfRoleDesc")

        frame_layout.addLayout(top_row)
        frame_layout.addWidget(desc_lbl)

        # Click via mousePressEvent on the frame
        frame.mousePressEvent = lambda event, r=role_key: self._counterflow_select_role(r)
        return frame

    def _counterflow_build_form_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Back button
        back_row = QHBoxLayout()
        self.counterflow_back_btn = QPushButton("← Back")
        self.counterflow_back_btn.setObjectName("cfBackBtn")
        self.counterflow_back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.counterflow_back_btn.setAutoDefault(False)
        self.counterflow_back_btn.clicked.connect(self._counterflow_go_back)
        back_row.addWidget(self.counterflow_back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)
        layout.addSpacing(20)

        # Heading (updated dynamically per role)
        self.counterflow_form_heading = QLabel("Admin Login")
        self.counterflow_form_heading.setObjectName("cfLoginHeading")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.counterflow_form_heading.setFont(font)
        layout.addWidget(self.counterflow_form_heading)
        layout.addSpacing(24)

        # Username
        uname_lbl = QLabel("Username")
        uname_lbl.setObjectName("cfFieldLabel")
        font2 = QFont()
        font2.setBold(True)
        font2.setPointSize(11)
        uname_lbl.setFont(font2)
        layout.addWidget(uname_lbl)
        layout.addSpacing(4)

        self.counterflow_username_input = QLineEdit()
        self.counterflow_username_input.setPlaceholderText("Enter your username")
        self.counterflow_username_input.setObjectName("cfAuthField")
        self.counterflow_username_input.setFixedHeight(44)
        layout.addWidget(self.counterflow_username_input)
        layout.addSpacing(14)

        # Password
        pw_lbl = QLabel("Password")
        pw_lbl.setObjectName("cfFieldLabel")
        pw_lbl.setFont(font2)
        layout.addWidget(pw_lbl)
        layout.addSpacing(4)

        self.counterflow_password_input = QLineEdit()
        self.counterflow_password_input.setPlaceholderText("Enter your password")
        self.counterflow_password_input.setObjectName("cfAuthField")
        self.counterflow_password_input.setFixedHeight(44)
        self.counterflow_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.counterflow_password_input)
        layout.addSpacing(8)

        # Error label
        self.counterflow_error_label = QLabel("")
        self.counterflow_error_label.setObjectName("cfAuthError")
        self.counterflow_error_label.setWordWrap(True)
        self.counterflow_error_label.setVisible(False)
        layout.addWidget(self.counterflow_error_label)
        layout.addSpacing(20)

        # Login button
        self.counterflow_login_btn = QPushButton("Login")
        self.counterflow_login_btn.setObjectName("cfAuthSubmit")
        self.counterflow_login_btn.setFixedHeight(48)
        self.counterflow_login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.counterflow_login_btn.setDefault(True)
        self.counterflow_login_btn.setAutoDefault(True)
        self.counterflow_login_btn.clicked.connect(self._counterflow_on_login)
        layout.addWidget(self.counterflow_login_btn)
        layout.addStretch()

        self.counterflow_username_input.returnPressed.connect(self.counterflow_password_input.setFocus)
        self.counterflow_password_input.returnPressed.connect(self._counterflow_on_login)
        return page

    # ── Role Selection ─────────────────────────────────────────

    def _counterflow_select_role(self, role: str):
        self._counterflow_selected_role = role
        self.counterflow_form_heading.setText(
            "Admin Login" if role == "ADMIN" else "Staff Login"
        )
        self.counterflow_username_input.clear()
        self.counterflow_password_input.clear()
        self.counterflow_error_label.setVisible(False)
        self._counterflow_stack.setCurrentIndex(1)
        self.counterflow_username_input.setFocus()

    def _counterflow_go_back(self):
        self._counterflow_selected_role = None
        self.counterflow_error_label.setVisible(False)
        self._counterflow_stack.setCurrentIndex(0)

    # ── Login Logic ────────────────────────────────────────────

    def _counterflow_on_login(self):
        username = self.counterflow_username_input.text().strip()
        password = self.counterflow_password_input.text()

        if not username or not password:
            self._counterflow_show_error("Please enter both username and password.")
            return

        try:
            self.counterflow_auth_manager.counterflow_authenticate(
                username=username,
                password=password,
                expected_role=self._counterflow_selected_role,
            )
            self.counterflow_login_successful.emit(self._counterflow_selected_role)
            self.accept()

        except CounterFlowAuthError as e:
            self._counterflow_show_error(str(e))
            self.counterflow_password_input.clear()
            self.counterflow_password_input.setFocus()

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
            #cfLoginBrand {{
                background: {theme['accent']};
                border-radius: 0px;
            }}
            #cfBrandName {{
                color: #FFFFFF;
                font-weight: 700;
            }}
            #cfBrandTagline {{
                color: rgba(255,255,255,0.80);
                font-size: 14px;
            }}
            #cfBrandPowered {{
                color: rgba(255,255,255,0.55);
                font-size: 12px;
            }}
            #cfLoginRight {{
                background: {theme['bg_main']};
            }}
            #cfLoginHeading {{
                color: {theme['text_primary']};
                font-weight: 700;
            }}
            #cfLoginSub {{
                color: {theme['text_secondary']};
                font-size: 14px;
            }}
            QFrame[objectName^="cfRoleCard_"] {{
                background: {theme['bg_card']};
                border: 1.5px solid {theme['border']};
                border-radius: 12px;
                margin-bottom: 4px;
            }}
            QFrame[objectName^="cfRoleCard_"]:hover {{
                border-color: {theme['accent']};
                background: {theme['hover']};
            }}
            #cfRoleIcon {{
                font-size: 20px;
            }}
            #cfRoleLabel {{
                color: {theme['text_primary']};
                font-weight: 700;
                font-size: 14px;
            }}
            #cfRoleDesc {{
                color: {theme['text_secondary']};
                font-size: 12px;
                padding-left: 32px;
            }}
            #cfFieldLabel {{
                color: {theme['text_primary']};
                font-weight: 700;
                font-size: 11px;
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
            }}
            #cfAuthSubmit:hover {{
                background: {theme['accent_hover']};
            }}
            #cfBackBtn {{
                background: transparent;
                color: {theme['text_secondary']};
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 0;
            }}
            #cfBackBtn:hover {{
                color: {theme['text_primary']};
            }}
            #cfAuthError {{
                color: {theme['danger']};
                font-size: 12px;
                font-weight: 600;
                padding: 4px 0;
            }}
        """)
