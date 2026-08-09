@echo off
setlocal EnableExtensions
title Jtutor
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo Virtual environment missing. Run INSTALL.bat first.
  pause
  exit /b 1
)

set "JTUTOR_ROOT=%ROOT%"
set "PYTHONPATH=%ROOT%"
set "PYTHONIOENCODING=utf-8"
set "PY=%ROOT%.venv\Scripts\python.exe"

echo.
echo  Jtutor starting...
echo  API + UI:  http://127.0.0.1:8765
echo  Keep this window open while you study.
echo  Prerequisites: Ollama + VOICEVOX running on this PC.
echo.

start "Jtutor" /min cmd /c "cd /d "%ROOT%" && set JTUTOR_ROOT=%ROOT%&& set PYTHONPATH=%ROOT%&& set PYTHONIOENCODING=utf-8&& "%PY%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8765/"

echo  Opened Jtutor in your browser.
echo  To stop: run STOP.bat or close the minimized Jtutor window.
echo.
timeout /t 4 >nul
exit /b 0
