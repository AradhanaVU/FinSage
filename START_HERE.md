# Quick Start Guide

## Current Status
- ✅ Frontend is running on http://localhost:3000
- ⚠️ Backend needs to be started manually

## To Start the Backend Server:

1. Open a **new PowerShell or Command Prompt window**

2. Navigate to the backend folder:
   ```powershell
   cd "C:\Users\Aradhana\OneDrive\Desktop\AI Finance App\backend"
   ```

3. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. Start the server:
   ```powershell
   python start_server.py
   ```
   
   OR use uvicorn directly:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. You should see:
   ```
   ✓ App imported successfully!
   Starting uvicorn on http://127.0.0.1:8000
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

## Access the Application:

- **Frontend (React App)**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

## Troubleshooting:

If you see import errors, make sure all dependencies are installed:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv python-multipart openai httpx plotly email-validator numpy pandas Pillow passlib python-jose
```

## Note:
Keep the backend server window open while using the app. The frontend should already be running in another window.


