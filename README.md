# Moon Jar Stories

Premium multi-platform Korean folktale storybook product.

This repo is now a demoable native-app scaffold:

- `ios/MoonJarStoriesiOS/` - SwiftUI reader prototype
- `android/MoonJarStoriesAndroid/` - Kotlin + Jetpack Compose starter
- `shared-content/` - canonical catalog, story JSON, asset manifests, generated demo assets, and synthetic narration drafts
- `tools/` - validation, prompt export, demo asset generation, and production asset pipeline scripts
- `backend/` - entitlement and CMS contracts
- `docs/` - product, design, safety, and production pipeline docs

Story content lives once in `shared-content/`. Native apps render the same JSON and assets.

## What Is Demoable

- 24-book launch catalog
- 24 complete shared-content books: 5 free and 19 premium locked by entitlement
- 698 generated-review scene PNGs in production draft folders, with placeholders kept as fallback
- 19 premium story sheets imported into 560 story-specific premium runtime scenes and 19 premium covers
- 698 synthetic-draft English narration WAV files
- 698 optional synthetic-draft Korean narration WAV files
- 24 generated-review cover PNGs in production image folders
- 24 per-book character bibles
- Layered animation production manifest for 698 scenes
- Synthetic-draft ambient loops
- Synthetic-draft page flip, button tap, and additional story SFX drafts
- App icon placeholder
- 3 presentation mockups: library, reader, paywall
- iOS Library -> Book Detail -> Reader flow
- Android Library -> Book Detail -> Reader flow
- Mock parent gate and premium locking behavior

## Run Validation

```bash
python3 tools/validate_books.py
python3 tools/validate_assets.py
tools/run_all_checks.sh
# Optional full app-feedback pass, when simulators/devices are available:
scripts/agent/validate-ui
```

This checks that:

- all 24 complete books load
- every complete scene has an image asset
- every complete scene has narration audio
- every complete scene has image and audio prompts
- every complete scene references a valid animation type
- cover assets exist
- character bible entries exist
- asset manifests are valid
- asset candidate manifests resolve final > reviewed > draft > placeholder
- placeholder assets are not marked production-ready
- premium catalog entries remain locked by entitlement while still carrying complete shared-content payloads
- compliance flags keep ads, tracking, child accounts, child data collection, and child-facing external links off

## Agent Harness

Future Codex/agent runs should start with:

```bash
scripts/agent/doctor
```

Common harness commands:

```bash
scripts/agent/lint
scripts/agent/test
scripts/agent/validate
scripts/agent/validate-ui
scripts/agent/start backend
scripts/agent/smoke backend
scripts/agent/smoke ios
scripts/agent/smoke android
scripts/agent/smoke all
scripts/agent/garden
```

See `AGENTS.md`, `docs/README.md`, and `scripts/agent/README.md` for the repo-local knowledge system, ExecPlan rules, validation checks, and artifact locations. Temporary harness logs and smoke outputs live under `.agent/tmp/` and are ignored.

## Generate Demo Assets

```bash
python3 tools/generate_demo_assets.py
```

Generated files live under:

- `shared-content/assets/books/`
- `shared-content/audio/books/`
- `shared-content/assets/ui/`
- `shared-content/audio/ui/`
- `shared-content/assets/presentation/`

The generator uses the book JSON and prompt data to create deterministic demo placeholders. It writes real PNG/SVG/WAV files and updates complete book JSON with `coverAsset`, `imageAsset`, `narrationAudio`, and `ambientAudio` fields.

## Generate Prompt Exports

```bash
python3 tools/generate_image_prompts.py
python3 tools/generate_audio_prompts.py
```

Outputs:

- `tools/output/image_prompts.md`
- `tools/output/audio_prompts.md`

## Production Asset Pipeline

Generation is offline/dev-time only. The iOS and Android apps never generate images or audio live in the child experience; they only load local packaged or downloaded asset paths from `shared-content`.

Tool discovery in this environment:

