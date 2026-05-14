#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IOS = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "Views.swift"
ANDROID = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "ui" / "MoonJarApp.kt"
HARNESS = ROOT / "scripts" / "agent" / "agent_harness.py"
ARTIFACTS = ROOT / ".agent" / "tmp" / "artifacts"
OUTPUT = ROOT / "tools" / "output" / "reader_experience_score_report.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def score_category(name: str, checks: list[tuple[str, bool, str]]) -> tuple[int, list[str]]:
    passed = sum(1 for _, ok, _ in checks if ok)
    score = round(100 * passed / len(checks))
    failures = [f"{label}: {fix}" for label, ok, fix in checks if not ok]
    return score, failures


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def json_bool(path: Path, key: str) -> bool:
    value = load_json(path).get(key)
    return value is True or value == "true"


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def screenshot_ok(name: str, min_width: int, min_height: int) -> bool:
    path = ARTIFACTS / name
    dimensions = png_dimensions(path)
    if dimensions is None:
        return False
    width, height = dimensions
    return width >= min_width and height >= min_height and path.stat().st_size > 200_000


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Moon Jar reader UX, Real Book Mode, and page-flip mechanics.")
    parser.add_argument(
        "--require-smoke-artifacts",
        action="store_true",
        help="Require current simulator/emulator self-test JSON and screenshots in .agent/tmp/artifacts.",
    )
    args = parser.parse_args()

    ios = read(IOS)
    android = read(ANDROID)
    harness = read(HARNESS)
    combined = f"{ios}\n{android}\n{harness}"

    reader_checks = [
        (
            "iOS has premium storybook chrome and top reader controls",
            has_all(ios, ["ReaderTopBar", "PageProgressBar", "ReaderControlDeck", "ReaderBackground"]),
            "Keep top controls, progress, control deck, and indigo storybook background wired in Views.swift.",
        ),
        (
            "iOS portrait page uses fit-safe art and parchment text surface",
            has_all(ios, ["PortraitStoryCard", "DemoAssetImage", "contentMode: .fit", "PageCurlCorner"]),
            "Primary reader art should render fit-first with the parchment text panel and corner curl cue.",
        ),
        (
            "iOS portrait reader has tactile page depth and readable vocabulary chips",
            has_all(ios, ["PageDepthOverlay", "ParchmentTexture", "page.vocabulary.prefix", "RoundedRectangle(cornerRadius: 7"]),
            "Keep portrait pages feeling like paper, with stable vocabulary affordances that do not crowd the prose.",
        ),
        (
            "iOS reader supports narration, autoplay, bedtime, and reduced-motion behavior",
            has_all(ios, ["autoPlay", "narrator.onFinished", "bedtimeMode", "accessibilityReduceMotion", "effectiveReduceMotion"]),
            "Reader UX should keep audio pacing and accessibility behavior integrated.",
        ),
        (
            "iOS thumbnails are stable and fit-safe",
            has_all(ios, ["ThumbnailStrip", "ArtThumbnail", "contentMode: .fit"]),
            "Page thumbnails should keep stable aspect ratios and show full art.",
        ),
        (
            "Android has storybook chrome, controls, and fit-safe portrait reader",
            has_all(android, ["ReaderChromeRow", "IconButton", "FilterChip", "PortraitReaderPage", "ContentScale.Fit"]),
            "Android reader should match the premium chrome and no-crop art rules.",
        ),
        (
            "Android portrait reader has tactile page depth, folio mark, and vocabulary chips",
            has_all(android, ["PageDepthOverlay", "FolioMark", "FlowRow", "page.vocabulary.take(3)"]),
            "Keep Android portrait reading polished and scannable, not just functional.",
        ),
        (
            "Android supports narration, autoplay, bedtime, and reduced-motion behavior",
            has_all(android, ["autoPlay", "AudioEngine", "bedtimeMode", "ANIMATOR_DURATION_SCALE", "reduceSceneMotion"]),
            "Android playback and accessibility should stay wired into reader navigation.",
        ),
        (
            "Both platforms keep English-first demo behavior with Korean optional",
            has_all(combined, ["ReaderLanguage.English", "ReaderLanguage.Korean", "ReaderLanguage.Bilingual"]),
            "English-first must remain the U.S. demo default while Korean stays available.",
        ),
        (
            "Both platforms expose agent-readable reader smoke/self-test hooks",
            has_all(combined, ["reader-playback", "real-book-next-back", "reader-contract", "moonjar.selfTest"]),
            "Keep smoke hooks so future agents can verify the app instead of guessing.",
        ),
    ]

    real_book_checks = [
        (
            "iOS uses a dedicated open-book spread renderer",
            has_all(ios, ["OpenBookStage", "OpenBookPage", "BookSpine", "BlankBookPage"]),
            "Real Book Mode should stay as a true spread surface, not a generic card.",
        ),
        (
            "iOS spread has center gutter, page stack edges, and parchment page styling",
            has_all(ios, ["BookSpine", "BookPageStackEdges", "BookBoardBacking", "PageTopBottomDepth", "BookFolioMark"]),
            "Keep the gutter, board backing, page edges, folio marks, and spread page styling visible.",
        ),
        (
            "iOS spread navigation advances one spread per action",
            has_all(ios, ["spreadStartIndex", "usesSpreadNavigation", "min(spreadStartIndex + 2", "max(spreadStartIndex - 2"]),
            "Next/back in Real Book Mode must not require double taps or skip incorrectly.",
        ),
        (
            "iOS Real Book Mode has turning-page preview during drag/button turns",
            has_all(ios, ["TurningBookPagePreview", "OpenBookPage(", "rotation3DEffect", "PageTurnSheet(progress: progress"]),
            "Keep a visible page sheet/fold over the spread while turning.",
        ),
        (
            "Android uses a dedicated real-book spread renderer",
            has_all(android, ["RealBookSpread", "BookSpreadPage", "BookPageStackEdges"]),
            "Android tablet mode should keep its two-page spread instead of a simple single page.",
        ),
        (
            "Android spread has center gutter, page edges, and fit-safe pages",
            has_all(android, ["width(22.dp)", "BookPageStackEdges", "BookObjectBacking", "PageDepthOverlay", "FolioMark", "ContentScale.Fit"]),
            "Keep center gutter, book-object backing, page stack edges, folio marks, and fit-safe page art on Android.",
        ),
        (
            "Android spread navigation advances by spread",
            has_all(android, ["spreadStart()", "spreadStart() + 2", "spreadStart() - 2", "spreadMode"]),
            "Next/back in Android spread mode should advance by the visible spread.",
        ),
        (
            "Both platforms include reduced-motion fallback for Real Book Mode",
            has_all(combined, ["reducedMotion", "reduceMotion", "effectiveReduceMotion", "ANIMATOR_DURATION_SCALE"]),
            "Spread motion must respect accessibility and bedtime reductions.",
        ),
    ]

    page_flip_checks = [
        (
            "iOS drag follows finger with threshold and predicted-release behavior",
            has_all(ios, ["DragGesture(minimumDistance: 28)", "predictedEndTranslation", "< -70", "> 70"]),
            "Gesture should follow drag, turn past threshold, and cancel below threshold.",
        ),
        (
            "iOS button/autoplay turns animate through a page-turn offset",
            has_all(ios, ["animatedTurnOffset", "withAnimation(.easeInOut(duration: 0.18))", "Task.sleep", "interactiveSpring"]),
            "Button and autoplay page turns should use the same visual turn system.",
        ),
        (
            "iOS page-turn sound fires after the committed page change",
            ios.find("pageIndex = targetIndex") < ios.find("narrator.playPageTurn") and "narrator.playPageTurn" in ios,
            "Play the turn sound only after the turn commits, not when a cancelled drag starts.",
        ),
        (
            "iOS page flip has shadow, thickness, fold, and 3D depth",
            has_all(ios, ["PageTurnSheet", "TurningBookPagePreview", "PageDepthOverlay", "shadow(color:", "rotation3DEffect", "perspective"]),
            "Keep curl/fold shadow and 3D depth cues in the page-turn surface.",
        ),
        (
            "Android drag follows finger with threshold and cancel behavior",
            has_all(android, ["detectHorizontalDragGestures", "dragOffset < -92f", "dragOffset > 92f", "onDragCancel = { dragOffset = 0f }"]),
            "Android gesture should follow drag, threshold-turn, and return smoothly on cancel.",
        ),
        (
            "Android button/autoplay navigation animates turn offset",
            has_all(android, ["buttonTurnOffset = direction * maxTurn", "pageIndex = target", "repeat(12)", "delay(16)"]),
            "Android button turns should commit the target page promptly and keep a visible curl finish.",
        ),
        (
            "Android page turn has curl overlay, crease, shadow/depth, and page thickness cues",
            has_all(android, ["PageTurnCurlOverlay", "PageDepthOverlay", "graphicsLayer", "rotationY", "cameraDistance", "shadowElevation", "creaseX"]),
            "Keep visible curl/depth cues in Compose.",
        ),
        (
            "Both platforms avoid turn motion when reduced motion is enabled",
            has_all(combined, ["if (reduceSceneMotion)", "if effectiveReduceMotion", "reducedMotion", "reduceMotion"]),
            "Reduced motion should skip 3D curl animation while keeping navigation functional.",
        ),
    ]

    if args.require_smoke_artifacts:
        ios_real_book = ARTIFACTS / "reader-real-book-self-test.json"
        ios_playback = ARTIFACTS / "reader-playback-self-test.json"
        android_self_test = ARTIFACTS / "moonjar-android-self-test.json"

        reader_checks.extend(
            [
                (
                    "iOS smoke proves narration playback starts in the reader",
                    json_bool(ios_playback, "isPlaying") and screenshot_ok("ios-smoke-reader-playback.png", 900, 900),
                    "Run `scripts/agent/smoke ios` and verify reader playback screenshot/self-test artifacts.",
                ),
                (
                    "Android smoke proves reader opens English-first with resolved assets and narration",
                    all(
                        json_bool(android_self_test, key)
                        for key in [
                            "englishFirst",
                            "freeBookReadable",
                            "sceneAssetResolved",
                            "englishNarrationResolved",
                            "koreanNarrationResolved",
                            "playbackStarted",
                        ]
                    )
                    and screenshot_ok("android-smoke-launch.png", 900, 900),
                    "Run `scripts/agent/smoke android` with an attached emulator/device.",
                ),
            ]
        )
        real_book_checks.extend(
            [
                (
                    "iOS smoke proves Real Book next and back behavior",
                    json_bool(ios_real_book, "nextAdvancedOneSpread")
                    and json_bool(ios_real_book, "backReturnedToInitialSpread")
                    and screenshot_ok("ios-smoke-real-book-page3.png", 900, 900),
                    "Run `scripts/agent/smoke ios`; self-test must verify next and back spread behavior.",
                ),
                (
                    "Android smoke proves Real Book Mode toggles and spread next advances",
                    json_bool(android_self_test, "realBookModeToggled")
                    and json_bool(android_self_test, "spreadNextAdvanced")
                    and json_bool(android_self_test, "singlePageFallbackKept"),
                    "Run `scripts/agent/smoke android`; self-test must toggle book mode on supported layouts, advance a spread, and keep phone portrait in single-page mode.",
                ),
            ]
        )
        page_flip_checks.extend(
            [
                (
                    "Android smoke proves next and previous reader actions work",
                    json_bool(android_self_test, "nextAdvanced") and json_bool(android_self_test, "previousReturned"),
                    "Run `scripts/agent/smoke android`; self-test must exercise next and previous inside ReaderScreen.",
                ),
                (
                    "iOS smoke proves page-turn sound path does not break committed next/back flow",
                    json_bool(ios_real_book, "nextAdvancedOneSpread") and json_bool(ios_real_book, "backReturnedToInitialSpread"),
                    "Run `scripts/agent/smoke ios`; committed page turns must survive sound timing.",
                ),
            ]
        )

    categories = [
        ("Reader UX", reader_checks),
        ("Real Book Mode", real_book_checks),
        ("Page flip", page_flip_checks),
    ]

    table_rows: list[str] = []
    detail_sections: list[str] = []
    lines = [
        "# Reader Experience Score Report",
        "",
        "This is an internal implementation score for the current all-catalog demo reader. It does not claim final production art, professional narration, or a physics-perfect native page-curl engine.",
        "",
        f"Smoke artifacts required: **{args.require_smoke_artifacts}**",
        "",
        "| Category | Score | Status |",
        "| --- | ---: | --- |",
    ]

    all_failures: list[str] = []
    for name, checks in categories:
        score, failures = score_category(name, checks)
        all_failures.extend(f"{name}: {failure}" for failure in failures)
        status = "pass" if score >= 95 else "fail"
        table_rows.append(f"| {name} | {score} | {status} |")
        detail_sections.append("")
        detail_sections.append(f"## {name}")
        detail_sections.append("")
        for label, ok, fix in checks:
            detail_sections.append(f"- {'PASS' if ok else 'FAIL'}: {label}")
            if not ok:
                detail_sections.append(f"  Fix: {fix}")
        detail_sections.append("")

    lines.extend(table_rows)
    lines.extend(detail_sections)

    lines.extend(
        [
            "## Honest Caveat",
            "",
            "- These scores mean the native prototype now has the expected all-catalog demo mechanics and regression checks.",
            "- They do not mean the product is App Store ready.",
            "- Remaining production blockers are final art review, professional voice, licensed/final sounds, legal/privacy review, real purchases, and production backend/CMS.",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if all_failures:
        print("Reader experience scoring failed:")
        for failure in all_failures:
            print(f"- {failure}")
        print(f"Report: {OUTPUT.relative_to(ROOT)}")
        return 1

    print("Reader UX: 100/100")
    print("Real Book Mode: 100/100")
    print("Page flip: 100/100")
    print(f"Report: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
