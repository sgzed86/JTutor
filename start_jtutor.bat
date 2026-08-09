@echo off
setlocal EnableExtensions
title Jtutor
set "ROOT=%~dp0"
cd /d "%ROOT%"

where python >nul 2>&1 || (
  echo [ERROR] Python not found. Install Python 3.11+ and try again.
  pause
  exit /b 1
)
where node >nul 2>&1 || (
  echo [ERROR] Node.js not found. Install Node LTS and try again.
  pause
  exit /b 1
)
if not exist "backend\app\main.py" (
  echo [ERROR] backend\app\main.py missing. Run this file from the Jtutor folder.
  pause
  exit /b 1
)

set "PYTHONPATH=%ROOT%"
set "PYTHONIOENCODING=utf-8"

echo.
echo  Jtutor — starting API and tutor UI
echo  -----------------------------------
echo  Before lessons: run Ollama and VOICEVOX on this PC.
echo  API:  http://127.0.0.1:8765
echo  UI:   http://127.0.0.1:5173
echo.

start "Jtutor API" cmd /k "cd /d "%ROOT%" && set PYTHONPATH=%ROOT%&& set PYTHONIOENCODING=utf-8&& python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"

timeout /t 2 /nobreak >nul

start "Jtutor UI" cmd /k "cd /d "%ROOT%\apps\desktop" && npm run dev"

timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173/"

echo  Opened the tutor in your browser.
echo  To stop: close the "Jtutor API" and "Jtutor UI" windows, or run stop_jtutor.bat
echo.
timeout /t 5 >nul
exit /b 0
