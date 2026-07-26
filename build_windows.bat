@echo off
REM Alfa COS v0.3 — Production Windows Build Script

echo ===================================================
echo   Alfa COS v0.3 — Windows Build Pipeline
echo ===================================================

mkdir release 2>nul
mkdir release\desktop 2>nul
mkdir release\android 2>nul

echo [1/3] Running Pytest Suite...
python -m pytest tests/ -v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pytest suite failed! Aborting build.
    exit /b %ERRORLEVEL%
)

echo [2/3] Building PySide6 Standalone Desktop Executable...
python -m PyInstaller --clean alfa_desktop.spec
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed! Aborting build.
    exit /b %ERRORLEVEL%
)

copy dist\AlfaDesktop.exe release\desktop\
echo [✓] Desktop Executable packaged to release\desktop\AlfaDesktop.exe

echo [3/3] Building Android Application (Flutter)...
cd android
call flutter pub get
call flutter analyze
call flutter test
call flutter build apk --release
call flutter build appbundle --release
cd ..

copy android\build\app\outputs\flutter-apk\app-release.apk release\android\alfa-cos-mobile.apk 2>nul
copy android\build\app\outputs\bundle\release\app-release.aab release\android\alfa-cos-mobile.aab 2>nul

echo ===================================================
echo   [✓] Alfa COS Phase 2 Build Complete!
echo   Artifacts saved to release/ folder.
echo ===================================================
