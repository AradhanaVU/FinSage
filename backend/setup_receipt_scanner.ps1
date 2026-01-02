# Setup script for Receipt Scanner on Windows

Write-Host "`n=== Receipt Scanner Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Tesseract is already installed
$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe"
)

$tesseractFound = $false
$tesseractPath = ""

foreach ($path in $tesseractPaths) {
    if (Test-Path $path) {
        $tesseractFound = $true
        $tesseractPath = $path
        Write-Host "[OK] Tesseract found at: $path" -ForegroundColor Green
        break
    }
}

if (-not $tesseractFound) {
    Write-Host "[NOT FOUND] Tesseract OCR is not installed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To install Tesseract OCR:" -ForegroundColor Cyan
    Write-Host "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "2. Look for: tesseract-ocr-w64-setup-5.x.x.exe"
    Write-Host "3. Run the installer (use default settings)"
    Write-Host "4. Run this script again after installation"
    Write-Host ""
    
    $response = Read-Host "Open download page in browser? (y/n)"
    if ($response -eq 'y') {
        Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
    }
    
    exit 1
}

# Install pytesseract
Write-Host ""
Write-Host "Installing pytesseract Python package..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1
pip install pytesseract

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] pytesseract installed successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to install pytesseract" -ForegroundColor Red
    exit 1
}

# Create a config file to set the Tesseract path
$configContent = @"
import pytesseract

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'$tesseractPath'
"@

$configPath = "app\tesseract_config.py"
$configContent | Out-File -FilePath $configPath -Encoding UTF8

Write-Host "[OK] Created config file at: $configPath" -ForegroundColor Green

# Update receipts.py to import the config
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart the backend server (Ctrl+C, then: python start_server.py)"
Write-Host "2. You should see: 'Receipt OCR features enabled'"
Write-Host "3. Use the receipt upload feature in the app"
Write-Host ""


