@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   LLM Research Harness - Starting UI
echo ========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo        Run build.bat first to install the project.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\harness-ui.exe" (
    echo ERROR: The `harness-ui` command was not found.
    echo        The project may not be installed. Run build.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Launching web UI at http://127.0.0.1:8080 ...
echo   (override: set HARNESS_UI_HOST / HARNESS_UI_PORT before running)
echo   (press Ctrl+C in this window to stop)
echo.
harness-ui

pause
endlocal
