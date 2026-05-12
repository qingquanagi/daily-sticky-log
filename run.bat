@echo off
cd /d "%~dp0"
python sticky_log.py
if errorlevel 1 (
  echo.
  echo Startup failed. Please send the error message above.
  pause
)
