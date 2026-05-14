# Harness Engineering Foundation ExecPlan

## Purpose / Big Picture

Make Moon Jar Stories easier for future Codex and agent runs to understand, modify, validate, review, and keep clean. The harness should be practical and runnable locally: repo-local knowledge, executable commands, validation scripts, architecture/taste checks, app feedback artifacts, and doc-gardening routines.

This repo is a multi-platform storybook product scaffold, not a single-framework app. The harness must fit the detected stack:

- iOS prototype: SwiftPM package at `ios/MoonJarStoriesiOS/`.
- Android prototype: Gradle/Kotlin/Compose app at `android/`.
- Shared content/assets: JSON and manifests under `shared-content/`.
- Backend stub: Python HTTP server at `backend/service_stub.py`.
- Validation/tooling: Python and shell scripts under `tools/`.
- Root package manager: none detected.
- CI: none detected before this plan.

## Progress

- [x] Inspected repository structure, docs, existing validation, iOS package, Android Gradle setup, backend stub, and gitignore.
- [x] Created the ExecPlan and harness directory skeleton.
- [x] Add concise `AGENTS.md` and deeper docs.
- [x] Add agent command index and executable commands.
- [x] Add docs freshness checks.
- [x] Add architecture/taste checks.
- [x] Add local app/smoke/log harness.
- [x] Add garden routine and evidence-oriented audit tooling.
- [x] Add lightweight CI workflow where appropriate.
- [x] Run final validation and record outcomes.
- [x] Added native content-contract tests for SwiftPM and Android JVM.
- [x] Added backend response-shape assertions and iOS simulator smoke screenshots/self-test JSON.
- [x] Added Android smoke harness that fails honestly when no emulator/device is attached.
- [x] Removed live AVSpeechSynthesizer fallback from the child app; narration now only plays packaged/offline assets.
- [x] Started local-only "push toward 95" pass: schema alignment, deeper native tests, backend smoke contract cases, iOS entitlement tile consistency, and Android emulator self-test hook.
- [x] Story-writing 95 pass: added a stricter editorial scorecard, revised all complete catalog books for read-aloud craft, regenerated draft narration/manifests, restored sound drafts, and validated/synced app bundles.
- [x] Reader-experience 95 pass: improved iOS/Android turn mechanics, added turning-page/curl overlays, fixed reduced-motion sound ordering, and added `tools/score_reader_experience.py` as a regression gate for Reader UX, Real Book Mode, and Page flip.
- [x] Review-agent hardening pass: fixed repo-local P1/P2 findings around artifact-backed scoring, iOS/Android self-test coverage, backend request validation, payment product IDs, asset-status crosswalks, visual-layout QA, kids-safety scanning, durable markdown reports, and CI parity.
- [x] Second review-agent hardening pass: added `scripts/agent/validate-ui`, `tools/run_all_checks.sh --with-smoke`, strict visual-layout QA with zero critical warnings, recursive kids-safety source scanning, and stricter backend enum/date/product validation with smoke cases.

## Surprises & Discoveries

- The repo has no root package manager; commands should be plain shell/Python scripts.
- Existing `tools/run_all_checks.sh` already validates books/assets/generated-draft readiness and builds iOS/Android.
- Production readiness intentionally fails at `--level production` because no final commissioned art or human-recorded narration exists.
- No CI directory exists yet.
- `.gitignore` was very small and did not ignore `.agent/tmp/`.
- GitHub Actions was absent, so this pass added a lightweight docs/content/backend-smoke workflow instead of a full mobile-build workflow.
- This workspace has no `.git` directory, so review against `origin/main` and tracked-artifact verification are impossible here. The harness reports this as a warning instead of guessing.
- `xcode-select` points at Command Line Tools in this environment; SwiftPM tests need Xcode's toolchain via `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift test`.
- Android `adb` is available only if Android SDK platform-tools and an emulator/device are attached. An emulator was attached during the final local pass, and Android smoke passed.
- The reviewer found the checked-in book JSON schema lagged the canonical validator. The schema now includes `text`, `storyBeat`, vocabulary definitions, expanded asset statuses, and top-level asset/bible fields; `validate_books.py` now checks that schema contract does not drift again.
- The complete catalog now has intended per-book page counts defined by `shared-content/catalog.json`. The next content lift should improve prose quality and metadata consistency rather than adding pages by default.
- Reader UX, Real Book Mode, and Page flip can be scored mechanically for the all-catalog demo target, but those scores are not a claim of final production art, professional voice, or a physics-perfect native page-curl engine.
- Review against `origin/main` cannot run literally in this workspace because there is no `.git` directory. The practical substitute is a review-agent pass over the current workspace plus `scripts/agent/*` and smoke artifacts.

