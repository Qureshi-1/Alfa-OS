#!/usr/bin/env bash
# Alfa COS Phase 2 — Dedicated Android Build Script (Linux/macOS)
set -e

echo "==================================================="
echo "  Alfa COS Phase 2 — Android Build Pipeline"
echo "==================================================="

mkdir -p release/android

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
echo "  [✓] Android Build Complete!"
echo "  APK: release/android/alfa-cos-mobile.apk"
echo "  AAB: release/android/alfa-cos-mobile.aab"
echo "==================================================="
