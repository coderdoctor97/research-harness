@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   LLM Research Harness - Build / Install
echo ========================================
echo.

REM ---- locate a working Python (prefer `python`, fall back to `py -3`) ----
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python was not found on PATH.
        echo        Install Python 3.10+ and make sure `python` is on PATH.
        pause
        exit /b 1
    )
    set "PY=py -3"
)
echo Using Python: %PY%
echo.

REM ---- create the virtual environment if missing ----
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade failed - continuing with the existing pip.
)

echo Installing the project with dev dependencies...
pip install -e ".[dev]"
if errorlevel 1 (
    echo.
    echo ERROR: Installation failed. See the messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo   Run start.bat to launch the web UI.
echo ========================================
pause
endlocal
