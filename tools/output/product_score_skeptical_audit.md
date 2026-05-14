# Product Score Skeptical Audit

> Historical/non-evidence for current scoring: this audit is superseded by `tools/output/product_score_external_validation_audit.md`. It may identify claims to verify, but it must not be used as positive evidence for current scores.

Generated: 2026-05-11

Prior score documents and progress summaries are claims, not evidence. Scores must be based on current repo artifacts, command output, screenshots, manifest counts, and external/human review evidence.

## Evidence Hierarchy

- Tier 1: current source code, current manifests, current asset files, command outputs, screenshots/videos, test results, running app evidence, real store configuration files, and real backend deployment/config.
- Tier 2: schema files, generated reports based on current files, validation scripts, contact sheets, and asset status reports.
- Tier 3: docs, plans, product summaries, self-written claims, old scorecards, and prior progress summaries.

Docs did not raise any score in this audit. Tier 3 material was used only to identify claims that needed verification.

## Ignored As Non-Evidence

- `docs/exec-plans/active/product-score-audit.md`
- Previous numerical-change notes or score improvement notes
- Previous reviewer summaries and generated optimism summaries unless backed by current manifests, source, command output, screenshots, or external/human review evidence

## Skeptical Scorecard

Category: Concept score
Score: 86
Hard Cap: Historical value superseded by `tools/output/product_score_external_validation_audit.md`, which applies an external-validation cap.
Confidence: Medium
Evidence Used:
- `shared-content/catalog.json` contains 24 catalog entries, including 5 complete free books and 19 premium metadata-only books.
- `shared-content/books/*.json` contains complete bilingual story data for the 5 free books.
- iOS and Android source code expose library, detail, reader, locked premium metadata, and paywall/parent-gate demo flows.
- Current screenshots show a usable library and reader concept.
Files Inspected:
- `shared-content/catalog.json`
- `shared-content/books/sun_moon.json`
- `shared-content/books/gold_silver_axe.json`
- `shared-content/books/tiger_persimmon.json`
- `shared-content/books/heungbu_nolbu.json`
- `shared-content/books/red_bean_grandma.json`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`
Commands Run:
- `python3 -c "... catalog/manifests counts ..."`
- `sed -n '1,180p' ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/ContentLoader.swift`
- `sed -n '1,180p' android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/data/ContentRepository.kt`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
- `.agent/tmp/artifacts/ios-smoke-reader-playback.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`
Missing Evidence:
- No parent/customer interviews.
- No pricing validation.
- No retention, conversion, or distribution proof.
- No competitor/discoverability analysis backed by data.
What Would Raise It By 5 Points:
- Add target-family interview notes, pricing tests, and a competitor/distribution memo with source-backed findings.
What Would Raise It To 95:
- Show evidence of real demand: parent testing, willingness-to-pay signal, retention signal, distribution plan, and a demo that validates the value proposition with target families.

Category: Engineering/demo readiness
Score: 94
Hard Cap: No external-validation cap was appropriate because this category is limited to repo-local engineering/demo proof and is superseded by the current external-validation audit.
Confidence: High
Evidence Used:
- Current SwiftUI source loads shared content, resolves manifests, renders library/detail/reader/paywall, and plays packaged narration.
- Current Android Compose source loads shared content, resolves manifest assets, renders library/detail/reader/paywall, and plays packaged narration through Media3.
- `scripts/agent/validate` passed content, story, asset, layout, kids-safety, payments scaffold, backend readiness, SwiftPM build/tests, Android Gradle tests, and Android debug assemble.
- Simulator/emulator smoke artifacts exist for iOS and Android.
Files Inspected:
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/ContentLoader.swift`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/AssetManifests.swift`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/NarrationPlayer.swift`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/data/ContentRepository.kt`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/billing/AudioEngine.kt`
- `ios/MoonJarStoriesiOS/Tests/MoonJarStoriesiOSTests/SharedContentTests.swift`
- `android/MoonJarStoriesAndroid/src/test/java/com/moonjar/stories/data/SharedContentContractTest.kt`
Commands Run:
- `scripts/agent/doctor`
- `scripts/agent/validate`
- `python3 -m json.tool .agent/tmp/artifacts/reader-real-book-self-test.json`
- `python3 -m json.tool .agent/tmp/artifacts/reader-playback-self-test.json`
- `python3 -m json.tool .agent/tmp/artifacts/moonjar-android-self-test.json`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
- `.agent/tmp/artifacts/ios-smoke-real-book-page3.png`
- `.agent/tmp/artifacts/ios-smoke-reader-playback.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`
Missing Evidence:
- No current clean CI evidence for simulator/device smoke.
- Large reader files remain concentrated in one Swift file and one Compose file.
- Real-device QA is not documented.
What Would Raise It By 5 Points:
- Add repeatable CI or fresh command evidence for simulator/emulator UI smoke plus real-device smoke, and split large reader surfaces after behavior stabilizes.
What Would Raise It To 95:
- This category is close; fresh simulator/emulator smoke in the current audit plus minor test/maintainability tightening would make 95 fair.

