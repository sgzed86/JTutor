@echo off
setlocal EnableExtensions
title Stop Jtutor dev servers
echo Stopping processes listening on ports 8765 (API) and 5173 (Vite)...
echo.

call :kill_port 8765
call :kill_port 5173

echo.
echo Done. You can run start_jtutor.bat again.
timeout /t 3 >nul
exit /b 0

:kill_port
set "PORT=%~1"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do (
  echo Port %PORT%: stopping PID %%a
  taskkill /PID %%a /F >nul 2>&1
  if errorlevel 1 echo   Could not stop PID %%a — try closing the window manually or run as admin.
)
exit /b 0
