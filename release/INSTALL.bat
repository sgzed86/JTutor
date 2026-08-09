@echo off
setlocal EnableExtensions
title Jtutor Install
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo  Jtutor — one-time setup
echo  ========================
echo.

where python >nul 2>&1 || (
  echo [ERROR] Python not found.
  echo Install Python 3.11+ from https://www.python.org/downloads/
  echo During setup, check "Add python.exe to PATH".
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" 2>nul || (
  echo [ERROR] Python 3.11+ required.
  pause
  exit /b 1
)

if not exist "%ROOT%backend\app\main.py" (
  echo [ERROR] Incomplete package — backend folder missing.
  pause
  exit /b 1
)

echo Creating virtual environment (.venv) ...
if not exist "%ROOT%.venv\Scripts\python.exe" (
  python -m venv "%ROOT%.venv"
  if errorlevel 1 (
    echo [ERROR] Could not create venv.
    pause
    exit /b 1
  )
)

echo Installing Python packages (first run can take several minutes — Whisper)...
"%ROOT%.venv\Scripts\python.exe" -m pip install --upgrade pip
"%ROOT%.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
  echo [ERROR] pip install failed.
  pause
  exit /b 1
)

if not exist "%ROOT%assets" mkdir "%ROOT%assets"
if not exist "%ROOT%assets\audio" mkdir "%ROOT%assets\audio"
if not exist "%ROOT%data" mkdir "%ROOT%data"

echo.
echo  Setup complete.
echo.
echo  NEXT STEPS
echo  ----------
echo  1. Put your Irodori PDFs and MP3s into the assets\ folder
echo     ^(see assets\README.txt^)
echo  2. Install and start Ollama  https://ollama.com
echo     then run:  ollama pull qwen2.5:7b
echo  3. Install and start VOICEVOX  https://voicevox.hiroshiba.jp
echo  4. Double-click START.bat
echo.
pause
exit /b 0
