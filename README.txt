============================================================
  CounterFlow v1.0.0
  Retail Management & Billing System
  by CN-6
============================================================

RUNNING FROM SOURCE
--------------------
1. Install Python 3.11 or newer
   https://python.org

2. Open a terminal in this folder and run:
   pip install -r requirements.txt

3. Launch the app:
   python main.py


BUILDING THE EXE (Windows)
---------------------------
1. Make sure Python and pip are installed and on PATH.

2. Double-click build.bat
   OR run from Command Prompt:
   build.bat

3. The finished EXE will be at:
   dist\CounterFlow\CounterFlow.exe

4. To distribute:
   Copy the entire dist\CounterFlow\ folder to a USB
   drive or share it with the shop owner.
   No Python needed on the target PC.


FOLDER STRUCTURE (Source)
--------------------------
CounterFlow\
  main.py                  Launch entry point
  requirements.txt         Python dependencies
  build.spec               PyInstaller config
  build.bat                One-click EXE builder
  counterflow.db           Created on first run
  assets\
    icons\
      counterflow_logo.png Sidebar & splash logo
      counterflow.ico      Window & taskbar icon
  app\
    config.py              App constants & paths
    theme.py               Colors & Qt stylesheet
    db\                    Database models & engine
    core\                  Business logic
    ui\                    All screens, dialogs, components
    utils\                 Validators, formatters, PDF


FIRST RUN
---------
The database (counterflow.db) is created automatically
on the first launch. No setup needed.


DATA BACKUP
-----------
To back up all shop data, copy:
  counterflow.db

That single file contains everything —
products, customers, invoices, stock history.


SYSTEM REQUIREMENTS
--------------------
  OS      : Windows 10 / 11 (64-bit)
  RAM     : 256 MB minimum
  Storage : 150 MB for the app + DB growth over time
  Display : 1280x720 minimum resolution


SUPPORT
-------
Built with Python 3.11, PyQt6, SQLAlchemy, ReportLab.
CounterFlow v1.0.0 — by CN-6
============================================================
