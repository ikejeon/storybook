#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FLAGS = ROOT / "shared-content" / "compliance" / "app_behavior_flags.json"

SCAN_ROOTS = [
    ROOT / "ios" / "MoonJarStoriesiOS" / "Package.swift",
    ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS",
    ROOT / "android" / "MoonJarStoriesAndroid" / "build.gradle.kts",
    ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main",
]

SCAN_SUFFIXES = {".swift", ".kt", ".kts", ".xml", ".plist", ".xcconfig", ".gradle"}

SCAN_EXCLUDE_PARTS = {
    ".build",
    ".gradle",
    "build",
    "Resources",
    "generated",
    "shared-content",
}

DISALLOWED_PATTERNS = [
    (r"\bAVSpeechSynthesizer\b", "Do not add live TTS fallback inside the child app; use packaged/offline audio only."),
    (r"\bWKWebView\b|\bSFSafariViewController\b|\bWebView\b", "Do not add child-facing web views."),
    (r"UIApplication\.shared\.open|openURL\s*\(|Intent\.ACTION_VIEW", "External links must not be child-facing and require a parent gate."),
    (r"FirebaseAnalytics|firebase-analytics|Analytics\.log|AppTrackingTransparency|ATTrackingManager", "Do not add tracking/analytics SDKs to the child experience."),
    (r"GoogleMobileAds|play-services-ads|GADBannerView|\bAdView\b", "Do not add ads or ad SDKs."),
    (r"api\.openai\.com|elevenlabs|clova|texttospeech|text-to-speech", "The child app must not call live AI/TTS providers."),
    (r"NSLocationWhenInUseUsageDescription|ACCESS_FINE_LOCATION|ACCESS_COARSE_LOCATION", "The child app should not request location permissions."),
    (r"RECORD_AUDIO|NSMicrophoneUsageDescription", "Voice recording requires a separate adult-consent design and is not allowed in the current child app."),
]

REQUIRED_SOURCE_MARKERS = [
    (
        ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "Views.swift",
        ["ParentGateView", "PaywallView", "ParentGate"],
        "iOS paywall/purchase flow should stay parent-gated.",
    ),
    (
        ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "ui" / "MoonJarApp.kt",
        ["ParentGateDialog", "PaywallDialog", "showParentGate"],
        "Android paywall/purchase flow should stay parent-gated.",
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def is_excluded(path: Path) -> bool:
    parts = set(path.relative_to(ROOT).parts)
    return bool(parts & SCAN_EXCLUDE_PARTS)


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SCAN_SUFFIXES and not is_excluded(path):
                files.append(path)
    return sorted(set(files))


def validate_flags(errors: list[str]) -> None:
    if not APP_FLAGS.exists():
        errors.append(f"{rel(APP_FLAGS)} is missing; child-safety behavior flags must be explicit.")
        return
    flags = json.loads(APP_FLAGS.read_text(encoding="utf-8"))
    expected_false = [
        "adsEnabled",
        "thirdPartyTrackingEnabled",
        "childAccountsEnabled",
        "childFacingExternalLinksEnabled",
        "childDataCollectionEnabled",
        "liveImageGenerationInChildApp",
        "liveTtsGenerationInChildApp",
    ]
    for key in expected_false:
        if flags.get(key) is not False:
            errors.append(f"{rel(APP_FLAGS)}: `{key}` must be false for the child app.")
    expected_true = [
        "parentGateRequiredForPurchases",
        "parentGateRequiredForRestorePurchases",
        "parentGateRequiredForSettings",
    ]
    for key in expected_true:
        if flags.get(key) is not True:
            errors.append(f"{rel(APP_FLAGS)}: `{key}` must be true.")
    for item in flags.get("dataCollected", []):
        if item.get("childData") is not False:
            errors.append(f"{rel(APP_FLAGS)}: child data collection is not allowed for `{item.get('name')}`.")
        if item.get("sharedWithThirdParties") is not False:
            errors.append(f"{rel(APP_FLAGS)}: third-party sharing is not allowed for `{item.get('name')}`.")


def validate_sources(errors: list[str]) -> None:
    scan_files = iter_scan_files()
    if not scan_files:
        errors.append("Kids-safety scanner found no iOS/Android app source files. Check SCAN_ROOTS in tools/validate_kids_safety.py.")
        return
    for path in scan_files:
        text = load_text(path)
        for pattern, reason in DISALLOWED_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                errors.append(f"{rel(path)}: disallowed child-app pattern `{match.group(0)}`. {reason}")

    for path, markers, message in REQUIRED_SOURCE_MARKERS:
        if not path.exists():
            errors.append(f"{rel(path)} is missing; cannot verify parent gate markers.")
            continue
        text = load_text(path)
        missing = [marker for marker in markers if marker not in text]
        if missing:
            errors.append(f"{rel(path)}: missing parent-gate marker(s) {missing}. {message}")


def main() -> int:
    errors: list[str] = []
    validate_flags(errors)
    validate_sources(errors)
    if errors:
        print("Moon Jar kids/privacy safety validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Moon Jar kids/privacy safety validation passed: no ads, tracking, live AI/TTS, child accounts, child external links, or ungated purchase markers found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
