# Agent Command Index

These commands are repo-local and require no root package manager.

| Agent name | Local command | What it does |
| --- | --- | --- |
| `agent:doctor` | `scripts/agent/doctor` | Prints detected stack, tools, and known commands. |
| `agent:test` | `scripts/agent/test` | Runs content, visual-system, Backend/CMS, generated-draft, SwiftPM host build/tests, and Android Gradle test/build checks. |
| `agent:lint` | `scripts/agent/lint` | Runs docs freshness and architecture/taste checks. |
| `agent:validate` | `scripts/agent/validate` | Runs lint plus test. Use before handing work back. |
| `agent:validate-ui` | `scripts/agent/validate-ui` | Runs full validation plus backend/iOS/Android smoke, artifact-backed reader scoring, and strict visual layout QA. |
| `agent:start` | `scripts/agent/start backend` | Starts the local Python backend stub and writes logs to `.agent/tmp/logs/backend.log`. |
| `agent:smoke` | `scripts/agent/smoke backend` | Hits backend catalog/assets/entitlement/CMS/admin endpoints, asserts response shape, and writes a transcript to `.agent/tmp/artifacts/`. |
| `agent:smoke ios` | `scripts/agent/smoke ios` | Builds/packages the SwiftUI app, launches an iPad simulator, captures reader screenshots, and verifies built-in self-test JSON. |
| `agent:smoke android` | `scripts/agent/smoke android` | Builds/installs the debug APK, launches it on an attached Android emulator/device, and captures a screenshot. |
| `agent:smoke all` | `scripts/agent/smoke all` | Runs backend smoke and iOS simulator smoke. |
| `agent:garden` | `scripts/agent/garden` | Prints docs/tech-debt/TODO follow-up report and writes it to `.agent/tmp/artifacts/garden-report.md`. |

Useful direct checks:

```bash
scripts/agent/check-docs
scripts/agent/check-architecture
```

Temporary artifacts belong under `.agent/tmp/` and are ignored.

Useful smoke artifacts:

```text
.agent/tmp/artifacts/backend-smoke-transcript.md
.agent/tmp/artifacts/ios-smoke-transcript.md
.agent/tmp/artifacts/ios-smoke-library.png
.agent/tmp/artifacts/ios-smoke-real-book-page3.png
.agent/tmp/artifacts/ios-smoke-reader-playback.png
.agent/tmp/artifacts/reader-real-book-self-test.json
.agent/tmp/artifacts/reader-playback-self-test.json
.agent/tmp/artifacts/android-smoke-transcript.md
.agent/tmp/artifacts/android-smoke-launch.png
```
