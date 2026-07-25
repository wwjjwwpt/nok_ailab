@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Checking Python...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 was not found.
  echo Install Python 3.11 from https://www.python.org/downloads/windows/
  echo During installation, enable "Add python.exe to PATH".
  pause
  exit /b 1
)

echo [2/4] Creating build environment...
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
)
call ".venv\Scripts\activate.bat"

echo [3/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo [4/4] Building Windows EXE...
python -m PyInstaller --noconfirm --clean NOK_Product_Insight.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Build complete:
echo %CD%\dist\NOK_Product_Insight.exe
pause

