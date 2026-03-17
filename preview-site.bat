@echo off
setlocal

cd /d "%~dp0"

set "ADMIN_PASSWORD=change-me-now"
set "PYTHON_EXE=C:\Users\anant\anaconda3\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Python not found at %PYTHON_EXE%
  echo Edit preview-site.bat and update the PYTHON_EXE path.
  pause
  exit /b 1
)

start "Italia CAF Site Server" cmd /k "cd /d %~dp0 && set ADMIN_PASSWORD=change-me-now && \"%PYTHON_EXE%\" run_local.py"
timeout /t 5 /nobreak >nul
start "" http://127.0.0.1:8001/

echo Server window opened.
echo Browser opened at http://127.0.0.1:8001/
echo If the site is not ready yet, refresh the browser after a few seconds.
exit /b 0