Category: Content/story readiness
Score: 84
Hard Cap: Historical value superseded by `tools/output/product_score_external_validation_audit.md`, which applies an external-editor/reviewer cap.
Confidence: Medium
Evidence Used:
- Current story JSON contains 5 complete bilingual books with 138 total pages.
- Story pages include English/Korean text, little/standard variants, story beats, vocabulary, image prompts, audio prompts, and narration scripts.
- Current validation commands pass story/content shape checks.
Files Inspected:
- `shared-content/catalog.json`
- `shared-content/books/sun_moon.json`
- `shared-content/books/gold_silver_axe.json`
- `shared-content/books/tiger_persimmon.json`
- `shared-content/books/heungbu_nolbu.json`
- `shared-content/books/red_bean_grandma.json`
- `shared-content/schemas/book.schema.json`
- `tools/validate_books.py`
- `tools/validate_story_quality.py`
Commands Run:
- `python3 -c "... print first story pages ..."`
- `scripts/agent/validate`
Screenshots/Contact Sheets Reviewed:
- None required for story text scoring.
Missing Evidence:
- No external children's editor signoff.
- No external Korean-language reviewer signoff.
- No external Korean cultural authenticity approval.
- 19 premium books are metadata-only, not complete story content.
What Would Raise It By 5 Points:
- Add external editor/Korean reviewer comments and resolve their required changes for the 5 complete books.
What Would Raise It To 95:
- Complete human editorial, Korean-language, cultural, and child-safety review with documented approvals and any required revisions applied.

