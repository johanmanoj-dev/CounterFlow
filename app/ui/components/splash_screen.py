"""
CounterFlow v1.0.0 — Splash Screen
=====================================
Loading screen shown at app startup while the
database initializes. Displays logo, app name,
and "by CN-6" branding at the bottom center.
Fades out once the main window is ready.
"""

from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
from app.config import (
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_ICONS_DIR,
)
import os


class CounterFlowSplashScreen(QSplashScreen):
    """
    CounterFlow — Startup Splash Screen.
    Shown while DB initializes.
    Displays logo + app name on same line, center.
    "by CN-6" at bottom center in thin modern style.
    """

    COUNTERFLOW_SPLASH_WIDTH  = 500
    COUNTERFLOW_SPLASH_HEIGHT = 300

    def __init__(self):
        counterflow_pixmap = self._counterflow_build_splash_pixmap()
        super().__init__(counterflow_pixmap)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def _counterflow_build_splash_pixmap(self) -> QPixmap:
        """
        CounterFlow — Draws the splash screen content onto a pixmap.
        Returns the completed pixmap for QSplashScreen.
        """
        w = self.COUNTERFLOW_SPLASH_WIDTH
        h = self.COUNTERFLOW_SPLASH_HEIGHT

        counterflow_pixmap = QPixmap(w, h)
        counterflow_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(counterflow_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # ── Background ─────────────────────────────────────────
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#e5e7eb"), 1))
        painter.drawRoundedRect(0, 0, w, h, 16, 16)

        # ── Logo ───────────────────────────────────────────────
        counterflow_logo_path = os.path.join(
            COUNTERFLOW_ICONS_DIR,
            "counterflow_logo.png"
        )

        counterflow_logo_size = 90

        # Define styles first so we can calculate text width
        counterflow_name_font = QFont("Segoe UI", 32)
        counterflow_name_font.setWeight(QFont.Weight.Bold)
        painter.setFont(counterflow_name_font)
        
        # Calculate total width of logo + spacing + text
        spacing = 10
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(COUNTERFLOW_APP_NAME)
        total_width = counterflow_logo_size + spacing + text_width
        
        # Calculate starting X for the entire block to be centered
        start_x = (w - total_width) // 2

        counterflow_logo_x = start_x
        counterflow_logo_y = (h // 2) - 45

        if os.path.exists(counterflow_logo_path):
            counterflow_logo = QPixmap(counterflow_logo_path).scaled(
                counterflow_logo_size,
                counterflow_logo_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(
                counterflow_logo_x,
                counterflow_logo_y,
                counterflow_logo
            )
        else:
            # Fallback circle if logo not found
            painter.setBrush(QBrush(QColor("#111827")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                counterflow_logo_x,
                counterflow_logo_y,
                counterflow_logo_size,
                counterflow_logo_size,
            )

        # ── App Name (right of logo, same line) ────────────────
        painter.setPen(QColor("#111827"))

        counterflow_name_x = counterflow_logo_x + counterflow_logo_size + spacing
        counterflow_name_y = counterflow_logo_y + (counterflow_logo_size // 2) + 15

        painter.drawText(
            counterflow_name_x,
            counterflow_name_y,
            COUNTERFLOW_APP_NAME
        )

        # ── Divider line ───────────────────────────────────────
        painter.setPen(QPen(QColor("#e5e7eb"), 1))
        painter.drawLine(40, h - 56, w - 40, h - 56)

        # ── "by CN-6" bottom center ────────────────────────────
        counterflow_by_font = QFont("Segoe UI", 15)
        counterflow_by_font.setWeight(QFont.Weight.ExtraBold)
        counterflow_by_font.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            1.5
        )
        painter.setFont(counterflow_by_font)
        painter.setPen(QColor("#374151"))

        counterflow_by_text = "by  CN-6"
        counterflow_fm      = painter.fontMetrics()
        counterflow_text_w  = counterflow_fm.horizontalAdvance(counterflow_by_text)
        counterflow_by_x    = (w - counterflow_text_w) // 2
        counterflow_by_y    = h - 24

        painter.drawText(counterflow_by_x, counterflow_by_y, counterflow_by_text)

        painter.end()
        return counterflow_pixmap

    def counterflow_finish(self, main_window):
        """
        CounterFlow — Fade out splash and show main window.
        Called once all initialization is complete.
        """
        self.finish(main_window)
