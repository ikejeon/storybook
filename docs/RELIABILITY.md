# Reliability

## Startup

- Backend stub: `scripts/agent/start backend`
- iOS host build/test: `cd ios/MoonJarStoriesiOS && swift build && swift test`
- iOS simulator smoke: `scripts/agent/smoke ios`
- Android build: `cd android && ./gradlew assembleDebug`

The backend harness writes logs to `.agent/tmp/logs/backend.log`.

## Tests and Validation

Routine before-PR command:

```bash
scripts/agent/validate
```

Full app-feedback validation, when Xcode simulator and Android emulator/device are available:

```bash
scripts/agent/validate-ui
```

Existing product checks:

```bash
python3 tools/validate_books.py
python3 tools/validate_assets.py
python3 tools/validate_production_readiness.py --level generated-draft
```

Full existing local check:

```bash
tools/run_all_checks.sh
```

To include backend/iOS/Android smoke artifacts in the product check:

```bash
tools/run_all_checks.sh --with-smoke
```

## Smoke Checks

Backend smoke:

```bash
scripts/agent/start backend
scripts/agent/smoke backend
```

The smoke transcript is saved under `.agent/tmp/artifacts/`.

iOS simulator smoke:

```bash
scripts/agent/smoke ios
```

The iOS smoke command installs the SwiftUI app on an available iPad simulator, captures library/reader screenshots, and copies reader self-test JSON into `.agent/tmp/artifacts/`.

Android smoke, when an emulator/device is attached:

```bash
scripts/agent/smoke android
```

This builds the debug APK, installs it through `adb`, launches the app, and captures `.agent/tmp/artifacts/android-smoke-launch.png`. If no device is attached, the command fails with a clear blocker transcript instead of pretending Android was manually tested.

## Logging

- Local harness logs belong in `.agent/tmp/logs/`.
- Do not commit local logs, screenshots, videos, or smoke artifacts.
- Native app logging should avoid child data and secrets.

## Error Handling Expectations

- Validation failures should say what failed and how to fix it.
- Missing platform tools should be reported as environment blockers, not hidden.
- Production-readiness failures are expected until final production assets, payments, backend, and store packaging exist.

## Recovery

- Delete `.agent/tmp/` to reset local harness state.
- Re-run `scripts/agent/doctor` after installing Xcode, Android Studio/JDK, or Python updates.
- If backend port `8080` is busy, stop the process recorded in `.agent/tmp/backend.pid` or start the backend manually on another port and document the command used.
