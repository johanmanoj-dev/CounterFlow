"""
CounterFlow v1.0.0 — Theme & Style System
==========================================
All colors, dimensions, and Qt stylesheets
for the CounterFlow UI. Based on approved design.

Light and Dark mode both defined here.
"""

# ── CounterFlow Light Mode Colors ─────────────────────────────
COUNTERFLOW_LIGHT = {
    "bg_app":           "#f5f7fa",
    "bg_surface":       "#ffffff",
    "bg_sidebar":       "#ffffff",
    "sidebar_border":   "#e8e8e8",
    "text_primary":     "#111827",
    "text_secondary":   "#6b7280",
    "text_sidebar":     "#374151",
    "text_sidebar_active": "#111827",
    "border":           "#e5e7eb",
    "hover":            "#f3f4f6",
    "active_bg":        "#f3f4f6",
    "active_indicator": "#111827",
    "input_bg":         "#ffffff",
    "input_border":     "#d1d5db",
    "input_focus":      "#111827",
    "table_header_bg":  "#f9fafb",
    "table_header_text":"#6b7280",
    "table_row_alt":    "#f9fafb",
    "table_hover":      "#f3f4f6",
    "table_border":     "#e5e7eb",
    "card_bg":          "#ffffff",
    "card_border":      "#e5e7eb",
    "scrollbar":        "#e5e7eb",
    "scrollbar_handle": "#d1d5db",
}

# ── CounterFlow Dark Mode Colors ──────────────────────────────
COUNTERFLOW_DARK = {
    "bg_app":           "#0f172a",
    "bg_surface":       "#1e293b",
    "bg_sidebar":       "#1e293b",
    "sidebar_border":   "#334155",
    "text_primary":     "#f1f5f9",
    "text_secondary":   "#94a3b8",
    "text_sidebar":     "#cbd5e1",
    "text_sidebar_active": "#f1f5f9",
    "border":           "#334155",
    "hover":            "#334155",
    "active_bg":        "#334155",
    "active_indicator": "#f1f5f9",
    "input_bg":         "#1e293b",
    "input_border":     "#475569",
    "input_focus":      "#94a3b8",
    "table_header_bg":  "#0f172a",
    "table_header_text":"#94a3b8",
    "table_row_alt":    "#1a2744",
    "table_hover":      "#334155",
    "table_border":     "#334155",
    "card_bg":          "#1e293b",
    "card_border":      "#334155",
    "scrollbar":        "#334155",
    "scrollbar_handle": "#475569",
}

# ── CounterFlow Accent Colors (same in both modes) ────────────
COUNTERFLOW_COLORS = {
    "primary":          "#111827",
    "primary_hover":    "#374151",
    "success":          "#16a34a",
    "success_light":    "#dcfce7",
    "success_text":     "#15803d",
    "danger":           "#dc2626",
    "danger_hover":     "#b91c1c",
    "danger_light":     "#fee2e2",
    "warning":          "#d97706",
    "warning_light":    "#fef3c7",
    "warning_text":     "#b45309",
    "upi_color":        "#2563eb",
    "upi_light":        "#dbeafe",
    "upi_text":         "#1d4ed8",
    "cash_color":       "#16a34a",
    "cash_light":       "#dcfce7",
    "cash_text":        "#15803d",
    "credit_color":     "#d97706",
    "credit_light":     "#fef3c7",
    "credit_text":      "#b45309",
    "stock_green":      "#16a34a",
    "stock_green_bg":   "#dcfce7",
    "stock_amber":      "#d97706",
    "stock_amber_bg":   "#fef3c7",
    "stock_red":        "#dc2626",
    "stock_red_bg":     "#fee2e2",
    "balance_zero":     "#16a34a",
    "balance_low":      "#d97706",
    "balance_high":     "#dc2626",
}

# ── CounterFlow Dimensions ─────────────────────────────────────
COUNTERFLOW_SIDEBAR_WIDTH       = 240
COUNTERFLOW_CONTENT_PADDING     = 32
COUNTERFLOW_CARD_RADIUS         = 12
COUNTERFLOW_INPUT_HEIGHT        = 40
COUNTERFLOW_BTN_HEIGHT          = 40
COUNTERFLOW_TABLE_ROW_HEIGHT    = 52
COUNTERFLOW_TABLE_HEADER_HEIGHT = 44
COUNTERFLOW_NAV_ITEM_HEIGHT     = 44
COUNTERFLOW_LOGO_SIZE           = 32

# ── Active theme tracker ───────────────────────────────────────
_counterflow_dark_mode = False


