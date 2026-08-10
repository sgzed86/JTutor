@echo off
title Jtutor
cd /d "%~dp0"

where npm >nul 2>&1
if errorlevel 1 (
  echo npm was not found. Install Node.js LTS, then try again.
  pause
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    echo Python was not found. Install Python 3.11+, then try again.
    pause
    exit /b 1
  )
)

echo Starting Jtutor...
echo Close the Electron window when you are done — that stops the app.
echo.
call npm run dev
if errorlevel 1 (
  echo.
  echo Jtutor exited with an error.
  pause
)
