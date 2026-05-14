# Android Emulator All-Story QA ExecPlan

## Purpose / Big Picture

Run a hands-on Android emulator QA pass without taking over an emulator that another app or agent may already be using. The pass should install the current app build, drive the UI with actual emulator input, capture screenshots, and review every catalog story at least at the detail and reader entry points.

## Progress

- [x] Read repo orientation and Android UI/harness source.
- [x] Checked currently attached Android devices and available AVDs.
- [x] Launch or select a non-overlapping emulator.
- [x] Build/install the Android debug app.
- [x] Drive the app UI with taps, text input, and screenshots.
- [x] Review every catalog story on-device for visible cover/detail/reader health.
- [x] Run final harness validation and record the outcome.

## Surprises & Discoveries

- `emulator-5554` is already running `codex_pixel_6_api35`; this QA pass must avoid it.
- Initial library screenshot showed the Android top bar title wrapping into a broken narrow column on phone portrait.
- UIAutomator is unreliable while the animated reader is on-screen, so the QA driver uses UI tree parsing for library/detail and stable coordinate taps for reader controls.
- The first p2 contact sheet caught some screenshots during page-turn state lag. Android page turn now updates the target page immediately and uses the curl as a visual finish.
- Final contact sheets show a major visual quality caveat: many premium story covers/scenes still use abstract generated visuals, not story-specific production-quality illustration.

## Decision Log

- Use `codex_medium_api35` on a separate emulator port if it can be launched.
- Use current source/manifests plus emulator screenshots as evidence, not old score docs.
- Keep smoke hooks as supporting evidence, but perform UI-driving QA with `adb shell input` and screenshots.
- Treat all-story Android flow/load evidence separately from art-quality judgment; a 24/24 flow pass does not mean the premium art is production-great.

## Outcomes & Retrospective

Completed on 2026-05-12.

Used a separate emulator, `emulator-5556` running `codex_medium_api35`, while leaving the pre-existing `emulator-5554` alone. Built, installed, launched, and drove the Android app with real `adb shell input` taps. Added `tools/android_all_story_emulator_qa.py` so the pass can be repeated against a specific serial.

Fixes made from emulator QA:

- Android compact library top bar no longer squeezes "Moon Jar Stories" into a broken portrait title column.
- Android button page turns now commit the target page immediately and keep the curl as a visual finish, which made all-story page-2 screenshots stable.
- `tools/score_reader_experience.py` now recognizes the new Android page-turn behavior.

Final evidence:

- Android all-story emulator QA: 24/24 flow-passed books on `emulator-5556`.
- Report: `.agent/tmp/artifacts/android-all-story-qa/android-all-story-qa-report.md`.
- Contact sheets: `.agent/tmp/artifacts/android-all-story-qa/contact-detail.png`, `contact-reader-p1.png`, and `contact-reader-p2.png`.
- `scripts/agent/validate`: passed after the Android page-turn scorer was updated.

Honest caveat:

- Flow/load/navigation passed for all 24 stories, but visual review did not prove "all stories are great." The contact sheets show many premium covers/scenes are still abstract generated visuals rather than story-specific production art. That remains an art-production gap, not an emulator-flow blocker.

## Context and Orientation

Canonical story and asset data lives under `shared-content/`. Android renders shared content through `ContentRepository` and the Compose UI in `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`.

## Plan of Work

1. Start a distinct emulator or confirm an unused attached one.
2. Assemble and install the debug APK.
3. Launch the app normally, capture the library, and use UIAutomator plus coordinate taps to navigate.
4. For every catalog book, open the detail screen, unlock premium once through the parent gate when needed, enter the reader, capture screenshots, advance pages, and return.
5. Summarize visual/interaction findings honestly.

## Concrete Steps

1. Launch `codex_medium_api35` on a separate port.
2. Wait for boot completion and install the APK.
3. Create or run a repeatable QA driver under `.agent/tmp/`.
4. Save artifacts under `.agent/tmp/artifacts/android-all-story-qa/`.
5. Run `scripts/agent/validate` before finishing.

## Validation and Acceptance

- The active emulator used for QA is not `emulator-5554`.
- Screenshots exist for library plus every catalog story detail/reader entry.
- QA notes call out visible blockers rather than inflating quality.
- `scripts/agent/validate` passes, or any blocker is documented exactly.

## Idempotence and Recovery

The QA run should be safe to repeat. Temporary screenshots and logs stay under `.agent/tmp/`. If the emulator launch fails, use a different available AVD or report the exact tooling failure.
