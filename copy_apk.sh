#!/bin/bash

# Script to copy APK from Android project to dashboard

ANDROID_PROJECT_PATH="../AOC_DOAPP"
APK_SOURCE_DIR="$ANDROID_PROJECT_PATH/app/build/outputs/apk/debug"
DASHBOARD_APK_DIR="uploads/apk"

echo "AOC APK Copy Script"
echo "==================="

# Check if Android project exists
if [ ! -d "$ANDROID_PROJECT_PATH" ]; then
    echo "ERROR: Android project not found at $ANDROID_PROJECT_PATH"
    echo "Please ensure the AOC_DOAPP project is in the parent directory"
    exit 1
fi

# Check if APK directory exists in Android project
if [ ! -d "$APK_SOURCE_DIR" ]; then
    echo "ERROR: APK directory not found at $APK_SOURCE_DIR"
    echo "Please build the Android project first:"
    echo "  cd $ANDROID_PROJECT_PATH"
    echo "  ./gradlew assembleDebug"
    exit 1
fi

# Find APK file
APK_FILE=$(find "$APK_SOURCE_DIR" -name "*.apk" -type f | head -1)

if [ -z "$APK_FILE" ]; then
    echo "ERROR: No APK file found in $APK_SOURCE_DIR"
    echo "Please build the Android project first"
    exit 1
fi

# Create dashboard APK directory if it doesn't exist
mkdir -p "$DASHBOARD_APK_DIR"

# Copy APK with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEW_APK_NAME="aoc_doapp_${TIMESTAMP}.apk"
DEST_PATH="$DASHBOARD_APK_DIR/$NEW_APK_NAME"

cp "$APK_FILE" "$DEST_PATH"

echo "✓ APK copied successfully!"
echo "  Source: $APK_FILE"
echo "  Destination: $DEST_PATH"
echo ""
echo "You can now upload this APK through the dashboard or it's ready for QR code generation."