- MCP generation tools: none exposed
- Image generation: built-in image generation was used offline for the current generated-review demo art; no configured MCP/API provider credentials are present for a production generator
- TTS narration: local macOS `say` with English and Korean voices is available; no premium MCP voice provider is configured
- Sound effects: first-party procedural synthetic drafts are generated locally; they are not final sound design
- Image upscaling: no AI upscaler; `sips` is available for basic file conversion/resizing only
- Audio normalization: project script applies simple WAV peak normalization after TTS
- File management: local filesystem/Python scripts

Status labels:

- Images: `placeholder`, `generated_draft`, `generated_reviewed`, `commissioned_draft`, `commissioned_reviewed`, `commissioned_final`, `rejected`
- Audio: `placeholder`, `synthetic_draft`, `synthetic_reviewed`, `human_recorded_draft`, `human_recorded_reviewed`, `human_recorded_final`, `rejected`

Production folders:

```text
shared-content/assets/placeholders/
shared-content/assets/generated-draft/
shared-content/assets/reviewed/
shared-content/assets/final/
shared-content/assets/manifests/

shared-content/audio/placeholders/
shared-content/audio/synthetic-draft/
shared-content/audio/reviewed/
shared-content/audio/human-recorded-final/
shared-content/audio/manifests/
```

Apps resolve assets from manifests by priority:

1. final
2. reviewed
3. generated draft / synthetic draft
4. placeholder

The story JSON stays stable when assets are upgraded. Update the manifest candidate list instead of editing every page.

Character bibles:

```text
shared-content/characters/
```

Layered animation plan:

```text
shared-content/animation/layer_manifest.json
```

Stage image placeholders into separated placeholder folders and write the image manifest:

```bash
python3 tools/generate_images.py --provider placeholder
```

Create the approval-first art job list and review reports:

```bash
python3 tools/create_art_approval_jobs.py
```

Outputs:

```text
shared-content/assets/manifests/art_approval_jobs.json
tools/output/art_review_checklist.md
tools/output/art_generation_bakeoff_report.md
```

Do not bulk-generate the remaining scenes until the approval set is reviewed:

- app hero style
- one cover concept
- tiger character sheet
- child character sheet
- forest scene
- house/night scene
- chase/tension scene

Image manifest:

```text
shared-content/assets/manifests/image_manifest.json
```

Current staged image folders:

```text
shared-content/assets/placeholders/images/scenes/
shared-content/assets/placeholders/images/covers/
shared-content/assets/placeholders/images/app-icon/
```

Generate English synthetic-draft narration offline. This is the default demo narration; Korean remains optional:

```bash
python3 tools/generate_audio.py --provider macos_say --languages en --english-voice Samantha --rate 145
```

Generate or refresh optional Korean synthetic-draft narration:

```bash
python3 tools/generate_audio.py --provider macos_say --languages ko --voice "Grandma (Korean (South Korea))" --rate 155
```

Audio manifest:

```text
shared-content/audio/manifests/audio_manifest.json
```

Refresh synthetic-draft UI, ambient, and story SFX:

```bash
python3 tools/generate_sound_drafts.py
```

Generate the voice provider bakeoff report:

```bash
python3 tools/create_voice_bakeoff_report.py
```

Output:

```text
tools/output/voice_bakeoff_report.md
```

Current narration folder:

```text
shared-content/audio/synthetic-draft/narration/
```

Normalize WAV assets:

```bash
python3 tools/normalize_audio.py shared-content/audio/synthetic-draft/narration
```

Import commissioned art/audio and register it in the manifest:

```bash
python3 tools/import_commissioned_assets.py --kind image_scene --story-id book.sun_moon --scene-id sun_moon_001 --source /path/to/page-001.png --status commissioned_draft
python3 tools/import_commissioned_assets.py --kind audio_narration --story-id book.sun_moon --scene-id sun_moon_001 --source /path/to/page-001.wav --status human_recorded_draft
```

Build or refresh the layer plan:

```bash
python3 tools/build_layer_manifest.py
```

To promote assets, add a new manifest candidate with the correct status and review fields. Do not mark anything final unless reviewer, review date, cultural review, child-safety review, and production approval are present.

After any asset replacement:

```bash
python3 tools/validate_books.py
python3 tools/validate_assets.py
```

## Run iOS / SwiftUI

Local build check:

```bash
cd ios/MoonJarStoriesiOS
swift build
```

If `swift test` cannot find `XCTest` because `xcode-select` points at Command Line Tools, run SwiftPM through Xcode:

