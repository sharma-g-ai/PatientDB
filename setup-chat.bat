@echo off
title Healthix Patient Chat - Enhanced with File Attachments

echo.
echo 🏥 ========================================
echo    HEALTHIX PATIENT CHAT SYSTEM
echo    Enhanced with File Attachment Support  
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo ❌ ERROR: Please run this script from the PatientDB root directory
    echo    Current directory: %CD%
    echo    Expected files: backend\main.py, frontend\index.html
    pause
    exit /b 1
)

echo 📦 Installing/updating dependencies...
cd backend
pip install -r ..\requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    echo 💡 Try running: pip install fastapi uvicorn python-multipart
    pause
    exit /b 1
)

echo.
echo 🚀 Starting Healthix Backend Server...
echo ⏳ Please wait for the server to initialize...
echo.
echo 📍 Server URL: http://localhost:8000
echo 💬 Enhanced Chat: http://localhost:8000/chat  
echo 📖 API Documentation: http://localhost:8000/docs
echo.
echo 🎯 ENHANCED FEATURES ACTIVE:
echo    � File Attachment Support
echo    📊 Excel/CSV Data Processing  
echo    🏥 Medical Document Analysis
echo    💾 Persistent Chat Context
echo.
echo 📎 Supported file types:
echo    • Documents: PDF, JPG, PNG, TXT
echo    • Data Files: Excel (.xlsx/.xls), CSV, TSV, JSON
echo    • Size Limit: 20MB per file
echo.
echo 🔧 Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
python main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Server failed to start
    echo 💡 Common solutions:
    echo    1. Make sure Python is installed
    echo    2. Check if port 8000 is available
    echo    3. Verify all dependencies are installed
    echo.
)

echo.
echo ✅ Server shutdown complete
pause