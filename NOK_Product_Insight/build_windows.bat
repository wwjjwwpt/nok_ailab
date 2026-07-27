@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PYTHON_CMD="
py -3.12 --version >nul 2>&1 && set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD py -3.11 --version >nul 2>&1 && set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD (
    echo Python 3.11 or 3.12 was not found.
    echo Download it from https://www.python.org/downloads/windows/
    echo During installation, enable "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [2/4] Creating build environment...
if not exist ".venv-windows\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv-windows
)

echo [3/4] Installing dependencies...
".venv-windows\Scripts\python.exe" -m pip install --upgrade pip
".venv-windows\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo [4/4] Building Windows EXE...
".venv-windows\Scripts\python.exe" scripts\create_windows_icon.py
".venv-windows\Scripts\python.exe" -m PyInstaller --noconfirm --clean NOK_Product_Insight.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Build complete:
echo %CD%\dist\NOK_Product_Insight.exe
pause
