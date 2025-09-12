@echo off
echo 🚀 Setting up Patient Document Management System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

REM Backend setup
echo 📦 Setting up backend...
cd backend

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Copy environment file
if not exist .env (
    copy .env.example .env
    echo ⚠️  Please update the .env file with your API keys before running the server.
)

cd ..

REM Frontend setup
echo 📱 Setting up frontend...
cd frontend

REM Install Node.js dependencies
echo Installing Node.js dependencies...
npm install

cd ..

echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Get a Google Gemini API key from Google AI Studio
echo 2. Update backend/.env with your API key
echo 3. Start the backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload
echo 4. Start the frontend: cd frontend ^&^& npm start
echo.
echo 🌐 The application will be available at:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs

pause
