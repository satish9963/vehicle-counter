@echo off
REM Vehicle Counter - Quick Start Setup Script for Windows
setlocal enabledelayedexpansion

echo ==================================
echo Vehicle Counter - Setup ^& Launch
echo ==================================
echo.

REM Check Python
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found
echo.

REM Check Node.js
echo [INFO] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [SUCCESS] Node.js %NODE_VERSION% found
echo.

REM Create virtual environment
echo [INFO] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated
echo.

REM Install Python dependencies
echo [INFO] Installing Python dependencies (this may take a few minutes)...
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed
echo.

REM Download YOLO model
echo [INFO] Downloading YOLOv8 model (this may take a few minutes)...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Could not auto-download YOLO model, will download on first run
)
echo.

REM Install Node dependencies
echo [INFO] Installing Node.js dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Node.js dependencies installed
echo.

REM Create directories
echo [INFO] Creating necessary directories...
if not exist "uploads" mkdir uploads
if not exist "results" mkdir results
if not exist "models" mkdir models
echo [SUCCESS] Directories created
echo.

REM Summary
echo ==================================
echo [SUCCESS] Setup Complete!
echo ==================================
echo.
echo To run the application:
echo.
echo [INFO] Development Mode (Full Integration):
echo   npm run full-dev
echo.
echo [INFO] Or run components separately:
echo   Terminal 1: npm run backend
echo   Terminal 2: npm start
echo   Terminal 3: npm run electron
echo.
echo [INFO] For testing backend only:
echo   npm run backend
echo   Then open: http://localhost:8000/docs
echo.
echo [INFO] To build for distribution:
echo   npm run electron-build
echo.
echo For more info, see SETUP_GUIDE.md
echo.
pause