Category: Visual/art readiness
Score: 70
Hard Cap: 75 because all complete-scene art is `generated_draft`
Confidence: High
Evidence Used:
- `shared-content/assets/manifests/image_manifest.json` shows 138 complete-scene entries with status `generated_draft`.
- The same manifest shows 5 complete-book covers with status `generated_draft`.
- Current sampled art files render and are demo-credible, but they are not reviewed or final assets.
- Current iOS screenshots show fit-safe reader rendering with draft art.
Files Inspected:
- `shared-content/assets/manifests/image_manifest.json`
- `shared-content/assets/generated-draft/images/scenes/sun-and-moon/page-001.png`
- `shared-content/assets/generated-draft/images/scenes/sun-and-moon/page-014.png`
- `shared-content/assets/generated-draft/images/scenes/tiger-and-persimmon/page-004.png`
- `shared-content/assets/generated-draft/images/scenes/gold-axe-silver-axe/page-001.png`
- `shared-content/assets/generated-draft/images/scenes/heungbu-and-nolbu/page-010.png`
- `shared-content/assets/generated-draft/images/scenes/red-bean-porridge-grandma/page-006.png`
- `shared-content/assets/generated-draft/images/covers/sun-and-moon.png`
Commands Run:
- `python3 -c "... scene_statuses/cover_statuses ..."`
- `file shared-content/assets/generated-draft/images/scenes/sun-and-moon/page-001.png`
- `scripts/agent/validate`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-real-book-page3.png`
- `.agent/tmp/artifacts/ios-smoke-reader-playback.png`
- `tools/output/sun_moon_32_scene_contact_sheet.html`
- `tools/output/sun_moon_approval_anchors_contact_sheet.html`
Missing Evidence:
- No `commissioned_final` scene art.
- No full set of `generated_reviewed` or `commissioned_reviewed` scene art.
- No final approved character pack.
- No human creative/cultural/child-safety approval for all runtime art.
- No licensing/ownership evidence for final production art.
What Would Raise It By 5 Points:
- Review and approve a meaningful subset of the generated draft scenes with written creative/cultural/child-safety findings, then fix defects.
What Would Raise It To 95:
- All 138 scene images and 5 covers are reviewed/final, character consistency is approved, cropping/continuity defects are resolved, and production ownership/licensing is documented.

Category: Audio readiness
Score: 45
Hard Cap: 55 because all narration is `synthetic_draft`
Confidence: High
Evidence Used:
- `shared-content/audio/manifests/audio_manifest.json` shows 276 narration entries with status `synthetic_draft`.
- The manifest contains 138 English and 138 Korean narration entries.
- Sample WAV files are mono 22050 Hz PCM generated draft assets.
- Voice bakeoff evidence shows only local baseline samples; no configured cloud/provider synthesis or reviewed provider samples.
Files Inspected:
- `shared-content/audio/manifests/audio_manifest.json`
- `shared-content/audio/manifests/voice_bakeoff_manifest.json`
- `shared-content/audio/synthetic-draft/narration/sun-and-moon/en/page-001.wav`
- `shared-content/audio/synthetic-draft/narration/sun-and-moon/ko/page-001.wav`
- `tools/generate_audio.py`
- `tools/providers/macos_say.py`
Commands Run:
- `python3 -c "... narration_statuses/narration_languages ..."`
- `file shared-content/audio/synthetic-draft/narration/sun-and-moon/en/page-001.wav`
- `file shared-content/audio/synthetic-draft/narration/sun-and-moon/ko/page-001.wav`
- `afinfo shared-content/audio/synthetic-draft/narration/sun-and-moon/en/page-001.wav`
- `afinfo shared-content/audio/synthetic-draft/narration/sun-and-moon/ko/page-001.wav`
Screenshots/Contact Sheets Reviewed:
- None applicable.
Missing Evidence:
- No professional narrator files.
- No human-recorded reviewed or final narration.
- No reviewed high-quality synthetic provider samples.
- No Korean pronunciation/pacing approval.
- No mastered final audio QA.
What Would Raise It By 5 Points:
- Generate real provider samples for English and Korean and get a reviewer to compare warmth, pronunciation, pacing, and child suitability.
What Would Raise It To 95:
- Final mastered English and Korean narration are approved, pronunciation and pacing are reviewed, sound design is final/licensed, and device audio QA passes.

Category: Payment readiness
Score: 58
Hard Cap: 75 because real StoreKit and Google Play Billing product configuration is absent
Confidence: High
Evidence Used:
- iOS source imports StoreKit, defines product IDs, calls `Product.products`, and restores from `Transaction.currentEntitlements`.
- Android has Play Billing dependency and entitlement/product ID scaffolding, but no real BillingClient purchase flow implementation in source.
- Current tests cover prototype entitlement gating and product ID formation.
Files Inspected:
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/EntitlementStore.swift`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/billing/EntitlementManager.kt`
- `android/MoonJarStoriesAndroid/build.gradle.kts`
- `ios/MoonJarStoriesiOS/Tests/MoonJarStoriesiOSTests/EntitlementStoreTests.swift`
- `android/MoonJarStoriesAndroid/src/test/java/com/moonjar/stories/billing/EntitlementManagerTest.kt`
Commands Run:
- `rg -n "StoreKit|BillingClient|Product\\.products|Transaction\\.currentEntitlements|restorePurchasesPlaceholder" ios android backend tools shared-content`
- `find ios android backend -maxdepth 5 -type f -name '*.storekit' -o -name '*.xcconfig' -o -name 'Info.plist'`
- `scripts/agent/validate`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
Missing Evidence:
- No `.storekit` configuration file.
- No App Store Connect product evidence.
- No Google Play Console product evidence.
- No Android BillingClient purchase flow implementation evidence.
- No sandbox purchase/restore evidence.
- No receipt/token verification backend integration.
What Would Raise It By 5 Points:
- Add real StoreKit configuration and Android BillingClient purchase/restore implementation with sandbox tests.
What Would Raise It To 95:
- Real iOS and Android store products are configured, purchase/restore flows pass sandbox/internal-track testing, parent gates are verified, and receipt/token verification is integrated with backend entitlements.

Category: Backend readiness
Score: 69
Hard Cap: 75 because backend evidence is OpenAPI/local stub only
Confidence: High
Evidence Used:
- `backend/service_stub.py` implements local catalog, assets manifest, entitlement check, purchase sync, review queue, CMS export, and release readiness endpoints.
- Backend smoke transcript shows local responses and explicitly reports local stub mode plus final-art/audio/backend blockers.
- `backend/openapi.yaml` defines the contract for catalog, entitlements, purchases, manifests, CMS export, and review workflows.
Files Inspected:
- `backend/service_stub.py`
- `backend/openapi.yaml`
- `.agent/tmp/artifacts/backend-smoke-transcript.md`
Commands Run:
- `sed -n '1,260p' backend/service_stub.py`
- `sed -n '260,560p' backend/service_stub.py`
- `sed -n '1,260p' backend/openapi.yaml`
- `sed -n '1,220p' .agent/tmp/artifacts/backend-smoke-transcript.md`
Screenshots/Contact Sheets Reviewed:
- None applicable.
Missing Evidence:
- No deployed backend URL/config beyond example placeholders.
- No durable database/migration evidence.
- No production auth/RBAC evidence.
- No receipt/token verification implementation.
- No monitoring, audit log, alerting, or operational runbook evidence.
- No CMS UI evidence.
What Would Raise It By 5 Points:
- Add a staging deployment with persistent storage and smoke tests that hit the deployed service.
What Would Raise It To 95:
- Deployed entitlement/catalog/purchase sync service exists with receipt/token verification, durable persistence, admin auth/workflows, monitoring, audit logs, security review, and production operations evidence.

Category: Compliance readiness
Score: 78
Hard Cap: Historical value superseded by `tools/output/product_score_external_validation_audit.md`, which applies privacy/legal/store evidence caps.
Confidence: Medium
Evidence Used:
- `shared-content/compliance/app_behavior_flags.json` disables ads, third-party tracking, child accounts, child-facing external links, child data collection, live image generation, and live TTS generation.
- Current iOS/Android source scan found no ad SDKs, analytics SDKs, web views, location permissions, or microphone permission requests in the child app code.
- Parent gates exist around prototype purchase/restore flows.
- `tools/validate_kids_safety.py` passed in `scripts/agent/validate`.
Files Inspected:
- `shared-content/compliance/app_behavior_flags.json`
- `tools/validate_kids_safety.py`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`
- `android/MoonJarStoriesAndroid/src/main/AndroidManifest.xml`
Commands Run:
- `rg -n "Firebase|Analytics|AdMob|tracking|ACCESS_FINE_LOCATION|RECORD_AUDIO|WebView" ios android shared-content backend tools`
- `sed -n '1,160p' android/MoonJarStoriesAndroid/src/main/AndroidManifest.xml`
- `scripts/agent/validate`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`
Missing Evidence:
- No final privacy policy file.
- No legal review signoff.
- No Apple Kids Category or Google Play Families review evidence.
- No accessibility QA evidence.
- No store privacy-label evidence.
What Would Raise It By 5 Points:
- Add a final privacy policy and external legal/store compliance review with issues resolved.
What Would Raise It To 95:
- Legal/privacy/store signoff is complete, parent gates are QA'd, accessibility and age-appropriateness testing are complete, and all third-party/provider data flows are reviewed and disclosed.

Category: Store readiness
Score: 38
Hard Cap: 50 because store evidence is incomplete
Confidence: High
Evidence Used:
- iOS production xcconfig contains a plausible bundle ID and production backend placeholder, but no signing/team evidence.
- Android debug APK can assemble, but no release signing or store metadata evidence was found.
- Search found no `.storekit` config, no Play product config, no privacy policy, and no store screenshot/metadata package.
Files Inspected:
- `ios/MoonJarStoriesiOSApp/Config/Production.xcconfig`
- `ios/MoonJarStoriesiOSApp/MoonJarStories/Info.plist`
- `android/MoonJarStoriesAndroid/build.gradle.kts`
- `android/MoonJarStoriesAndroid/src/main/AndroidManifest.xml`
Commands Run:
- `find ios android backend -maxdepth 5 -type f -name '*.storekit' -o -name '*.xcconfig' -o -name 'Info.plist'`
- `find . -maxdepth 4 -type f -iname '*privacy*' -o -iname '*screenshot*' -o -iname '*metadata*' -o -iname '*store*' -o -iname '*release*'`
- `scripts/agent/validate`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`
Missing Evidence:
- No signing/provisioning/team evidence.
- No final app icon/launch asset set for store submission.
- No store screenshots/metadata package.
- No privacy policy or privacy labels.
- No subscription disclosures.
- No configured store products.
- No TestFlight/internal-track QA evidence.
What Would Raise It By 5 Points:
- Add real signing/release config, privacy policy, store metadata, screenshot set, and store product configuration evidence.
What Would Raise It To 95:
- App Store and Play submission packages are complete with signing, store products, screenshots, metadata, privacy labels, subscription disclosures, compliance review, and TestFlight/internal-track QA evidence.

