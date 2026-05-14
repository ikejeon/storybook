# Architecture

Moon Jar Stories is a native multi-platform storybook product with a shared content and asset engine.

## Detected Stack

| Layer | Stack | Path |
| --- | --- | --- |
| iOS/iPadOS app | SwiftPM, SwiftUI, AVFoundation-style narration support, StoreKit scaffolding | `ios/MoonJarStoriesiOS/` |
| Android app | Gradle, Kotlin, Jetpack Compose, Media3/ExoPlayer, Google Play Billing scaffolding | `android/` |
| Shared content | JSON catalog/books/schemas, character bibles, design tokens, manifests | `shared-content/` |
| Asset pipeline | Python scripts and local files; provider adapters without required secrets | `tools/` |
| Backend/CMS contract | OpenAPI plus local persistent Python HTTP stub | `backend/` |
| Agent harness | Dependency-free shell/Python commands | `scripts/agent/` |

## Module Map

- `shared-content/catalog.json`: catalog and lock/free metadata.
- `shared-content/books/*.json`: complete story content, page metadata, prompts, vocabulary, and story beats.
- `shared-content/assets/manifests/image_manifest.json`: best-available image candidates by status.
- `shared-content/audio/manifests/audio_manifest.json`: narration, UI sound, ambient, and story SFX candidates.
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/ContentLoader.swift`: iOS shared-content loading.
- `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/AssetManifests.swift`: iOS asset resolution.
- `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/data/ContentRepository.kt`: Android shared-content loading.
- `backend/service_stub.py`: local API and CMS workflow contract exerciser with `.agent/tmp/` review/import/purchase state.

## Dependency Direction Rules

These are conservative rules for future work:

1. `shared-content/` is canonical. Apps may read or bundle it; they must not fork story data into native source.
2. Native app code should depend on shared-content schemas/manifests, not on production tooling internals.
3. `tools/` may generate or validate shared content, but child-facing apps must not call image/TTS generation live.
4. `backend/` contracts may reference shared catalog and manifest shapes, but should not own child-facing story prose.
5. Docs and harness scripts may inspect all layers, but should avoid mutating production assets unless explicitly named as generation/import tools.

## Provisional Boundaries

The repo has a local Backend/CMS contract stub, but does not yet have a production CMS, deployed backend, real StoreKit/Google Play product configuration, or final asset CDN. Until those exist:

- Keep backend changes contract-first in `backend/openapi.yaml`.
- Keep payment behavior mocked unless real product IDs and validation services are provided.
- Keep final/reviewed asset status protected by manifests and validation.
- Keep local Backend/CMS state under `.agent/tmp/`; do not treat it as production persistence.

## Mechanical Checks

`scripts/agent/check-architecture` enforces lightweight invariants:

- no `.agent/tmp/` artifacts committed;
- no obvious secrets in tracked text files;
- required product/architecture docs exist;
- large source/docs files are flagged unless allowlisted; canonical story JSON, generated manifests, and bundled shared-content resources are data exceptions validated by product scripts;
- native app source should not embed long story prose that belongs in `shared-content/`;
- generated output directories stay out of committed docs unless intentionally tracked.

Errors include what failed, why it matters, how to fix it, and which doc to read.
