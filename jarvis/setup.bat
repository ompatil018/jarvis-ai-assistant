@echo off
title Jarvis AI Assistant — Setup
color 0B

echo.
echo  ================================================================
echo   J.A.R.V.I.S  —  AI Desktop Assistant Setup
echo  ================================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Download from: https://www.python.org/downloads/
    pause & exit /b 1
)
echo  [OK] Python found.

:: Create virtual environment
if not exist ".venv" (
    echo  [*] Creating virtual environment...
    python -m venv .venv
)
echo  [OK] Virtual environment ready.

:: Activate venv
call .venv\Scripts\activate.bat

:: Upgrade pip
echo  [*] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install dependencies
echo  [*] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo  [WARN] Some packages may have failed. Trying without quiet mode...
    pip install -r requirements.txt
)

echo  [OK] Dependencies installed.

:: Copy .env if not exists
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo  [OK] Created .env from template.
        echo.
        echo  *** IMPORTANT: Open .env and add your API key! ***
        echo      OPENAI_API_KEY=sk-...   (or GROQ_API_KEY for free)
    )
)

:: Create data/logs dirs
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo  ================================================================
echo   Setup complete!
echo  ================================================================
echo.
echo  Next steps:
echo    1. Edit .env and add your OPENAI_API_KEY (or GROQ_API_KEY)
echo    2. Run:  python main.py
echo.
echo  Optional (for better wake-word):
echo    Set PICOVOICE_API_KEY in .env (free at console.picovoice.ai)
echo.
pause
