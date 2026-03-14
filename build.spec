# -*- mode: python ; coding: utf-8 -*-
"""
CounterFlow v1.0.0 — PyInstaller Build Specification
======================================================
Packages the entire CounterFlow application into a
single folder EXE for Windows distribution.

Output structure after build:
    dist/
    └── CounterFlow/
        ├── CounterFlow.exe      ← double-click to launch
        ├── counterflow.db       ← created on first run
        └── _internal/           ← PyInstaller internals

Usage:
    pyinstaller build.spec

Or use build.bat for a full clean build with one click.
"""

import os

# ── CounterFlow Paths ──────────────────────────────────────────
COUNTERFLOW_ROOT   = os.path.dirname(os.path.abspath(SPEC))
COUNTERFLOW_ASSETS = os.path.join(COUNTERFLOW_ROOT, 'assets')
COUNTERFLOW_ICONS  = os.path.join(COUNTERFLOW_ASSETS, 'icons')
COUNTERFLOW_FONTS  = os.path.join(COUNTERFLOW_ASSETS, 'fonts')

# ── Analysis ───────────────────────────────────────────────────
counterflow_analysis = Analysis(
    # Entry point
    scripts=[os.path.join(COUNTERFLOW_ROOT, 'main.py')],

    # Search paths for imports
    pathex=[COUNTERFLOW_ROOT],

    # Binary dependencies (none needed — PyQt6 handles its own)
    binaries=[],

    # Data files to bundle into the EXE
    datas=[
        # Include entire assets folder
        (COUNTERFLOW_ASSETS, 'assets'),
    ],

    # Hidden imports PyInstaller may miss
    hiddenimports=[
        # SQLAlchemy dialects
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'sqlalchemy.event',

        # ReportLab internals
        'reportlab.graphics',
        'reportlab.graphics.shapes',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.lib.styles',
        'reportlab.lib.enums',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase._fontdata',
        'reportlab.pdfbase.pdfmetrics',

        # PyQt6 modules used across CounterFlow
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',

        # CounterFlow app modules
        'app',
        'app.config',
        'app.theme',
        'app.db',
        'app.db.models',
        'app.db.database',
        'app.core',
        'app.core.billing',
        'app.core.inventory_manager',
        'app.core.customer_manager',
        'app.core.credit_manager',
        'app.core.report_generator',
        'app.ui',
        'app.ui.main_window',
        'app.ui.components',
        'app.ui.components.sidebar',
        'app.ui.components.stat_card',
        'app.ui.components.splash_screen',
        'app.ui.screens',
        'app.ui.screens.dashboard',
        'app.ui.screens.pos_billing',
        'app.ui.screens.inventory',
        'app.ui.screens.customers',
        'app.ui.screens.sales_history',
        'app.ui.screens.financial_overview',
        'app.ui.screens.database_records',
        'app.ui.dialogs',
        'app.ui.dialogs.add_product',
        'app.ui.dialogs.customer_lookup',
        'app.ui.dialogs.payment_dialog',
        'app.ui.dialogs.credit_warning',
        'app.utils',
        'app.utils.validators',
        'app.utils.formatters',
        'app.utils.barcode_handler',
        'app.utils.pdf_invoice',
    ],

    # Modules to explicitly exclude (reduces EXE size)


    # PyInstaller hooks
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

# ── PYZ Archive ────────────────────────────────────────────────
counterflow_pyz = PYZ(counterflow_analysis.pure)

# ── EXE ───────────────────────────────────────────────────────
counterflow_exe = EXE(
    counterflow_pyz,
    counterflow_analysis.scripts,
    [],

    # Do NOT embed — use folder mode (faster startup)
    exclude_binaries=True,

    # EXE metadata
    name='CounterFlow',
    icon=os.path.join(COUNTERFLOW_ICONS, 'counterflow.ico'),
    debug=False,

    # No console window — pure GUI app
    console=False,
    disable_windowed_traceback=False,

    # Windows version info
    version=None,

    # UAC: don't request admin elevation
    uac_admin=False,
    uac_uiaccess=False,

    # Strip debug symbols → smaller binary
    strip=False,
    upx=False,

    bootloader_ignore_signals=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ── COLLECT — Final folder bundle ─────────────────────────────
counterflow_collect = COLLECT(
    counterflow_exe,
    counterflow_analysis.binaries,
    counterflow_analysis.zipfiles,
    counterflow_analysis.datas,

    # Output folder name → dist/CounterFlow/
    name='CounterFlow',

    strip=False,
    upx=False,
    upx_exclude=[],
)
