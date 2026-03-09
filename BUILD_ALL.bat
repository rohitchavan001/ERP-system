@echo off
echo ============================================
echo   ERP System - Complete Build
echo ============================================
echo.
echo This will create:
echo   1. Desktop EXE (Windows installer)
echo   2. Mobile APK (Android app)
echo   3. Both will sync data automatically
echo.
pause

echo.
echo ============================================
echo   STEP 1: Building Desktop EXE
echo ============================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Creating EXE...
pyinstaller --clean ERP-System.spec

if exist "dist\ERP-System.exe" (
    echo ✓ Desktop EXE created: dist\ERP-System.exe
) else (
    echo ✗ Desktop EXE build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   STEP 2: Building Mobile APK
echo ============================================
echo.
echo NOTE: APK build requires:
echo   - Docker Desktop (for Windows)
echo   - OR GitHub Actions (automatic)
echo   - OR Linux/WSL
echo.
echo Choose build method:
echo   1. Docker (if installed)
echo   2. GitHub Actions (push to GitHub)
echo   3. Skip APK build
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Building APK with Docker...
    cd mobile
    docker build -t erp-apk -f- . << DOCKERFILE
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3 python3-pip openjdk-17-jdk git zip unzip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*
RUN pip3 install buildozer cython==0.29.33
WORKDIR /app
CMD ["buildozer", "-v", "android", "debug"]
DOCKERFILE
    
    docker run --rm -v "%cd%:/app" erp-apk
    cd ..
    
    if exist "mobile\bin\*.apk" (
        echo ✓ Mobile APK created: mobile\bin\
    ) else (
        echo ✗ APK build failed!
    )
) else if "%choice%"=="2" (
    echo.
    echo To build with GitHub Actions:
    echo   1. Push code to GitHub
    echo   2. Go to Actions tab
    echo   3. Download APK when ready
    echo.
    echo Run: git push origin main
) else (
    echo Skipping APK build...
)

echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Desktop EXE: dist\ERP-System.exe
echo Mobile APK:  mobile\bin\*.apk
echo.
echo ============================================
echo   SETUP INSTRUCTIONS
echo ============================================
echo.
echo DESKTOP (Windows PC):
echo   1. Run: dist\ERP-System.exe
echo   2. Desktop app will start
echo   3. API server runs automatically on port 8000
echo.
echo MOBILE (Android Phone):
echo   1. Install APK on phone
echo   2. Open app, login (admin/1234)
echo   3. Go to Settings (⋮ menu)
echo   4. Enter PC IP address (find with: ipconfig)
echo   5. Test connection and Save
echo.
echo SAME WIFI:
echo   - Both devices on same WiFi network
echo   - Mobile connects to PC's IP address
echo   - Data syncs automatically
echo.
echo DIFFERENT NETWORKS:
echo   - Use ngrok: ngrok http 8000
echo   - Enter ngrok URL in mobile settings
echo   - Works from anywhere!
echo.
echo See MOBILE_SETUP_GUIDE.md for details.
echo.
pause
