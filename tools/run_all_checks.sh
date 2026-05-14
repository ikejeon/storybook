#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_SMOKE=0
if [[ "${1:-}" == "--with-smoke" ]]; then
  WITH_SMOKE=1
  shift
fi
if [[ "$#" -gt 0 ]]; then
  echo "Usage: tools/run_all_checks.sh [--with-smoke]" >&2
  exit 2
fi
if [[ -d /Applications/Xcode.app/Contents/Developer ]]; then
  export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
  SWIFT_CMD=(/usr/bin/xcrun swift)
else
  SWIFT_CMD=(swift)
fi

cd "$ROOT"
python3 tools/validate_books.py
python3 tools/validate_all_story_standard.py
python3 tools/validate_story_quality.py
python3 tools/score_story_writing.py
python3 tools/validate_cultural_authenticity.py
if [[ "$WITH_SMOKE" == "1" ]]; then
  scripts/agent/smoke backend
  scripts/agent/smoke ios
  scripts/agent/smoke android
  python3 tools/score_reader_experience.py --require-smoke-artifacts
else
  python3 tools/score_reader_experience.py
fi
python3 tools/score_art_experience.py
python3 tools/validate_story_specific_art.py
python3 tools/validate_story_asset_authenticity.py
python3 tools/validate_premium_asset_quality_parity.py
python3 tools/validate_premium_imagegen_sheets.py
python3 tools/validate_visual_system_readiness.py
python3 tools/validate_assets.py
python3 tools/validate_asset_status_crosswalk.py
if [[ "$WITH_SMOKE" == "1" ]]; then
  python3 tools/validate_visual_layout.py --strict
else
  python3 tools/validate_visual_layout.py
fi
python3 tools/validate_kids_safety.py
python3 tools/validate_payments_readiness.py
python3 tools/validate_non_human_readiness.py
python3 tools/score_backend_cms_readiness.py
python3 tools/validate_production_readiness.py --level generated-draft

cd "$ROOT/ios/MoonJarStoriesiOS"
"${SWIFT_CMD[@]}" build
"${SWIFT_CMD[@]}" test

cd "$ROOT/android"
./gradlew test
./gradlew assembleDebug
