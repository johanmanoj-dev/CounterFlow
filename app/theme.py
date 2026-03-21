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
    "sidebar_border":   "#d9d9d9",
    "text_primary":     "#111827",
    "text_secondary":   "#6b7280",
    "text_sidebar":     "#374151",
    "text_sidebar_active": "#111827",
    "border":           "#d5d7db",
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
    "card_border":      "#d5d7db",
    "scrollbar":        "#e5e7eb",
    "scrollbar_handle": "#d1d5db",
    "total_card_bg":    "#111827",
    "total_card_text":  "#ffffff",
}

# ── CounterFlow Dark Mode Colors ──────────────────────────────
COUNTERFLOW_DARK = {
    "bg_app":           "#000000",
    "bg_surface":       "#121212",
    "bg_sidebar":       "#121212",
    "sidebar_border":   "#2b2b2b",
    "text_primary":     "#f5f5f5",
    "text_secondary":   "#a3a3a3",
    "text_sidebar":     "#d4d4d4",
    "text_sidebar_active": "#ffffff",
    "border":           "#3a3a3a",
    "hover":            "#2b2b2b",
    "active_bg":        "#2b2b2b",
    "active_indicator": "#ffffff",
    "input_bg":         "#121212",
    "input_border":     "#3a3a3a",
    "input_focus":      "#a3a3a3",
    "table_header_bg":  "#000000",
    "table_header_text":"#a3a3a3",
    "table_row_alt":    "#1c1c1c",
    "table_hover":      "#2b2b2b",
    "table_border":     "#2b2b2b",
    "card_bg":          "#121212",
    "card_border":      "#3a3a3a",
    "scrollbar":        "#2b2b2b",
    "scrollbar_handle": "#4d4d4d",
    "total_card_bg":    "#e5e5e5",
    "total_card_text":  "#000000",
    # Dark-mode-aware accent overrides (override COUNTERFLOW_COLORS)
    "success_light":    "#064e3b",
    "danger_light":     "#7f1d1d",
    "warning_light":    "#78350f",
    "upi_light":        "#1e3a5f",
    "cash_light":       "#064e3b",
    "credit_light":     "#78350f",
    "stock_green_bg":   "#064e3b",
    "stock_amber_bg":   "#78350f",
    "stock_red_bg":     "#7f1d1d",
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
COUNTERFLOW_SIDEBAR_WIDTH       = 220
COUNTERFLOW_CONTENT_PADDING     = 32
COUNTERFLOW_CARD_RADIUS         = 12
COUNTERFLOW_INPUT_HEIGHT        = 42
COUNTERFLOW_BTN_HEIGHT          = 42
COUNTERFLOW_TABLE_ROW_HEIGHT    = 48
COUNTERFLOW_TABLE_HEADER_HEIGHT = 44
COUNTERFLOW_NAV_ITEM_HEIGHT     = 44
COUNTERFLOW_LOGO_SIZE           = 32

# ── Active theme tracker ───────────────────────────────────────
_counterflow_dark_mode = True


def counterflow_is_dark() -> bool:
    return _counterflow_dark_mode


def counterflow_set_dark(value: bool):
    global _counterflow_dark_mode
    _counterflow_dark_mode = value


def counterflow_theme() -> dict:
    """Returns current active theme colors merged with accents.

    Merge order: shared accents first, then mode-specific palette on top.
    This lets COUNTERFLOW_DARK override accent keys like success_light,
    stock_green_bg, etc. with dark-friendly variants.

    Convenience aliases injected for auth/log UI files:
    accent, accent_hover, bg_main, bg_card.
    """
    base   = COUNTERFLOW_DARK if _counterflow_dark_mode else COUNTERFLOW_LIGHT
    merged = {**COUNTERFLOW_COLORS, **base}
    # ── CounterFlow auth/log screen aliases ───────────────────
    merged["accent"]       = merged["primary"]
    merged["accent_hover"] = merged["primary_hover"]
    merged["bg_main"]      = merged["bg_app"]
    merged["bg_card"]      = merged["bg_surface"]
    return merged


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
        font-size: 14px;
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
        font-size: 14px;
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
        font-size: 14px;
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
        font-size: 15px;
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
        background: transparent;
        border: none;
        gridline-color: {t['table_border']};
        selection-background-color: {t['hover']};
        selection-color: {t['text_primary']};
        alternate-background-color: {t['table_row_alt']};
    }}
    QTableWidget::item {{
        padding: 0px 8px;
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
        font-size: 14px;
        font-weight: 700;
        padding: 0px 12px;
        height: {COUNTERFLOW_TABLE_HEADER_HEIGHT}px;
        border: none;
        border-right: 1px solid {t['table_border']};
        border-bottom: 2px solid {t['table_border']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QHeaderView::section:last {{
        border-right: none;
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
