@echo off
REM Alfa COS Phase 2 — Dedicated Android Build Script (Windows)

echo ===================================================
echo   Alfa COS Phase 2 — Android Build Pipeline
echo ===================================================

mkdir release\android 2>nul

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
echo   [✓] Android Build Complete!
echo   APK: release/android/alfa-cos-mobile.apk
echo   AAB: release/android/alfa-cos-mobile.aab
echo ===================================================
