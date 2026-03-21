@echo off
:: ============================================================
:: CounterFlow v1.0.0 — Windows EXE Builder
:: ============================================================
:: Run this file to build CounterFlow.exe
:: Double-click  OR  run from Command Prompt:
::     build.bat
::
:: Requirements:
::     pip install -r requirements.txt
::
:: Output:
::     dist\CounterFlow\CounterFlow.exe
:: ============================================================

title CounterFlow — EXE Builder
color 0A
cls

echo.
echo  ============================================
echo   CounterFlow v1.0.0 - EXE Builder
echo   by CN-6
echo  ============================================
echo.

:: ── Check Python is installed ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Please install Python 3.14+ from https://python.org
    echo  and make sure it is added to PATH.
    pause
    exit /b 1
)

:: ── Check PyInstaller is installed ────────────────────────
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo  [INFO] PyInstaller not found. Installing...
    pip install pyinstaller==6.15.0
    if errorlevel 1 (
        echo  [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: ── Install all dependencies ───────────────────────────────
echo  [1/4] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [1/4] Done.
echo.

:: ── Clean previous build ──────────────────────────────────
echo  [2/4] Cleaning previous build...
if exist "build" (
    rmdir /s /q "build"
    echo        Removed: build\
)
if exist "dist\CounterFlow" (
    rmdir /s /q "dist\CounterFlow"
    echo        Removed: dist\CounterFlow\
)
echo  [2/4] Done.
echo.

:: ── Run PyInstaller ────────────────────────────────────────
echo  [3/4] Building CounterFlow.exe...
echo        This may take 1-3 minutes...
echo.
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check the output above for errors.
    pause
    exit /b 1
)
echo.
echo  [3/4] Done.
echo.

:: ── Verify output ─────────────────────────────────────────
echo  [4/4] Verifying output...
if not exist "dist\CounterFlow\CounterFlow.exe" (
    echo  [ERROR] CounterFlow.exe not found in dist\CounterFlow\
    echo  Something went wrong with the build.
    pause
    exit /b 1
)
echo  [4/4] Done.
echo.

:: ── Success ───────────────────────────────────────────────
echo  ============================================
echo   BUILD SUCCESSFUL
echo  ============================================
echo.
echo   EXE location:
echo   dist\CounterFlow\CounterFlow.exe
echo.
echo   To distribute:
echo   Copy the entire dist\CounterFlow\ folder
echo   to a USB drive or share with the shop owner.
echo.
echo   The folder is self-contained.
echo   No Python installation needed on the shop PC.
echo  ============================================
echo.

:: Open the output folder
explorer dist\CounterFlow

pause