def counterflow_is_dark() -> bool:
    return _counterflow_dark_mode


def counterflow_set_dark(value: bool):
    global _counterflow_dark_mode
    _counterflow_dark_mode = value


def counterflow_theme() -> dict:
    """Returns current active theme colors merged with accents."""
    base = COUNTERFLOW_DARK if _counterflow_dark_mode else COUNTERFLOW_LIGHT
    return {**base, **COUNTERFLOW_COLORS}


def counterflow_build_stylesheet() -> str:
    """
    CounterFlow — Builds and returns the full Qt stylesheet
    based on the current theme (light or dark).
    """
    t = counterflow_theme()

    return f"""
    /* ── CounterFlow Global ── */
    QMainWindow, QWidget {{
        background-color: {t['bg_app']};
        color: {t['text_primary']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
        border: none;
        outline: none;
    }}

    /* ── CounterFlow ScrollBar ── */
    QScrollBar:vertical {{
        background: {t['scrollbar']};
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['scrollbar_handle']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ── CounterFlow Inputs ── */
    QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: {t['input_bg']};
        border: 1px solid {t['input_border']};
        border-radius: 8px;
        padding: 6px 12px;
        color: {t['text_primary']};
        font-size: 13px;
        min-height: {COUNTERFLOW_INPUT_HEIGHT}px;
    }}
    QLineEdit:focus, QDateEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1.5px solid {t['input_focus']};
    }}
    QLineEdit::placeholder {{
        color: {t['text_secondary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background: {t['bg_surface']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        selection-background-color: {t['hover']};
        color: {t['text_primary']};
    }}
    QDateEdit::up-button, QDateEdit::down-button {{
        width: 0px;
    }}

    /* ── CounterFlow Primary Button ── */
    QPushButton {{
        background: {t['primary']};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
        min-height: {COUNTERFLOW_BTN_HEIGHT}px;
    }}
    QPushButton:hover {{
        background: {t['primary_hover']};
    }}
    QPushButton:disabled {{
        background: {t['border']};
        color: {t['text_secondary']};
    }}

    /* ── CounterFlow Danger Button ── */
    QPushButton#counterflowDangerBtn {{
        background: {t['danger']};
    }}
    QPushButton#counterflowDangerBtn:hover {{
        background: {t['danger_hover']};
    }}

    /* ── CounterFlow Outline Button ── */
    QPushButton#counterflowOutlineBtn {{
        background: transparent;
        color: {t['text_primary']};
        border: 1px solid {t['border']};
    }}
    QPushButton#counterflowOutlineBtn:hover {{
        background: {t['hover']};
    }}

    /* ── CounterFlow Quick Filter Button ── */
    QPushButton#counterflowFilterBtn {{
        background: transparent;
        color: {t['text_secondary']};
        border: 1px solid {t['border']};
        border-radius: 20px;
        padding: 5px 16px;
        font-size: 12px;
        font-weight: 500;
        min-height: 32px;
    }}
    QPushButton#counterflowFilterBtn:hover {{
        background: {t['hover']};
        color: {t['text_primary']};
    }}
    QPushButton#counterflowFilterBtn:checked {{
        background: {t['primary']};
        color: #ffffff;
        border-color: {t['primary']};
    }}

    /* ── CounterFlow Table ── */
    QTableWidget {{
        background: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: 12px;
        gridline-color: {t['table_border']};
        selection-background-color: {t['hover']};
        selection-color: {t['text_primary']};
        alternate-background-color: {t['table_row_alt']};
    }}
    QTableWidget::item {{
        padding: 0px 16px;
        border: none;
        color: {t['text_primary']};
    }}
    QTableWidget::item:hover {{
        background: {t['table_hover']};
    }}
    QTableWidget::item:selected {{
        background: {t['hover']};
        color: {t['text_primary']};
    }}
    QHeaderView::section {{
        background: {t['table_header_bg']};
        color: {t['table_header_text']};
        font-size: 12px;
        font-weight: 600;
        padding: 0px 16px;
        height: {COUNTERFLOW_TABLE_HEADER_HEIGHT}px;
        border: none;
        border-bottom: 1px solid {t['table_border']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 12px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 12px;
    }}

    /* ── CounterFlow Dialog ── */
    QDialog {{
        background: {t['bg_surface']};
        border-radius: 12px;
    }}

    /* ── CounterFlow Label ── */
    QLabel {{
        background: transparent;
        color: {t['text_primary']};
    }}

    /* ── CounterFlow Frame/Card ── */
    QFrame#counterflowCard {{
        background: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: {COUNTERFLOW_CARD_RADIUS}px;
    }}
    """
