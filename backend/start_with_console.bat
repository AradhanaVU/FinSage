@echo off
REM Start backend server in a new console window so you can see the logs

cd /d "%~dp0"
echo Starting backend server in new window...
echo.
echo You should see a new window open with the server logs.
echo.

start "AI Finance Backend Server" cmd /k "venv\Scripts\activate.bat && python start_server.py"

timeout /t 2 /nobreak >nul
echo.
echo Backend server window should be open now!
echo Look for a window titled "AI Finance Backend Server"
echo.
pause


