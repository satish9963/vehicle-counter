@echo off
REM Vehicle Counter - Windows .EXE Builder
REM This script builds the Windows installer and portable app

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║       Vehicle Counter - Windows .EXE Builder              ║
echo ║                                                            ║
echo ║  This will create:                                         ║
echo ║  1. Vehicle Counter Setup 1.0.0.exe (Installer)          ║
echo ║  2. Vehicle Counter 1.0.0.exe (Portable)                 ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Node modules exist
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node dependencies
        pause
        exit /b 1
    )
)

REM Build React app
echo.
echo [INFO] Building React application...
call npm run build
if errorlevel 1 (
    echo [ERROR] Failed to build React app
    pause
    exit /b 1
)

REM Create dist directory for binaries
if not exist "dist" mkdir dist

REM Build with Electron Builder
echo.
echo [INFO] Building Windows installers with Electron Builder...
echo [INFO] This may take 5-10 minutes...
echo.

call npx electron-builder ^
    --publish never ^
    --win portable exe ^
    --win nsis ^
    --c.files="build/**/*" ^
    --c.directories.buildResources="assets"

if errorlevel 1 (
    echo [ERROR] Failed to build Windows executables
    echo [INFO] Make sure you have:
    echo   - Node.js and npm installed
    echo   - Python 3.9+ in PATH
    echo   - 10GB+ free disk space
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              BUILD SUCCESSFUL!                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check for output files
if exist "dist\Vehicle Counter Setup 1.0.0.exe" (
    echo [SUCCESS] ✓ Installer created:
    echo   dist\Vehicle Counter Setup 1.0.0.exe
    echo.
    echo   Size: 
    for /f "tokens=5" %%A in ('dir "dist\Vehicle Counter Setup 1.0.0.exe" ^| findstr "Vehicle Counter Setup"') do echo   %%A bytes
) else (
    echo [WARNING] Installer not found
)

echo.

if exist "dist\Vehicle Counter 1.0.0.exe" (
    echo [SUCCESS] ✓ Portable app created:
    echo   dist\Vehicle Counter 1.0.0.exe
    echo.
    echo   Size:
    for /f "tokens=5" %%A in ('dir "dist\Vehicle Counter 1.0.0.exe" ^| findstr "Vehicle Counter 1"') do echo   %%A bytes
) else (
    echo [WARNING] Portable app not found
)

echo.
echo ════════════════════════════════════════════════════════════
echo.
echo INSTALLATION OPTIONS:
echo.
echo Option 1: INSTALLER (Recommended)
echo   - File: Vehicle Counter Setup 1.0.0.exe
echo   - Installation size: ~500MB
echo   - Auto-updates: Yes
echo   - Shortcut: Creates Start Menu shortcut
echo   - How to use: Double-click and follow installer
echo.
echo Option 2: PORTABLE (No Installation)
echo   - File: Vehicle Counter 1.0.0.exe
echo   - No installation needed
echo   - Run from any location
echo   - No registry changes
echo   - Smaller download: ~400MB
echo.
echo ════════════════════════════════════════════════════════════
echo.
echo [INFO] Both files are in the "dist" folder
echo.
echo NEXT STEPS:
echo   1. Close this window
echo   2. Go to the "dist" folder
echo   3. Run either installer or portable executable
echo   4. Follow the installation/launch prompts
echo.
echo ════════════════════════════════════════════════════════════
echo.

pause
