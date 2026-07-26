#!/usr/bin/env bash
# Alfa COS Phase 2 — Production Linux Build Script
set -e

echo "==================================================="
echo "  Alfa COS Phase 2 — Linux Build Pipeline"
echo "==================================================="

mkdir -p release/desktop release/android

echo "[1/3] Running Pytest Suite..."
python3 -m pytest tests/ -v

echo "[2/3] Building PySide6 Standalone Desktop Executable..."
python3 -m PyInstaller --clean alfa_desktop.spec

cp dist/AlfaDesktop release/desktop/AlfaDesktop-linux
echo "[✓] Desktop Executable packaged to release/desktop/AlfaDesktop-linux"

echo "[3/3] Building Android Application (Flutter)..."
cd android
flutter pub get
flutter analyze
flutter test
flutter build apk --release
flutter build appbundle --release
cd ..

cp android/build/app/outputs/flutter-apk/app-release.apk release/android/alfa-cos-mobile.apk || true
cp android/build/app/outputs/bundle/release/app-release.aab release/android/alfa-cos-mobile.aab || true

echo "==================================================="
echo "  [✓] Alfa COS Phase 2 Build Complete!"
echo "  Artifacts saved to release/ folder."
echo "==================================================="
