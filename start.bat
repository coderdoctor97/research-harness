@echo off
chcp 65001 >nul
echo ========================================
echo   LLM Research Harness - Starting UI
echo ========================================

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run build.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Launching web UI at http://127.0.0.1:8080 ...
harness-ui

pause
