@echo off
chcp 65001 >nul
echo ========================================
echo   LLM Research Harness - Build/Install
echo ========================================

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing project with dev dependencies...
pip install -e ".[dev]"

echo.
echo ========================================
echo   Build complete!
echo   Run start.bat to launch the app.
echo ========================================
pause
