# Moon Jar Stories Agent Map

This file is the short orientation map. Keep detailed guidance in `docs/`.

## First 5 Minutes

1. Read `README.md`.
2. Read `docs/README.md`.
3. Run `scripts/agent/doctor`.
4. For non-trivial work, create or update an ExecPlan in `docs/exec-plans/active/`.
5. Before finishing, run `scripts/agent/validate` or explain exactly why it could not run.

## Repo Shape

| Area | Path | Notes |
| --- | --- | --- |
| Shared content | `shared-content/` | Canonical catalog, stories, schemas, assets, audio, manifests. |
| iOS app | `ios/MoonJarStoriesiOS/` | SwiftPM SwiftUI prototype. |
| Android app | `android/` | Kotlin + Jetpack Compose Gradle app. |
| Backend stub/API | `backend/` | Local Python stub plus OpenAPI contract. |
| Product tooling | `tools/` | Asset/content generation and validation. |
| Agent harness | `scripts/agent/` | Local commands for doctor/test/lint/validate/start/smoke/garden. |
| Docs | `docs/` | Architecture, plans, security, reliability, product, quality. |

## Commands

| Goal | Command |
| --- | --- |
| Inspect local setup | `scripts/agent/doctor` |
| Run tests/build checks | `scripts/agent/test` |
| Run docs/architecture checks | `scripts/agent/lint` |
| Before-PR validation | `scripts/agent/validate` |
| Full UI/smoke validation | `scripts/agent/validate-ui` |
| Start backend stub with logs | `scripts/agent/start backend` |
| Smoke test local backend | `scripts/agent/smoke backend` |
| Smoke test iOS simulator | `scripts/agent/smoke ios` |
| Smoke test Android emulator/device | `scripts/agent/smoke android` |
| Garden docs/tech debt | `scripts/agent/garden` |

## Planning Rule

Use an ExecPlan for complex features, refactors, production pipeline changes, app-flow rewrites, or anything that may span multiple turns. See `docs/PLANS.md`.

## Source of Truth

- Story and asset truth lives in `shared-content/`.
- Native apps should render shared content; do not fork story text into app code.
- Asset status must stay honest: generated drafts and synthetic narration are not final.
- If unsure, inspect files and run harness commands instead of guessing.

## Safety

- Do not commit secrets or API keys.
- Do not add live AI generation inside the child app.
- Do not add ads, tracking, child accounts, or child-facing external links.
- Keep temp artifacts under `.agent/tmp/`.

More detail: `docs/ARCHITECTURE.md`, `docs/RELIABILITY.md`, `docs/SECURITY.md`, and `docs/PRODUCT_SENSE.md`.
