@echo off
setlocal
cd /d "%~dp0"

set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo [1/3] Creating virtual environment...
%PY% -m venv .venv || (
    echo Python was not found. Install Python 3.10+ from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during setup.
    pause & exit /b 1
)
set "VPY=.venv\Scripts\python.exe"

echo [2/3] Installing dependencies...
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -e . || (pause & exit /b 1)

echo [3/3] Downloading Chromium for Playwright...
"%VPY%" -m playwright install chromium || (
    echo.
    echo WARNING: Chromium could not be downloaded. That is fine if Google Chrome or
    echo Microsoft Edge is installed - the tool will use it automatically.
)

echo.
echo Setup complete. Double-click run.bat to download slides.
pause
