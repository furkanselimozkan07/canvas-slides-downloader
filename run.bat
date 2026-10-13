@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
    echo Run install.bat first.
    pause & exit /b 1
)
set "PYTHONIOENCODING=utf-8"

rem With arguments: pass everything straight to the CLI.
if not "%~1"=="" (
    "%VPY%" -m slides_downloader %*
    exit /b
)

rem Without arguments: ask for the links and save to the Downloads folder.
set "OUT=%USERPROFILE%\Downloads"
echo Paste one or more links separated by spaces (Canvas page or Google Slides).
set /p "LINKS=Links: "
if not defined LINKS (
    echo No link given.
    pause & exit /b 1
)
"%VPY%" -m slides_downloader -o "%OUT%" !LINKS!
echo.
echo Files are in %OUT%
pause
