# Installing Receipt Scanner

The receipt scanner requires Tesseract OCR to be installed on your system.

## Option 1: Quick Install (Recommended)

### Step 1: Download Tesseract
1. Download the Windows installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Get the latest version: `tesseract-ocr-w64-setup-5.x.x.exe`
3. Run the installer
4. **Important**: During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)

### Step 2: Install Python package
Open PowerShell in the backend folder and run:
```powershell
.\venv\Scripts\Activate.ps1
pip install pytesseract
```

### Step 3: Configure path
You may need to tell Python where Tesseract is installed.

## Option 2: Automatic Install Script

Run the setup script I created:
```powershell
.\setup_receipt_scanner.ps1
```

## Verify Installation

After installation, restart the backend server. You should see:
- ✓ Receipt OCR features enabled

Instead of:
- pytesseract not installed. Receipt OCR features will be disabled.

## Usage

1. Go to the Transactions page
2. Click "Upload Receipt" button (if available in UI)
3. Select a receipt image
4. The app will automatically extract:
   - Merchant name
   - Total amount
   - Create a transaction
   - Auto-categorize it

## Troubleshooting

If you get an error like "tesseract is not installed":
1. Make sure Tesseract is installed
2. Add it to your system PATH, or
3. Set the path in Python (see setup script)