Category: Production readiness
Score: 55
Hard Cap: 70 because final/reviewed art is missing for complete scenes
Confidence: High
Evidence Used:
- Current manifests show all 138 complete-scene images are `generated_draft`.
- Current manifests show all 276 narration entries are `synthetic_draft`.
- Backend evidence is a local persistent stub, not a deployed production service.
- Store evidence is scaffold-level and missing signing/products/metadata.
- Compliance guardrails are strong in source/config, but legal/store review is not present.
- `scripts/agent/validate` passes generated-draft readiness and warns that no scene images are final and no narration files are human-recorded final.
Files Inspected:
- `shared-content/assets/manifests/image_manifest.json`
- `shared-content/audio/manifests/audio_manifest.json`
- `backend/service_stub.py`
- `backend/openapi.yaml`
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/EntitlementStore.swift`
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/billing/EntitlementManager.kt`
- `ios/MoonJarStoriesiOSApp/Config/Production.xcconfig`
- `android/MoonJarStoriesAndroid/build.gradle.kts`
Commands Run:
- `python3 -c "... current manifest counts ..."`
- `scripts/agent/validate`
- `sed -n '1,220p' .agent/tmp/artifacts/backend-smoke-transcript.md`
Screenshots/Contact Sheets Reviewed:
- `.agent/tmp/artifacts/ios-smoke-library.png`
- `.agent/tmp/artifacts/ios-smoke-real-book-page3.png`
- `.agent/tmp/artifacts/ios-smoke-reader-playback.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`
- `tools/output/sun_moon_32_scene_contact_sheet.html`
Missing Evidence:
- No reviewed/final complete-scene art.
- No final covers.
- No professional or human-reviewed narration.
- No final sound design.
- No real store product configuration or purchase testing.
- No deployed receipt/token verification backend.
- No legal/privacy/store compliance signoff.
- No real-device/accessibility QA evidence.
- No store packaging/signing/listing evidence.
What Would Raise It By 5 Points:
- Convert one major blocker from draft/scaffold to reviewed operational evidence, such as reviewed art for all complete scenes or real provider narration samples with approval.
What Would Raise It To 95:
- Final/reviewed art, final/pro narration, final sound design, real StoreKit/Google Play Billing, deployed receipt/token verification backend, hosted CMS/backend, legal/privacy/compliance signoff, real-device/accessibility QA, and store packaging/signing/listings/screenshots are all complete and proven by current evidence.

## Hard Caps Applied

- Visual/art readiness is capped at 75 because all complete-scene art is `generated_draft`.
- Audio readiness is capped at 55 because all narration is `synthetic_draft`.
- Payment readiness is capped at 75 because real store product configuration and purchase-flow evidence are missing.
- Backend readiness is capped at 75 because backend evidence is OpenAPI/local stub only.
- Store readiness is capped at 50 because store evidence is incomplete.
- Production readiness is capped at 70 because final/reviewed art is missing for complete scenes; additional blockers keep the fair score well below that cap.

## 95 Status

- 95 is currently plausible only for engineering/demo readiness after fresh UI smoke evidence and small maintainability tightening.
- Production readiness cannot honestly be 95 right now.
- Store readiness cannot honestly be 95 right now.
- Visual/art, audio, payment, backend, and compliance readiness cannot honestly be 95 right now because required proof is missing.
