# Tech Debt Tracker

Use this file for recurring cleanup notes discovered by agents.

## Current Debt

- Native UI automation and screenshot QA are still mostly manual.
- Production backend/CMS is contract-only.
- StoreKit 2 and Google Play Billing are scaffolded but not wired to real product IDs or server verification.
- Generated-draft story art and synthetic narration are not final.
- Real layered animation image assets are not present.

## Proposed Cleanup Tasks

- Add XCTest/Compose UI tests for reader navigation, Real Book Mode, language toggle, and narration controls.
- Add CI jobs for Android build and macOS iOS build when runners are available.
- Add schema validation for every asset/audio manifest entry.
- Add a production asset review dashboard or admin import workflow.

## Stale Docs

- Check product/design/status reports whenever generated-draft assets are replaced with reviewed/final assets.

## Flaky Tests

- None recorded yet.

## Architecture Drift

- Watch for story text or asset metadata copied into native app source.
- Watch for live generation APIs entering child-facing app code.

## Garden Log

- 2026-05-07: Harness foundation created; initial debt categories added.
