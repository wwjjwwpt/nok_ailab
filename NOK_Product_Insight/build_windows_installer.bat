@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================================
echo        NOK 产品经营分析 Windows 安装版构建工具
echo ============================================================
echo.

set "PYTHON_CMD="
py -3.12 --version >nul 2>&1 && set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD py -3.11 --version >nul 2>&1 && set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD (
    echo [错误] 未找到 Python 3.11 或 3.12。
    echo 请从 https://www.python.org/downloads/windows/ 安装 64 位 Python，
    echo 安装时勾选 "Add python.exe to PATH"。
    goto :failed
)

echo [1/7] 创建独立构建环境...
if not exist ".venv-windows\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv-windows
    if errorlevel 1 goto :failed
)

echo [2/7] 安装打包依赖...
".venv-windows\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv-windows\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto :failed

echo [3/7] 生成 Windows 应用图标...
".venv-windows\Scripts\python.exe" scripts\create_windows_icon.py
if errorlevel 1 goto :failed

echo [4/7] 生成 64 位单文件 EXE...
".venv-windows\Scripts\python.exe" -m PyInstaller --noconfirm --clean NOK_Product_Insight.spec
if errorlevel 1 goto :failed

if not exist "release" mkdir "release"
copy /Y "dist\NOK_Product_Insight.exe" "release\NOK_Product_Insight_Portable_v1.1.0_x64.exe" >nul

echo [5/7] 查找 Inno Setup 6...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"

if not defined ISCC (
    echo 未安装 Inno Setup 6。
    where winget >nul 2>&1
    if not errorlevel 1 (
        choice /M "是否现在通过 winget 安装 Inno Setup 6"
        if not errorlevel 2 (
            winget install --id JRSoftware.InnoSetup -e --source winget --accept-source-agreements --accept-package-agreements
        )
    )
)

if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo.
    echo [提示] 单文件 EXE 已生成，但安装向导尚未生成。
    echo 请安装 Inno Setup 6 后重新运行本脚本：
    echo https://jrsoftware.org/isdl.php
    echo.
    echo 可直接使用：
    echo %CD%\release\NOK_Product_Insight_Portable_v1.1.0_x64.exe
    goto :failed
)

echo [6/7] 生成 Windows 安装向导...
"%ISCC%" "installer\NOK_Product_Insight.iss"
if errorlevel 1 goto :failed

echo [7/7] 计算安装包校验值...
certutil -hashfile "release\NOK_Product_Insight_Setup_v1.1.0_x64.exe" SHA256

echo.
echo ============================================================
echo 构建成功
echo 安装版：
echo %CD%\release\NOK_Product_Insight_Setup_v1.1.0_x64.exe
echo.
echo 免安装版：
echo %CD%\release\NOK_Product_Insight_Portable_v1.1.0_x64.exe
echo ============================================================
start "" "release"
pause
exit /b 0

:failed
echo.
echo 构建未完成，请根据上方提示处理后重试。
pause
exit /b 1
