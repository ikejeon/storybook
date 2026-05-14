#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IOS_DIR="$ROOT_DIR/ios/MoonJarStoriesiOS"
DERIVED_DATA="$ROOT_DIR/build/ios-sim"
PRODUCTS="$DERIVED_DATA/Build/Products/Debug-iphonesimulator"
APP="$PRODUCTS/MoonJarStoriesiOS.app"
BUNDLE_ID="com.moonjar.stories.demo"
DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_UDID="${SIMULATOR_UDID:-}"

if [[ -z "$SIMULATOR_UDID" ]]; then
  SIMULATOR_UDID="$(DEVELOPER_DIR="$DEVELOPER_DIR" /usr/bin/xcrun simctl list devices booted | awk -F '[()]' '/Booted/ { print $2; exit }')"
fi

if [[ -z "$SIMULATOR_UDID" ]]; then
  echo "Set SIMULATOR_UDID to an available iOS Simulator UDID, or boot a simulator first." >&2
  exit 1
fi

cd "$IOS_DIR"
"$DEVELOPER_DIR/usr/bin/xcodebuild" \
  -scheme MoonJarStoriesiOS \
  -destination "id=$SIMULATOR_UDID" \
  -derivedDataPath "$DERIVED_DATA" \
  build

rm -rf "$APP"
mkdir -p "$APP"
cp "$PRODUCTS/MoonJarStoriesiOS" "$APP/MoonJarStoriesiOS"
cp -R "$PRODUCTS/MoonJarStoriesiOS_MoonJarStoriesiOS.bundle" "$APP/"

/usr/libexec/PlistBuddy -c 'Clear dict' "$APP/Info.plist" >/dev/null
/usr/libexec/PlistBuddy -c 'Add :CFBundleDevelopmentRegion string en' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleDisplayName string Moon Jar Stories' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleExecutable string MoonJarStoriesiOS' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $BUNDLE_ID" "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleInfoDictionaryVersion string 6.0' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleName string MoonJarStories' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundlePackageType string APPL' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleShortVersionString string 0.1.0' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleVersion string 1' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :LSRequiresIPhoneOS bool true' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :MinimumOSVersion string 17.0' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UIDeviceFamily array' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UIDeviceFamily:0 integer 1' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UIDeviceFamily:1 integer 2' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UILaunchScreen dict' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UIApplicationSceneManifest dict' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :UIApplicationSceneManifest:UIApplicationSupportsMultipleScenes bool true' "$APP/Info.plist"

/usr/bin/codesign --force --sign - --timestamp=none --generate-entitlement-der "$APP"
DEVELOPER_DIR="$DEVELOPER_DIR" /usr/bin/xcrun simctl uninstall "$SIMULATOR_UDID" "$BUNDLE_ID" >/dev/null 2>&1 || true
DEVELOPER_DIR="$DEVELOPER_DIR" /usr/bin/xcrun simctl install "$SIMULATOR_UDID" "$APP"

echo "Installed $APP on simulator $SIMULATOR_UDID"
