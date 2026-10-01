@echo off
REM ─────────────────────────────────────────────────
REM  setup.bat — One-click local dev setup (Windows)
REM  Run this from the project root
REM ─────────────────────────────────────────────────

echo.
echo ====================================================
echo  Alzheimer Predictor — Local Development Setup
echo ====================================================
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Create virtual environment
IF NOT EXIST ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)
echo [OK] Virtual environment ready

REM Activate venv
call .venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt

REM Copy .env if not exists
IF NOT EXIST ".env" (
    echo [INFO] Creating .env from template...
    copy .env.template .env
    echo [WARN] Please edit .env with your settings!
)

REM Run migrations
echo [INFO] Running migrations...
set DJANGO_SETTINGS_MODULE=alz_predictor.settings.dev
python manage.py migrate

REM Collect static
echo [INFO] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ====================================================
echo  Setup complete!
echo  Run: .venv\Scripts\activate && python manage.py runserver
echo  API Docs: http://localhost:8000/api/docs/
echo  Admin:    http://localhost:8000/admin/
echo ====================================================
pause