## Decision Log

- Use `scripts/agent/` as the command home because the repo already uses `tools/` for product/content tooling; `scripts/agent/` cleanly separates agent harness commands.
- Use dependency-free Python for mechanical checks so the harness works without adding paid SaaS, secrets, or extra package managers.
- Keep `AGENTS.md` short and put detailed guidance under `docs/`.
- Make architecture checks conservative: file-size thresholds, temp artifact hygiene, obvious secret scanning, required app/content docs, and Swift/Android shared-content duplication checks.
- Add a lightweight GitHub Actions workflow because no CI exists and the project benefits from an automated harness/docs/content gate. Mobile builds remain local unless the runner has required tools.
- Use Xcode's `xcrun swift` from the harness when Xcode exists so XCTest is available even if the selected developer directory is Command Line Tools.
- Keep Android smoke separate from `smoke all` for now because it requires an attached emulator/device and would otherwise make routine smoke checks fail on machines without Android Studio open.
- Add Android self-test as an app-level debug launch extra instead of brittle tap automation. The harness asserts content loading, English-first mode, free/premium entitlement behavior, image resolution, and English/Korean narration resolution from inside the app process, and polls for the matching token so it does not read stale or pre-startup output.

## Outcomes & Retrospective

Implemented a practical, dependency-free harness for future agent work:

- concise `AGENTS.md` map;
- deeper docs under `docs/`;
- `scripts/agent/` command index and wrappers;
- docs freshness checks;
- architecture/taste checks;
- backend startup/smoke harness with artifacts;
- garden routine;
- lightweight GitHub Actions workflow.

Latest validation results from this pass:

- `scripts/agent/doctor`: passed.
- `scripts/agent/lint`: passed with allowlisted large data/demo UI warnings.
- `scripts/agent/test`: passed, including SwiftPM XCTest and Android JVM tests.
- `scripts/agent/validate`: passed.
- `scripts/agent/smoke backend`: passed with response-shape assertions and wrote `.agent/tmp/artifacts/backend-smoke-transcript.md`.
- `scripts/agent/smoke ios`: passed and wrote `.agent/tmp/artifacts/ios-smoke-library.png`, `.agent/tmp/artifacts/ios-smoke-real-book-page3.png`, `.agent/tmp/artifacts/ios-smoke-reader-playback.png`, `reader-real-book-self-test.json`, and `reader-playback-self-test.json`.
- `scripts/agent/smoke android`: passed with an attached emulator after the harness was updated to poll for tokenized app self-test output during shared-content startup.
- `scripts/agent/garden`: passed and wrote `.agent/tmp/artifacts/garden-report.md`.
- `tools/run_all_checks.sh`: passed, including SwiftPM XCTest.
- `python3 tools/score_reader_experience.py --require-smoke-artifacts`: passed with Reader UX, Real Book Mode, and Page flip at 100/100 using iOS/Android smoke JSON and screenshots.
- `python3 tools/validate_kids_safety.py`: passed; no child-app ads, tracking, live AI/TTS, child accounts, child external links, or ungated purchase markers found.
- `python3 tools/validate_payments_readiness.py`: passed; native StoreKit/Play Billing scaffolds cover subscription, lifetime, and individual book product IDs.
- `python3 tools/validate_asset_status_crosswalk.py`: passed; manifests provide draft-or-better runtime assets while book JSON keeps fallback placeholder status explicit.
- `python3 tools/validate_visual_layout.py`: passed with manual-review warnings; dimensions and smoke screenshots are fit-safe, while source art composition still needs creative review.
- `scripts/agent/validate-ui`: passed; runs default validation plus backend/iOS/Android smoke, artifact-backed reader score, and strict visual layout QA.
- `tools/run_all_checks.sh --with-smoke`: passed; runs content checks, smoke artifacts, native builds/tests, and strict layout.
- `python3 tools/validate_production_readiness.py --level release-candidate`: failed as expected because final art/audio, deployed backend receipt verification, store products, legal/privacy signoff, review signoff, signing, and store listing evidence do not exist yet.

