@echo off
setlocal EnableExtensions
title Jtutor (Electron)
set "ROOT=%~dp0"
cd /d "%ROOT%"

where python >nul 2>&1 || (
  echo [ERROR] Python not found.
  pause
  exit /b 1
)
where node >nul 2>&1 || (
  echo [ERROR] Node.js not found.
  pause
  exit /b 1
)

set "PYTHONPATH=%ROOT%"
set "PYTHONIOENCODING=utf-8"

echo Starting API + Vite, then Electron...
start "Jtutor API" cmd /k "cd /d "%ROOT%" && set PYTHONPATH=%ROOT%&& set PYTHONIOENCODING=utf-8&& python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"
timeout /t 2 /nobreak >nul
start "Jtutor UI" cmd /k "cd /d "%ROOT%\apps\desktop" && npm run dev"
timeout /t 5 /nobreak >nul
cd /d "%ROOT%"
npx electron .
echo.
echo Close the API and UI windows when you are done.
pause