```bash
cd ios/MoonJarStoriesiOS
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift build
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift test
```

Run the SwiftUI demo locally on macOS:

```bash
cd ios/MoonJarStoriesiOS
MOONJAR_CONTENT_ROOT="$(cd ../.. && pwd)/shared-content" swift run MoonJarStoriesiOS
```

Run as iPad/iPhone app:

```bash
open ios/MoonJarStoriesiOS/Package.swift
```

Then in Xcode, select the `MoonJarStoriesiOS` scheme and an iPad simulator.

The production Xcode target scaffold lives in:

```text
ios/MoonJarStoriesiOSApp/
```

It includes bundle identifier placeholders, Debug/Staging/Production `.xcconfig` files, an app icon asset catalog placeholder, and a launch screen placeholder.

The shared content is also bundled into the Swift package resources for simulator builds, so the app can run without setting `MOONJAR_CONTENT_ROOT`. If you want to override the bundled content while developing, set `MOONJAR_CONTENT_ROOT` to the repo's `shared-content` path.

CLI simulator smoke test:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl boot <SIMULATOR_UDID> || true
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl bootstatus <SIMULATOR_UDID> -b
SIMULATOR_UDID=<SIMULATOR_UDID> DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer tools/package_ios_sim_app.sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl launch <SIMULATOR_UDID> com.moonjar.stories.demo
```

Simulator demo routes:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl launch --terminate-running-process <SIMULATOR_UDID> com.moonjar.stories.demo --demo-detail
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl launch --terminate-running-process <SIMULATOR_UDID> com.moonjar.stories.demo --demo-reader
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl launch --terminate-running-process <SIMULATOR_UDID> com.moonjar.stories.demo --demo-paywall
```

Screenshots from simulator smoke tests are written to:

```text
.agent/tmp/artifacts/
```

The repeatable harness command is `scripts/agent/smoke ios`; it captures library, Real Book Mode, and playback screenshots plus reader self-test JSON.

## Build Android

```bash
cd android
./gradlew test
./gradlew assembleDebug
```

Debug APK:

```text
android/MoonJarStoriesAndroid/build/outputs/apk/debug/MoonJarStoriesAndroid-debug.apk
```

## Real vs Placeholder

Real:

- shared content schema
- 24-book catalog
- 24 complete child-safe all-catalog story scripts
- vocabulary, narration scripts, prompt metadata
- app flows and native JSON loading
- mock entitlement / parent gate flows
- validation checks

Placeholder:

- scene art and covers are generated-review demo drafts, not final commissioned illustration
- English narration WAVs are synthetic drafts, not final human-recorded narration
- Korean narration WAVs are optional synthetic drafts, not final human-recorded narration
- ambient, UI, and story SFX are synthetic drafts or placeholders, not final sound design
- app icon and screenshots are presentation placeholders
- StoreKit / Google Play Billing are mocked for the demo
- backend has an OpenAPI contract and local stub, not a production service

## Replace Placeholders With Production Assets

Use manifest candidates rather than rewriting page JSON:

- generated images: `shared-content/assets/generated-draft/`
- reviewed images: `shared-content/assets/reviewed/`
- final commissioned images: `shared-content/assets/final/`
- synthetic narration: `shared-content/audio/synthetic-draft/`
- reviewed audio: `shared-content/audio/reviewed/`
- final human narration: `shared-content/audio/human-recorded-final/`

The iOS and Android apps load the best available manifest path automatically.

After replacement, run:

```bash
python3 tools/validate_books.py
python3 tools/validate_assets.py
cd ios/MoonJarStoriesiOS && swift build && swift test
cd ../../android && ./gradlew test && ./gradlew assembleDebug
```

## Backend And Compliance

Backend contract and local stub:

```bash
python3 backend/service_stub.py
```

Files:

- `backend/openapi.yaml`
- `backend/entitlement_service_stub.md`
- `backend/catalog_service_stub.md`
- `backend/asset_manifest_service_stub.md`
- `backend/admin_workflow.md`
- `docs/entitlement_rules.md`
- `docs/compliance_kids_safety.md`
- `shared-content/compliance/app_behavior_flags.json`
