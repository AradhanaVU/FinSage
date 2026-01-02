# Start backend server in a new PowerShell window so you can see the logs

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = $scriptPath

Write-Host "Starting backend server in new window..." -ForegroundColor Green
Write-Host ""

# Start a new PowerShell window with the backend
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendPath'; .\venv\Scripts\Activate.ps1; Write-Host 'Backend Server Console - You can see all logs here!' -ForegroundColor Cyan; Write-Host ''; python start_server.py"
) -WindowStyle Normal

Write-Host "Backend server window should be open now!" -ForegroundColor Green
Write-Host "Look for a new PowerShell window with the server logs." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this script (the server will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


