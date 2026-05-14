# Manual Emulator UI QA ExecPlan

## Purpose / Big Picture

Perform a hands-on Android emulator QA pass against the current story/asset authenticity build. This is intentionally different from a pure automated all-story pass: the agent will interact with the app, capture screenshots after meaningful UI actions, inspect those screenshots, and record visible UI findings, including premium stories beyond the free trial/free catalog set.

## Progress

- [x] Ran `scripts/agent/doctor`.
- [x] Confirmed existing `emulator-5554` is already attached and should not be disturbed.
- [x] Launch or attach separate QA emulator.
- [x] Install current debug APK.
- [x] Manually test library, premium card/detail/unlock flow, reader navigation, language toggles, playback controls, and late-catalog premium story screens.
- [x] Capture and inspect representative premium reader screens beyond the free stories.
- [x] Inspect screenshots and record findings.
- [x] Run final validation/lint or explain any blocker.

## Surprises & Discoveries

- `emulator-5556` booted cleanly, but repeated installs of the 2.0 GB debug APK eventually filled `/data` and later installs failed with `INSTALL_FAILED_INSUFFICIENT_STORAGE`. Final install and verification moved to the already-running `emulator-5554`, which had sufficient free space.
- `adb install -r` was unreliable with this asset-heavy APK; uninstall-then-install was the repeatable path during this pass.
- Simcheong page 1 exposed a phone portrait reader layout problem: the image took too much vertical space and story text looked clipped.
- Fairy/Woodcutter in `KO/EN` exposed a second problem: compact bilingual mode needed its own text-first layout and should not show partially clipped vocabulary chips.
- A late-catalog check of The Gentle Serpent Scholar exposed the long-page version of the same issue; bilingual phone portrait needed a more decisive text-first layout than the earlier Fairy-only adjustment.
- Rapid tap automation can be ignored during page-turn animation. High-risk Fairy pages were recaptured using slower, verified page indicators.

## Decision Log

- Prefer `codex_medium_api35` on port `5556` so the existing `emulator-5554` remains untouched. If the dedicated emulator cannot boot cleanly or runs out of space for the asset-heavy APK, use the already attached emulator only after recording that choice.
- Use adb tap/swipe/screenshot plus UIAutomator dumps as the manual testing substrate.
- Save artifacts under `.agent/tmp/artifacts/manual-emulator-ui-qa/`.
- Keep `KO/EN` phone portrait text readable ahead of vocabulary-chip density; hide vocabulary chips only for compact bilingual portrait.

## Outcomes & Retrospective

- Current APK was built and installed on emulator, first on `emulator-5556` and finally on `emulator-5554` after the dedicated QA emulator ran out of install space.
- Verified library covers are real story-specific art, not placeholder rings.
- Verified premium unlock flow through the prototype parent gate.
- Verified premium screens beyond the free catalog:
  - `current-fix-04-simcheong-reader-page1-after-layout-fix.png`: Simcheong page 1 after phone portrait text fix.
  - `current-fix-39-fairy-reader-page15-departure-final-actual.png`: Fairy departure is sober/bittersweet, with the fairy carrying one child in each arm and the woodcutter left below.
  - `current-fix-40-fairy-reader-page16-empty-cottage-final-actual.png`: empty cottage/sandals page reads lonely rather than cheerful.
  - `current-fix-41-fairy-reader-page18-bucket-ascent-final-actual.png`: sky-bucket ascent matches the page text.
  - `current-fix-73-5554-serpent-reader-page01-bilingual-final-tight.png` and `current-fix-74-5554-serpent-reader-page02-bilingual-final-tight.png`: late-catalog Serpent pages fit bilingual text and keep the serpent gentle, not monstrous.
- Fixed Android phone portrait reader layout:
  - single-language pages now reserve more text height while retaining large scene art;
  - compact bilingual pages use a text-first split, smaller type, and no vocabulary chips so the story is not visibly clipped.
- Remaining non-final caveat: visual assets are still generated/internal-demo art, not commissioned final production art.
- Validation passed:
  - `./gradlew test assembleDebug`
  - `scripts/agent/validate`

## Context and Orientation

Canonical content and assets are under `shared-content/`. The Android app packages shared content via Gradle’s `copySharedContent` task. The current target is to visually verify that new story-specific premium art appears in real app UI and that common reader controls behave sensibly.

## Plan of Work

1. Build current debug APK.
2. Launch separate emulator.
3. Install APK.
4. Manually exercise:
   - library top;
   - premium card/detail;
   - Simcheong reader;
   - page next/previous;
   - language toggle;
   - bedtime toggle;
   - playback button;
   - later premium story readers, including Fairy/Woodcutter and at least one late-catalog premium story;
   - back navigation.
5. Inspect screenshots.
6. Summarize pass/fail with exact artifacts.

## Concrete Steps

1. Run `./gradlew assembleDebug`.
2. Run emulator on port `5556`.
3. Install APK with `adb -s emulator-5556 install -r ...`.
4. Use adb tap/swipe and screenshots.
5. Use `view_image` to inspect the captured screens.

## Validation and Acceptance

- Screenshots show current new-asset build, not old ring placeholders.
- Library and reader controls are visibly usable.
- Premium story screens open and page navigation works.
- Any visible UX issue is reported honestly.

## Idempotence and Recovery

The pass writes only temporary artifacts under `.agent/tmp/artifacts/manual-emulator-ui-qa/`. The dedicated `emulator-5556` can be killed safely after the pass. `emulator-5554` was used only after `emulator-5556` ran out of install space; it now has the current debug APK installed and the app is open for inspection.
