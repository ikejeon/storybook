# Agent Harness

The harness gives future agents a local, runnable way to inspect, validate, smoke-test, and garden the repo.

## Command Home

Commands live under `scripts/agent/`:

| Command | Purpose |
| --- | --- |
| `doctor` | Detect stack/tools and print known commands. |
| `test` | Run content, visual-system, Backend/CMS, generated-draft, and native build/test checks. |
| `lint` | Run docs and architecture/taste checks. |
| `validate` | Run lint + tests + generated-draft readiness. |
| `validate-ui` | Run full validation plus backend/iOS/Android smoke, require current smoke artifacts, and run strict visual layout QA. |
| `start backend` | Start the local backend stub and capture logs. |
| `smoke backend` | Hit backend catalog, entitlement, CMS export/readiness, admin review, and error-contract endpoints and write a transcript. |
| `smoke ios` | Build/package the SwiftUI app, launch an iPad simulator, capture screenshots, and assert reader self-tests. |
| `smoke android` | Build/install the debug APK, launch it on an attached Android device/emulator, and capture a screenshot. |
| `smoke all` | Run backend and iOS simulator smoke checks. |
| `garden` | Print docs/tech-debt/TODO follow-up report. |
| `check-docs` | Docs freshness and link checks. |
| `check-architecture` | Architecture/taste invariant checks. |

## Artifacts

Temporary output goes under `.agent/tmp/`:

- logs: `.agent/tmp/logs/`
- smoke artifacts: `.agent/tmp/artifacts/`
- process IDs: `.agent/tmp/*.pid`

These paths are ignored and should not be committed.

## Validation Levels

- Demo/generated-draft readiness should pass for routine development.
- Visual-system and Backend/CMS readiness checks should pass before claiming near-100 repo-local scores in those categories.
- Non-human readiness checks should pass before claiming repo-owned market, privacy, store metadata, payment product planning, or backend deployment planning gaps are closed.
- UI/smoke validation should pass before claiming Reader UX, Real Book Mode, Page Flip, or native app foundation improvements.
- Production readiness is expected to fail until final art/audio/payment/backend/store work is complete.

## Adding Checks

Add small, actionable checks first. A good check explains:

- what failed;
- why it matters;
- how to fix it;
- which doc to read.

Avoid checks that require paid SaaS, secrets, or fragile local state.

## CI

The lightweight workflow at `.github/workflows/agent-harness.yml` runs:

- `scripts/agent/doctor`
- `scripts/agent/lint`
- content and asset validation
- generated-draft readiness
- backend smoke
- Android `./gradlew test` and `./gradlew assembleDebug`
- SwiftPM host `swift test` on macOS

iOS simulator smoke remains a local/manual harness command because it requires an installed simulator runtime and is slower than the lightweight CI gate.
