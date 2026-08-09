@echo off
echo Stopping Jtutor (port 8765)...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8765 ^| findstr LISTENING') do (
  taskkill /PID %%P /F >nul 2>&1
)
echo Done.
timeout /t 2 >nul