Known warnings are intentional:

- `Views.swift` is a large allowlisted demo reader surface.
- Canonical story JSON, generated manifests, layer plans, and bundled shared-content resources are large data files validated by product scripts rather than split by the architecture check.

## Context and Orientation

Moon Jar Stories is a premium Korean folktale storybook app prototype with native iOS and Android readers sharing one content and asset pipeline. The repo already contains:

- `shared-content/catalog.json` and complete/free story JSON under `shared-content/books/`.
- Asset and audio manifests under `shared-content/assets/manifests/` and `shared-content/audio/manifests/`.
- iOS SwiftUI reader source under `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/`.
- Android Compose source under `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/`.
- Backend API contract and local stub under `backend/`.
- Content and asset validation scripts under `tools/`.

Future agents should treat `shared-content/` as canonical and avoid duplicating story data inside native apps.

## Plan of Work

1. Add repo-local agent knowledge:
   - `AGENTS.md`
   - docs map and architecture/reliability/security/product docs
   - ExecPlan guidance and tech-debt tracker
2. Add agent commands:
   - `doctor`, `test`, `lint`, `validate`, `start`, `smoke`, `garden`
3. Add mechanical checks:
   - docs freshness / links / ExecPlan sections
   - architecture/taste invariants
4. Add app feedback harness:
   - local backend startup with logs
   - smoke test against backend endpoints and saved transcript
5. Add CI:
   - lightweight GitHub Actions workflow for harness lint/validation that avoids platform-specific paid dependencies.
6. Run all relevant commands and fix issues introduced by this pass.
7. For story-writing passes, use a measurable scorecard plus human-readable rewrite report. The scorecard is not a substitute for a children’s editor or Korean cultural reviewer, but it prevents future content from sliding back into flat plot summary.

## Concrete Steps

1. Create/refresh docs structure.
2. Implement `scripts/agent/agent_harness.py` and wrapper scripts.
3. Update `.gitignore` for `.agent/tmp/`.
4. Add CI workflow.
5. Run:
   - `scripts/agent/doctor`
   - `scripts/agent/lint`
   - `scripts/agent/test`
   - `scripts/agent/validate`
   - `scripts/agent/smoke`
   - `scripts/agent/garden`
6. Update this ExecPlan with results.

## Validation and Acceptance

The harness is accepted when:

- `AGENTS.md` exists and links to key docs.
- Required docs exist and are cross-linked from `docs/README.md`.
- Agent commands are executable and documented.
- Docs checks catch missing required docs/headings and broken local links.
- Architecture checks catch temp artifacts, obvious secrets, oversized files outside allowlists, and shared-content duplication drift.
- Smoke test produces a legible artifact under `.agent/tmp/artifacts/`.
- `agent:validate` runs the minimal before-PR bundle and summarizes pass/fail.
- CI has a lightweight harness workflow or a documented reason not to add one.

## Idempotence and Recovery

- Agent commands should be safe to run repeatedly.
- Temporary logs/artifacts are written under `.agent/tmp/` and ignored by git.
- `scripts/agent/start` should stop an existing backend stub on the same port only if it was started by this harness and recorded in `.agent/tmp/backend.pid`.
- If platform tools are missing, commands should explain the missing tool and next step instead of failing mysteriously.
- The production readiness gate may fail at production level until final art/audio/payment/backend work is complete; this is expected and should not be hidden.
