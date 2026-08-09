@echo off
set "ROOT=%~dp0.."
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%"
set "PYTHONIOENCODING=utf-8"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
