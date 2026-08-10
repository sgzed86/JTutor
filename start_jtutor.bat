@echo off
REM Normal desktop launch (no console). Developers: use `npm run dev` instead.
cd /d "%~dp0"
wscript //nologo "%~dp0start_jtutor.vbs"
