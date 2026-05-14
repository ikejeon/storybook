#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
AGENT_TMP = ROOT / ".agent" / "tmp"
LOG_DIR = AGENT_TMP / "logs"
ARTIFACT_DIR = AGENT_TMP / "artifacts"
BACKEND_PID = AGENT_TMP / "backend.pid"
BACKEND_LOG = LOG_DIR / "backend.log"
IOS_BUNDLE_ID = "com.moonjar.stories.demo"
ANDROID_PACKAGE_ID = "com.moonjar.stories"

REQUIRED_DOCS = [
    "docs/README.md",
    "docs/ARCHITECTURE.md",
    "docs/HARNESS.md",
    "docs/PLANS.md",
    "docs/RELIABILITY.md",
    "docs/SECURITY.md",
    "docs/PRODUCT_SENSE.md",
    "docs/design-docs/index.md",
    "docs/exec-plans/tech-debt-tracker.md",
]

REQUIRED_EXECPLAN_HEADINGS = [
    "Purpose / Big Picture",
    "Progress",
    "Surprises & Discoveries",
    "Decision Log",
    "Outcomes & Retrospective",
    "Context and Orientation",
    "Plan of Work",
    "Concrete Steps",
    "Validation and Acceptance",
    "Idempotence and Recovery",
]

SKIP_DIRS = {
    ".git",
    ".agent/tmp",
    "android/.gradle",
    "android/.kotlin",
    "android/MoonJarStoriesAndroid/build",
    "build",
    "ios/MoonJarStoriesiOS/.build",
    "ios/MoonJarStoriesiOS/.swiftpm",
    "tools/output",
}

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".sh",
    ".swift",
    ".kt",
    ".kts",
    ".toml",
    ".xml",
    ".plist",
    ".xcconfig",
    ".gradle",
}

FILE_SIZE_ALLOWLIST = {
    "ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift": "Known large demo reader surface; split after UI stabilizes.",
    "android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt": "Known large Compose demo reader surface; split after UI stabilizes.",
}

FILE_SIZE_ALLOWLIST_PREFIXES = {
    "shared-content/books/": "Canonical story data can be large; validate shape with tools/validate_books.py.",
    "shared-content/assets/manifests/": "Generated asset manifests can be large; validate shape with tools/validate_assets.py.",
    "shared-content/audio/manifests/": "Generated audio manifests can be large; validate shape with tools/validate_assets.py.",
    "shared-content/animation/": "Layer plans are data files; validate shape with tools/validate_assets.py.",
    "ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Resources/shared-content/": "Bundled copy of canonical shared content for SwiftPM demo app.",
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str = ""


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_tmp() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def is_in_skipped_dir(path: Path) -> bool:
    relative = rel(path)
    return any(relative == item or relative.startswith(item + "/") for item in SKIP_DIRS)


def iter_repo_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if path.is_file() and not is_in_skipped_dir(path):
            yield path


def is_text_file(path: Path) -> bool:
    if path.name in {".gitignore", ".env.example"}:
        return True
    return path.suffix in TEXT_SUFFIXES


def file_size_allowlist_reason(relative: str) -> str | None:
    if relative in FILE_SIZE_ALLOWLIST:
        return FILE_SIZE_ALLOWLIST[relative]
    for prefix, reason in FILE_SIZE_ALLOWLIST_PREFIXES.items():
        if relative.startswith(prefix):
            return reason
    return None


def which(name: str) -> str:
    return shutil.which(name) or "missing"


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def run_command(name: str, cmd: list[str], cwd: Path = ROOT, required: bool = True) -> CheckResult:
    print(f"\n$ {' '.join(cmd)}")
    print(f"cwd: {rel(cwd)}")
    try:
        completed = subprocess.run(cmd, cwd=cwd, check=False)
    except FileNotFoundError:
        message = f"{cmd[0]} is missing. Install it or read docs/HARNESS.md."
        print(f"FAIL: {message}")
        return CheckResult(name, not required, message)
    if completed.returncode == 0:
        print(f"PASS: {name}")
        return CheckResult(name, True)
    message = f"command exited {completed.returncode}"
    print(f"FAIL: {name}: {message}")
    return CheckResult(name, False, message)


def swift_command(*args: str) -> list[str]:
    xcode_developer_dir = Path("/Applications/Xcode.app/Contents/Developer")
    if xcode_developer_dir.exists():
        return ["/usr/bin/env", f"DEVELOPER_DIR={xcode_developer_dir}", "/usr/bin/xcrun", "swift", *args]
    return ["swift", *args]


def summarize(results: list[CheckResult]) -> int:
    print_header("Summary")
    failed = [item for item in results if not item.ok]
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        suffix = f" - {item.details}" if item.details else ""
        print(f"{status}: {item.name}{suffix}")
    if failed:
        print(f"\n{len(failed)} check(s) failed. Read the failure text above; it is written for future agents.")
        return 1
    print("\nAll requested harness checks passed.")
    return 0


def doctor(_: argparse.Namespace) -> int:
    print_header("Detected Stack")
    rows = [
        ("root package manager", "none detected"),
        ("iOS", "SwiftPM at ios/MoonJarStoriesiOS/Package.swift"),
        ("Android", "Gradle wrapper at android/gradlew"),
        ("Python tooling", "tools/*.py and backend/service_stub.py"),
        ("shared content", "shared-content/catalog.json and shared-content/books/*.json"),
        ("CI", ".github/workflows if present"),
    ]
    for key, value in rows:
        print(f"{key}: {value}")

    print_header("Tool Availability")
    for name in ["python3", "swift", "java", "xcodebuild", "curl", "git"]:
        print(f"{name}: {which(name)}")
    gradlew = ROOT / "android" / "gradlew"
    print(f"android gradlew: {'present' if gradlew.exists() else 'missing'}")

    print_header("Known Commands")
    print("doctor: scripts/agent/doctor")
    print("lint: scripts/agent/lint")
    print("test: scripts/agent/test")
    print("validate: scripts/agent/validate")
    print("start backend: scripts/agent/start backend")
    print("smoke backend: scripts/agent/smoke backend")
    print("smoke ios: scripts/agent/smoke ios")
    print("smoke android: scripts/agent/smoke android")
    print("smoke all: scripts/agent/smoke all")
    print("garden: scripts/agent/garden")
    print("full existing product check: tools/run_all_checks.sh")
    return 0


def docs_errors() -> list[str]:
    errors: list[str] = []
    for item in REQUIRED_DOCS:
        if not (ROOT / item).exists():
            errors.append(f"Missing required doc `{item}`. Create it or update scripts/agent/agent_harness.py if the doc moved. Read docs/README.md.")

    agents = ROOT / "AGENTS.md"
    if not agents.exists():
        errors.append("Missing AGENTS.md. Future agents need a short repo map.")
    else:
        text = agents.read_text(encoding="utf-8")
        for token in ["docs/README.md", "scripts/agent/doctor", "docs/PLANS.md", "shared-content/"]:
            if token not in text:
                errors.append(f"AGENTS.md does not mention `{token}`. Add the link/command so future agents can orient quickly.")

    docs_readme = ROOT / "docs" / "README.md"
    if docs_readme.exists():
        text = docs_readme.read_text(encoding="utf-8")
        for item in REQUIRED_DOCS:
            name = Path(item).name
            if name not in text and item not in text:
                errors.append(f"docs/README.md does not link or name `{item}`. Keep the docs map authoritative.")

    active_dir = ROOT / "docs" / "exec-plans" / "active"
    completed_dir = ROOT / "docs" / "exec-plans" / "completed"
    if not active_dir.is_dir():
        errors.append("Missing docs/exec-plans/active/. Active ExecPlans need a predictable home.")
    if not completed_dir.is_dir():
        errors.append("Missing docs/exec-plans/completed/. Completed ExecPlans need a predictable home.")

    if active_dir.is_dir():
        for plan in sorted(active_dir.glob("*.md")):
            text = plan.read_text(encoding="utf-8")
            for heading in REQUIRED_EXECPLAN_HEADINGS:
                if f"## {heading}" not in text:
                    errors.append(f"{rel(plan)} is missing ExecPlan heading `## {heading}`. Read docs/PLANS.md.")

    errors.extend(markdown_link_errors())
    errors.extend(tracked_temp_errors())
    return errors


def markdown_link_errors() -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in iter_repo_files():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in link_pattern.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = target.split("#", 1)[0].strip()
            if not target:
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if " " in target and not Path(target).suffix:
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                continue
            if not candidate.exists():
                errors.append(f"Broken markdown link in {rel(path)} -> `{target}`. Fix the link or create the target.")
    return errors


def git_tracked(paths: list[str]) -> list[str]:
    if not (ROOT / ".git").exists() or which("git") == "missing":
        return []
    completed = subprocess.run(["git", "ls-files", *paths], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def tracked_temp_errors() -> list[str]:
    tracked = git_tracked([".agent/tmp", "build", "android/.gradle", "ios/MoonJarStoriesiOS/.build"])
    errors = [
        f"Generated/temp artifact `{item}` is tracked. Remove it from version control and keep it ignored. Read docs/HARNESS.md."
        for item in tracked
    ]
    if not (ROOT / ".git").exists():
        generated_dirs = [
            ".agent/tmp",
            "build",
            "android/.gradle",
            "android/MoonJarStoriesAndroid/build",
            "ios/MoonJarStoriesiOS/.build",
        ]
        for item in generated_dirs:
            path = ROOT / item
            if path.exists() and any(path.iterdir()):
                print(
                    f"WARN: `{item}` is non-empty, but this workspace has no .git metadata, "
                    "so the harness cannot verify whether generated artifacts are tracked."
                )
    return errors


def check_docs(_: argparse.Namespace) -> int:
    print_header("Docs Freshness Check")
    errors = docs_errors()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: docs map, ExecPlans, links, and temp artifact hygiene look good.")
    return 0


def architecture_errors() -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []

    for item in REQUIRED_DOCS:
        if not (ROOT / item).exists():
            errors.append(f"Required architecture doc `{item}` is missing. Future agents lose context. Read docs/README.md.")

    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{20,}"
    )
    live_ai_pattern = re.compile(r"(?i)(api\.openai\.com|elevenlabs|clova|firefly|text-to-speech)")
    story_phrase_pattern = re.compile(r"(?i)(once upon a time|옛날 옛적|옛날 옛날)")

    for path in iter_repo_files():
        relative = rel(path)
        if not is_text_file(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name != ".env.example" and secret_pattern.search(text):
            errors.append(
                f"Possible secret in `{relative}`. Secrets do not belong in the repo; move real values to local env and keep only names in .env.example. Read docs/SECURITY.md."
            )
        line_count = text.count("\n") + 1
        allowlist_reason = file_size_allowlist_reason(relative)
        if line_count > 1800 and allowlist_reason is None:
            errors.append(
                f"`{relative}` has {line_count} lines. Large files are hard for agents to review. Split it or add a narrow allowlist reason in scripts/agent/agent_harness.py. Read docs/ARCHITECTURE.md."
            )
        elif line_count > 1800:
            warnings.append(f"WARN: `{relative}` has {line_count} lines and is allowlisted: {allowlist_reason}")

        if relative.startswith(("ios/", "android/")) and "/Resources/shared-content/" not in relative:
            if path.suffix in {".swift", ".kt", ".kts"} and story_phrase_pattern.search(text):
                errors.append(
                    f"Possible story prose duplicated in native source `{relative}`. Keep stories in shared-content and load them in apps. Read docs/ARCHITECTURE.md."
                )
            if path.suffix in {".swift", ".kt", ".kts"} and live_ai_pattern.search(text):
                errors.append(
                    f"Possible live generation provider reference in child app source `{relative}`. Asset generation must be offline/dev-time only. Read docs/SECURITY.md."
                )

    if (ROOT / ".agent" / "tmp").exists() and any((ROOT / ".agent" / "tmp").rglob("*")):
        tracked = git_tracked([".agent/tmp"])
        if tracked:
            errors.append("Tracked files exist under `.agent/tmp/`. Remove them from version control. Read docs/HARNESS.md.")

    errors.extend(shared_content_bundle_errors())
    for warning in warnings:
        print(warning)
    return errors


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shared_content_bundle_errors() -> list[str]:
    errors: list[str] = []
    source_root = ROOT / "shared-content"
    bundle_root = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "Resources" / "shared-content"
    if not bundle_root.exists():
        errors.append("iOS bundled shared-content is missing. Sync canonical shared-content into the SwiftPM resource bundle. Read docs/ARCHITECTURE.md.")
        return errors

    excluded_prefixes = {"assets/manual-import"}
    source_files = {
        path.relative_to(source_root).as_posix(): path
        for path in source_root.rglob("*")
        if path.is_file() and not any(path.relative_to(source_root).as_posix().startswith(prefix + "/") for prefix in excluded_prefixes)
    }
    bundle_files = {
        path.relative_to(bundle_root).as_posix(): path
        for path in bundle_root.rglob("*")
        if path.is_file()
    }
    missing = sorted(set(source_files) - set(bundle_files))
    extra = sorted(set(bundle_files) - set(source_files))
    changed = sorted(
        relative
        for relative in set(source_files) & set(bundle_files)
        if file_hash(source_files[relative]) != file_hash(bundle_files[relative])
    )

    if missing or extra or changed:
        summary = []
        if missing:
            summary.append(f"missing {len(missing)}")
        if extra:
            summary.append(f"extra {len(extra)}")
        if changed:
            summary.append(f"changed {len(changed)}")
        sample = (missing + extra + changed)[:8]
        errors.append(
            "iOS bundled shared-content is stale compared with canonical shared-content "
            f"({', '.join(summary)}). Run `rsync -a --delete --exclude 'assets/manual-import/' shared-content/ "
            "ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Resources/shared-content/`. "
            f"Sample drift: {sample}. Read docs/ARCHITECTURE.md."
        )
    return errors


def check_architecture(_: argparse.Namespace) -> int:
    print_header("Architecture / Taste Check")
    errors = architecture_errors()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: architecture/taste invariants look good.")
    return 0


def lint(_: argparse.Namespace) -> int:
    results = [
        CheckResult("check-docs", check_docs(argparse.Namespace()) == 0),
        CheckResult("check-architecture", check_architecture(argparse.Namespace()) == 0),
    ]
    return summarize(results)


def test(_: argparse.Namespace) -> int:
    results: list[CheckResult] = []
    results.append(run_command("validate_books", ["python3", "tools/validate_books.py"]))
    results.append(run_command("validate_all_story_standard", ["python3", "tools/validate_all_story_standard.py"]))
    results.append(run_command("validate_story_quality", ["python3", "tools/validate_story_quality.py"]))
    results.append(run_command("score_story_writing", ["python3", "tools/score_story_writing.py"]))
    results.append(run_command("validate_cultural_authenticity", ["python3", "tools/validate_cultural_authenticity.py"]))
    results.append(run_command("score_reader_experience", ["python3", "tools/score_reader_experience.py"]))
    results.append(run_command("score_art_experience", ["python3", "tools/score_art_experience.py"]))
    results.append(run_command("validate_story_specific_art", ["python3", "tools/validate_story_specific_art.py"]))
    results.append(run_command("validate_story_asset_authenticity", ["python3", "tools/validate_story_asset_authenticity.py"]))
    results.append(run_command("validate_premium_asset_quality_parity", ["python3", "tools/validate_premium_asset_quality_parity.py"]))
    results.append(run_command("validate_visual_system_readiness", ["python3", "tools/validate_visual_system_readiness.py"]))
    results.append(run_command("validate_assets", ["python3", "tools/validate_assets.py"]))
    results.append(run_command("validate_asset_status_crosswalk", ["python3", "tools/validate_asset_status_crosswalk.py"]))
    results.append(run_command("validate_visual_layout", ["python3", "tools/validate_visual_layout.py"]))
    results.append(run_command("validate_kids_safety", ["python3", "tools/validate_kids_safety.py"]))
    results.append(run_command("validate_payments_readiness", ["python3", "tools/validate_payments_readiness.py"]))
    results.append(run_command("validate_non_human_readiness", ["python3", "tools/validate_non_human_readiness.py"]))
    results.append(run_command("score_backend_cms_readiness", ["python3", "tools/score_backend_cms_readiness.py"]))
    results.append(
        run_command(
            "generated-draft readiness",
            ["python3", "tools/validate_production_readiness.py", "--level", "generated-draft"],
        )
    )
    results.append(
        run_command(
            "scorecard truthfulness",
            ["python3", "tools/validate_scorecard_truthfulness.py", "tools/output/product_score_external_validation_audit.md"],
        )
    )
    if which("swift") != "missing" or Path("/Applications/Xcode.app/Contents/Developer").exists():
        results.append(run_command("SwiftPM host build", swift_command("build"), cwd=ROOT / "ios" / "MoonJarStoriesiOS"))
        results.append(run_command("SwiftPM host tests", swift_command("test"), cwd=ROOT / "ios" / "MoonJarStoriesiOS"))
    else:
        print("WARN: swift missing; skipped SwiftPM build/tests. Install Xcode/Swift to run this locally.")
        results.append(CheckResult("SwiftPM host build/tests", True, "skipped: swift missing"))

    if which("java") != "missing" and (ROOT / "android" / "gradlew").exists():
        results.append(run_command("Android Gradle test", ["./gradlew", "test"], cwd=ROOT / "android"))
        results.append(run_command("Android assembleDebug", ["./gradlew", "assembleDebug"], cwd=ROOT / "android"))
    else:
        print("WARN: java or android/gradlew missing; skipped Android build. Install JDK/Android tooling to run this locally.")
        results.append(CheckResult("Android Gradle build", True, "skipped: java/gradlew missing"))
    return summarize(results)


def validate(args: argparse.Namespace) -> int:
    results = [
        CheckResult("agent:lint", lint(argparse.Namespace()) == 0),
        CheckResult("agent:test", test(argparse.Namespace()) == 0),
    ]
    if getattr(args, "with_smoke", False):
        results.extend(
            [
                CheckResult("backend smoke", smoke(argparse.Namespace(target="backend")) == 0),
                CheckResult("iOS simulator smoke", smoke_ios() == 0),
                CheckResult("Android emulator smoke", smoke_android() == 0),
                run_command(
                    "artifact-backed reader score",
                    ["python3", "tools/score_reader_experience.py", "--require-smoke-artifacts"],
                ),
                run_command("strict visual layout QA", ["python3", "tools/validate_visual_layout.py", "--strict"]),
            ]
        )
    return summarize(results)


def read_pid() -> int | None:
    if not BACKEND_PID.exists():
        return None
    try:
        return int(BACKEND_PID.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def backend_responds() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/v1/catalog", timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def start_backend_process(persistent: bool) -> subprocess.Popen[str] | None:
    ensure_tmp()
    pid = read_pid()
    if pid and is_process_running(pid) and backend_responds():
        print(f"Backend already running with pid {pid}. Log: {rel(BACKEND_LOG)}")
        return None

    log_handle = BACKEND_LOG.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "backend" / "service_stub.py")],
        cwd=ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    BACKEND_PID.write_text(str(process.pid), encoding="utf-8")
    time.sleep(0.8)
    if not backend_responds():
        process.terminate()
        print(f"FAIL: backend did not respond on http://127.0.0.1:8080. See {rel(BACKEND_LOG)}")
        return process
    print(f"Backend started at http://127.0.0.1:8080 with pid {process.pid}. Log: {rel(BACKEND_LOG)}")
    if persistent:
        return None
    return process


def start(args: argparse.Namespace) -> int:
    if args.target != "backend":
        print("FAIL: only `scripts/agent/start backend` is currently supported. Read docs/RELIABILITY.md.")
        return 1
    process = start_backend_process(persistent=True)
    if process and process.poll() is not None:
        return 1
    return 0


def stop(args: argparse.Namespace) -> int:
    if args.target != "backend":
        print("FAIL: only `scripts/agent/stop backend` is currently supported.")
        return 1
    pid = read_pid()
    if not pid:
        print("No backend pid file found.")
        return 0
    if is_process_running(pid):
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped backend pid {pid}.")
    BACKEND_PID.unlink(missing_ok=True)
    return 0


def http_json(method: str, url: str, payload: dict | None = None) -> tuple[int, str]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3.0) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def http_raw(method: str, url: str, body: str, content_type: str = "application/json") -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        headers={"Content-Type": content_type},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=3.0) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def expected_complete_scene_count() -> int:
    catalog_path = ROOT / "shared-content" / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    total = 0
    for entry in catalog.get("books", []):
        if entry.get("status") != "complete":
            continue
        book_path = entry.get("bookPath")
        if not isinstance(book_path, str):
            continue
        try:
            book = json.loads((ROOT / "shared-content" / book_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        total += len(book.get("pages", []))
    return total


def expected_complete_book_count() -> int:
    catalog_path = ROOT / "shared-content" / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return sum(1 for entry in catalog.get("books", []) if entry.get("status") == "complete")


def assert_backend_payload(method: str, url: str, status: int, body: str) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return [f"{method} {url} did not return valid JSON."]

    if url.endswith("/v1/catalog"):
        if status != 200:
            errors.append("catalog endpoint did not return 200.")
        if payload.get("schemaVersion") != "1.0.0":
            errors.append("catalog schemaVersion should be 1.0.0.")
        if len(payload.get("books", [])) != 24:
            errors.append("catalog should expose 24 books.")
        complete = [item for item in payload.get("books", []) if item.get("status") == "complete"]
        if len(complete) != len(payload.get("books", [])):
            errors.append("catalog should expose complete shared-content payloads for every catalog book.")
    elif url.endswith("/v1/assets/manifest"):
        for key in ["imageManifestUrl", "audioManifestUrl", "version"]:
            if key not in payload:
                errors.append(f"asset manifest response is missing `{key}`.")
    elif url.endswith("/v1/entitlements/check"):
        if "canRead" not in payload or "reason" not in payload:
            errors.append("entitlement check response must include canRead and reason.")
    elif url.endswith("/v1/purchases/sync"):
        for key in ["anonymousUserId", "hasLifetimeUnlock", "unlockedBookIds"]:
            if key not in payload:
                errors.append(f"purchase sync response is missing `{key}`.")
    elif url.endswith("/v1/cms/release/readiness"):
        if status != 200 or payload.get("backendMode") != "local_persistent_stub":
            errors.append("release readiness endpoint should return local_persistent_stub mode.")
        counts = payload.get("counts", {})
        expected_scenes = expected_complete_scene_count()
        if counts.get("sceneImages") != expected_scenes:
            errors.append(f"release readiness should count {expected_scenes} complete-book scene images.")
        if not isinstance(payload.get("blockers"), list):
            errors.append("release readiness should include explicit production blockers.")
    elif url.endswith("/v1/cms/export/books/book.sun_moon"):
        book = payload.get("book", {})
        if status != 200 or payload.get("bookId") != "book.sun_moon":
            errors.append("CMS export should return the Sun and Moon book payload.")
        if len(book.get("pages", [])) != 32:
            errors.append("CMS export should include 32 Sun and Moon pages.")
    elif url.endswith("/v1/admin/reviews/queue"):
        counts = payload.get("counts", {})
        if status != 200 or payload.get("backendMode") != "local_persistent_stub":
            errors.append("admin review queue should return local_persistent_stub mode.")
        if counts.get("queuedAssets", 0) < 1 or counts.get("queuedStories", 0) < 1:
            errors.append("admin review queue should include queued assets and stories.")
    elif url.endswith("/v1/admin/assets/import"):
        if status != 200 or payload.get("assetId") != "local-imported-scene":
            errors.append("asset import should persist and return the imported asset ID.")
    elif url.endswith("/v1/admin/assets/local-asset") or url.endswith("/v1/admin/assets/local-imported-scene"):
        if status != 200 or not payload.get("assetId"):
            errors.append("admin asset lookup should return a persisted/default asset review record.")
    elif "/v1/books/book.sun_moon" in url:
        if status != 200 or payload.get("id") != "book.sun_moon":
            errors.append("book metadata endpoint should return the Sun and Moon catalog entry.")
    elif "/v1/books/book.not_real" in url:
        if status != 404 or payload.get("error") != "not_found":
            errors.append("unknown book endpoint should return 404 not_found.")
    return errors


def smoke(args: argparse.Namespace) -> int:
    if args.target == "ios":
        return smoke_ios()
    if args.target == "android":
        return smoke_android()
    if args.target == "all":
        return summarize(
            [
                CheckResult("backend smoke", smoke(argparse.Namespace(target="backend")) == 0),
                CheckResult("iOS simulator smoke", smoke_ios() == 0),
            ]
        )
    if args.target != "backend":
        print("FAIL: supported smoke targets are `backend`, `ios`, `android`, and `all`. Read docs/HARNESS.md.")
        return 1
    ensure_tmp()
    started = None
    if not backend_responds():
        started = start_backend_process(persistent=False)
        if started and started.poll() is not None:
            return 1

    transcript: list[str] = []
    checks = [
        ("GET", "http://127.0.0.1:8080/v1/catalog", None, 200),
        ("GET", "http://127.0.0.1:8080/v1/books/book.sun_moon", None, 200),
        ("GET", "http://127.0.0.1:8080/v1/books/book.not_real", None, 404),
        ("GET", "http://127.0.0.1:8080/v1/assets/manifest", None, 200),
        ("GET", "http://127.0.0.1:8080/v1/cms/release/readiness", None, 200),
        ("GET", "http://127.0.0.1:8080/v1/cms/export/books/book.sun_moon", None, 200),
        ("GET", "http://127.0.0.1:8080/v1/admin/reviews/queue", None, 200),
        (
            "POST",
            "http://127.0.0.1:8080/v1/entitlements/check",
            {"anonymousUserId": "agent-smoke-local", "platform": "ios", "bookId": "book.sun_moon"},
            200,
        ),
        (
            "POST",
            "http://127.0.0.1:8080/v1/entitlements/check",
            {"anonymousUserId": "agent-smoke-local", "platform": "ios", "bookId": "book.simcheong"},
            200,
        ),
        (
            "POST",
            "http://127.0.0.1:8080/v1/purchases/sync",
            {
                "anonymousUserId": "agent-smoke-local",
                "platform": "ios",
                "transactions": [
                    {"productId": "com.moonjarstories.subscription.monthly", "transactionToken": "local-test-token"}
                ],
            },
            200,
        ),
        (
            "PATCH",
            "http://127.0.0.1:8080/v1/admin/assets/local-asset/status",
            {
                "status": "generated_reviewed",
                "reviewer": "agent-smoke",
                "reviewDate": "2026-05-07",
                "culturalReviewStatus": "approved",
                "childSafetyReviewStatus": "approved",
                "productionApprovalStatus": "not_approved",
            },
            200,
        ),
        ("GET", "http://127.0.0.1:8080/v1/admin/assets/local-asset", None, 200),
        (
            "PATCH",
            "http://127.0.0.1:8080/v1/admin/stories/book.sun_moon/review",
            {
                "editorialStatus": "ready_for_review",
                "culturalReviewStatus": "not_reviewed",
                "childSafetyReviewStatus": "not_reviewed",
                "reviewer": "agent-smoke",
                "reviewDate": "2026-05-07",
            },
            200,
        ),
        (
            "POST",
            "http://127.0.0.1:8080/v1/admin/assets/import",
            {
                "assetId": "local-imported-scene",
                "storyId": "book.sun_moon",
                "assetType": "scene",
                "status": "generated_reviewed",
                "outputFile": "assets/books/sun-and-moon/page-001.png",
                "reviewer": "agent-smoke",
                "reviewDate": "2026-05-07",
                "culturalReviewStatus": "approved",
                "childSafetyReviewStatus": "approved",
                "productionApprovalStatus": "not_approved",
            },
            200,
        ),
        ("GET", "http://127.0.0.1:8080/v1/admin/assets/local-imported-scene", None, 200),
    ]
    ok = True
    for method, url, payload, expected_status in checks:
        status, body = http_json(method, url, payload)
        transcript.append(f"$ {method} {url}")
        if payload is not None:
            transcript.append(json.dumps(payload, ensure_ascii=False))
        transcript.append(f"status: {status}")
        transcript.append(body[:1200])
        transcript.append("")
        if status != expected_status:
            ok = False
            transcript.append(f"ASSERTION: expected status {expected_status}.")
        assertion_errors = assert_backend_payload(method, url, status, body)
        if assertion_errors:
            ok = False
            transcript.extend(f"ASSERTION: {error}" for error in assertion_errors)
            transcript.append("")
        if url.endswith("/v1/entitlements/check"):
            payload_body = json.loads(body)
            requested_book = payload.get("bookId") if payload else None
            if requested_book == "book.sun_moon" and payload_body.get("canRead") is not True:
                ok = False
                transcript.append("ASSERTION: free book should be readable.")
            if requested_book == "book.simcheong" and (payload_body.get("canRead") is not False or payload_body.get("reason") != "locked"):
                ok = False
                transcript.append("ASSERTION: premium complete-content book should remain locked by entitlement.")

    status, body = http_raw("POST", "http://127.0.0.1:8080/v1/entitlements/check", "{bad json")
    transcript.append("$ POST http://127.0.0.1:8080/v1/entitlements/check")
    transcript.append("{bad json")
    transcript.append(f"status: {status}")
    transcript.append(body[:1200])
    transcript.append("")
    if status != 400:
        ok = False
        transcript.append("ASSERTION: invalid JSON should return 400.")

    missing_field_checks = [
        ("POST", "http://127.0.0.1:8080/v1/entitlements/check", {"anonymousUserId": "agent-smoke-local"}),
        ("POST", "http://127.0.0.1:8080/v1/purchases/sync", {"anonymousUserId": "agent-smoke-local"}),
        ("PATCH", "http://127.0.0.1:8080/v1/admin/assets/local-asset/status", {"status": "generated_reviewed"}),
    ]
    for method, url, payload in missing_field_checks:
        status, body = http_json(method, url, payload)
        transcript.append(f"$ {method} {url}")
        transcript.append(json.dumps(payload, ensure_ascii=False))
        transcript.append(f"status: {status}")
        transcript.append(body[:1200])
        transcript.append("")
        if status != 400:
            ok = False
            transcript.append("ASSERTION: missing required fields should return 400.")
        else:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {}
            if parsed.get("error") != "missing_required_fields":
                ok = False
                transcript.append("ASSERTION: missing-field error should be structured.")

    invalid_contract_checks = [
        (
            "POST",
            "http://127.0.0.1:8080/v1/purchases/sync",
            {"anonymousUserId": "agent-smoke-local", "platform": "ios", "transactions": []},
            "invalid_field",
        ),
        (
            "POST",
            "http://127.0.0.1:8080/v1/purchases/sync",
            {
                "anonymousUserId": "agent-smoke-local",
                "platform": "ios",
                "transactions": [
                    {"productId": "invalid.product", "transactionToken": "local-test-token", "transactionState": "purchased"}
                ],
            },
            "invalid_transaction",
        ),
        (
            "POST",
            "http://127.0.0.1:8080/v1/purchases/sync",
            {
                "anonymousUserId": "agent-smoke-local",
                "platform": "ios",
                "transactions": [
                    {
                        "productId": "com.moonjarstories.subscription.monthly",
                        "transactionToken": "local-test-token",
                        "transactionState": "unknown_state",
                    }
                ],
            },
            "invalid_transaction",
        ),
        (
            "PATCH",
            "http://127.0.0.1:8080/v1/admin/assets/local-asset/status",
            {
                "status": "final_but_not_real",
                "reviewer": "agent-smoke",
                "reviewDate": "2026-05-07",
                "culturalReviewStatus": "approved",
                "childSafetyReviewStatus": "approved",
                "productionApprovalStatus": "not_approved",
            },
            "invalid_enum",
        ),
        (
            "PATCH",
            "http://127.0.0.1:8080/v1/admin/stories/book.sun_moon/review",
            {
                "editorialStatus": "ready_for_review",
                "culturalReviewStatus": "not_reviewed",
                "childSafetyReviewStatus": "not_reviewed",
                "reviewer": "agent-smoke",
                "reviewDate": "05/07/2026",
            },
            "invalid_date",
        ),
    ]
    for method, url, payload, expected_error in invalid_contract_checks:
        status, body = http_json(method, url, payload)
        transcript.append(f"$ {method} {url}")
        transcript.append(json.dumps(payload, ensure_ascii=False))
        transcript.append(f"status: {status}")
        transcript.append(body[:1200])
        transcript.append("")
        if status != 400:
            ok = False
            transcript.append("ASSERTION: invalid contract payload should return 400.")
        else:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {}
            if parsed.get("error") != expected_error:
                ok = False
                transcript.append(f"ASSERTION: expected `{expected_error}` error.")

    artifact = ARTIFACT_DIR / "backend-smoke-transcript.md"
    artifact.write_text("\n".join(transcript), encoding="utf-8")
    print(f"Smoke transcript: {rel(artifact)}")

    if started is not None and started.poll() is None:
        started.terminate()
        try:
            started.wait(timeout=2)
        except subprocess.TimeoutExpired:
            started.kill()
        BACKEND_PID.unlink(missing_ok=True)

    if not ok:
        print("FAIL: backend smoke contract assertions failed. Read the transcript and backend/README.md.")
        return 1
    print("PASS: backend smoke endpoints and error contracts behaved as expected.")
    return 0


def developer_dir() -> str:
    configured = os.environ.get("DEVELOPER_DIR")
    if configured:
        return configured
    bundled_xcode = Path("/Applications/Xcode.app/Contents/Developer")
    if bundled_xcode.exists():
        return str(bundled_xcode)
    selected = subprocess.run(["/usr/bin/xcode-select", "-p"], text=True, capture_output=True, check=False)
    return selected.stdout.strip() or str(bundled_xcode)


def run_simctl(*args: str, required: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DEVELOPER_DIR"] = developer_dir()
    completed = subprocess.run(
        ["/usr/bin/xcrun", "simctl", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if required and completed.returncode != 0:
        raise RuntimeError(f"simctl {' '.join(args)} failed: {completed.stdout}\n{completed.stderr}")
    return completed


def booted_simulator_udid() -> str | None:
    requested = os.environ.get("SIMULATOR_UDID")
    if requested:
        return requested
    completed = run_simctl("list", "devices", "booted", required=False)
    for line in completed.stdout.splitlines():
        match = re.search(r"\(([0-9A-F-]{36})\)\s+\(Booted\)", line)
        if match:
            return match.group(1)
    return None


def first_available_ipad_udid() -> str | None:
    completed = run_simctl("list", "devices", "available", required=False)
    for line in completed.stdout.splitlines():
        if "iPad" not in line:
            continue
        match = re.search(r"\(([0-9A-F-]{36})\)\s+\((Shutdown|Booted)\)", line)
        if match:
            return match.group(1)
    return None


def ensure_ios_simulator() -> str:
    if not Path(developer_dir()).exists():
        raise RuntimeError("Xcode developer directory is missing. Install Xcode or set DEVELOPER_DIR.")
    udid = booted_simulator_udid() or first_available_ipad_udid()
    if not udid:
        raise RuntimeError("No available iPad simulator found. Install an iPad simulator runtime in Xcode.")
    run_simctl("boot", udid, required=False)
    run_simctl("bootstatus", udid, "-b", required=False)
    return udid


def package_ios_app(udid: str) -> Path:
    ensure_tmp()
    env = os.environ.copy()
    env["DEVELOPER_DIR"] = developer_dir()
    env["SIMULATOR_UDID"] = udid
    completed = subprocess.run(
        [str(ROOT / "tools" / "package_ios_sim_app.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    log_path = LOG_DIR / "ios-smoke-build-install.log"
    log_path.write_text((completed.stdout or "") + "\n" + (completed.stderr or ""), encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"iOS build/install failed. See {rel(log_path)}")
    return log_path


def launch_ios(udid: str, *arguments: str) -> None:
    run_simctl("terminate", udid, IOS_BUNDLE_ID, required=False)
    run_simctl("launch", udid, IOS_BUNDLE_ID, "--args", *arguments)


def screenshot_ios(udid: str, filename: str) -> Path:
    output = ARTIFACT_DIR / filename
    run_simctl("io", udid, "screenshot", str(output))
    return output


def copy_ios_self_test_artifacts(udid: str) -> list[Path]:
    completed = run_simctl("get_app_container", udid, IOS_BUNDLE_ID, "data", required=False)
    if completed.returncode != 0:
        return []
    documents = Path(completed.stdout.strip()) / "Documents"
    copied: list[Path] = []
    for name in ["reader-real-book-self-test.json", "reader-playback-self-test.json"]:
        source = documents / name
        if source.exists():
            destination = ARTIFACT_DIR / name
            shutil.copy2(source, destination)
            copied.append(destination)
    return copied


def clear_ios_self_test_artifacts(udid: str) -> None:
    completed = run_simctl("get_app_container", udid, IOS_BUNDLE_ID, "data", required=False)
    if completed.returncode != 0:
        return
    documents = Path(completed.stdout.strip()) / "Documents"
    for name in ["reader-real-book-self-test.json", "reader-playback-self-test.json"]:
        (documents / name).unlink(missing_ok=True)
        (ARTIFACT_DIR / name).unlink(missing_ok=True)


def json_result_bool(path: Path, key: str) -> bool:
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get(key)
    except Exception:
        return False
    return value is True or value == "true"


def smoke_ios() -> int:
    ensure_tmp()
    transcript = ["# iOS Simulator Smoke Transcript", ""]
    try:
        udid = ensure_ios_simulator()
        transcript.append(f"- simulator: `{udid}`")
        build_log = package_ios_app(udid)
        transcript.append(f"- build/install log: `{rel(build_log)}`")
        clear_ios_self_test_artifacts(udid)

        launch_ios(udid)
        time.sleep(2.0)
        library_shot = screenshot_ios(udid, "ios-smoke-library.png")
        transcript.append(f"- library screenshot: `{rel(library_shot)}`")

        launch_ios(udid, "--demo-reader", "--demo-page=3", "--demo-real-book", "--demo-self-test=real-book-next-back")
        time.sleep(5.2)
        real_book_shot = screenshot_ios(udid, "ios-smoke-real-book-page3.png")
        transcript.append(f"- Real Book Mode screenshot: `{rel(real_book_shot)}`")
        for path in copy_ios_self_test_artifacts(udid):
            transcript.append(f"- self-test result: `{rel(path)}`")

        launch_ios(udid, "--demo-reader", "--demo-page=2", "--demo-self-test=reader-playback")
        time.sleep(4.2)
        playback_shot = screenshot_ios(udid, "ios-smoke-reader-playback.png")
        transcript.append(f"- playback screenshot: `{rel(playback_shot)}`")

        for path in copy_ios_self_test_artifacts(udid):
            transcript.append(f"- self-test result: `{rel(path)}`")

        real_book_result = ARTIFACT_DIR / "reader-real-book-self-test.json"
        playback_result = ARTIFACT_DIR / "reader-playback-self-test.json"
        ok = True
        if not real_book_result.exists() or not json_result_bool(real_book_result, "nextAdvancedOneSpread"):
            transcript.append("- FAIL: Real Book Mode did not confirm a single next action advanced one spread.")
            ok = False
        if not real_book_result.exists() or not json_result_bool(real_book_result, "backReturnedToInitialSpread"):
            transcript.append("- FAIL: Real Book Mode did not confirm back returned to the original spread.")
            ok = False
        if not playback_result.exists() or not json_result_bool(playback_result, "isPlaying"):
            transcript.append("- FAIL: playback self-test did not confirm narration playback started.")
            ok = False

        artifact = ARTIFACT_DIR / "ios-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"iOS smoke transcript: {rel(artifact)}")
        if not ok:
            print("FAIL: iOS smoke assertions failed. Check screenshots and self-test JSON.")
            return 1
        print("PASS: iOS simulator smoke launched library, Real Book Mode, and playback flows.")
        return 0
    except Exception as exc:
        transcript.append(f"- FAIL: {exc}")
        artifact = ARTIFACT_DIR / "ios-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: iOS smoke failed: {exc}")
        print(f"Transcript: {rel(artifact)}")
        return 1


def adb_command() -> str | None:
    discovered = shutil.which("adb")
    if discovered:
        return discovered
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        candidate = Path(android_home) / "platform-tools" / "adb"
        if candidate.exists():
            return str(candidate)
    return None


def attached_android_device(adb: str) -> str | None:
    completed = subprocess.run([adb, "devices"], cwd=ROOT, text=True, capture_output=True, check=False)
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0]
    return None


def smoke_android() -> int:
    ensure_tmp()
    transcript = ["# Android Smoke Transcript", ""]
    adb = adb_command()
    if not adb:
        transcript.append("- FAIL: `adb` was not found. Install Android SDK platform-tools or set ANDROID_HOME/ANDROID_SDK_ROOT.")
        artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: Android smoke needs adb. Transcript: {rel(artifact)}")
        return 1

    device = attached_android_device(adb)
    if not device:
        transcript.append("- FAIL: no attached Android emulator/device is in `device` state.")
        transcript.append("- Run Android Studio emulator or attach a device, then retry `scripts/agent/smoke android`.")
        artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: no Android emulator/device attached. Transcript: {rel(artifact)}")
        return 1

    build_result = subprocess.run(["./gradlew", "assembleDebug"], cwd=ROOT / "android", text=True, capture_output=True, check=False)
    build_log = LOG_DIR / "android-smoke-build.log"
    build_log.write_text((build_result.stdout or "") + "\n" + (build_result.stderr or ""), encoding="utf-8")
    transcript.append(f"- device: `{device}`")
    transcript.append(f"- build log: `{rel(build_log)}`")
    if build_result.returncode != 0:
        transcript.append("- FAIL: `./gradlew assembleDebug` failed.")
        artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: Android build failed. Transcript: {rel(artifact)}")
        return 1

    apk = ROOT / "android" / "MoonJarStoriesAndroid" / "build" / "outputs" / "apk" / "debug" / "MoonJarStoriesAndroid-debug.apk"
    install_result = subprocess.run([adb, "-s", device, "install", "-r", str(apk)], cwd=ROOT, text=True, capture_output=True, check=False)
    transcript.append(install_result.stdout.strip())
    if install_result.returncode != 0:
        transcript.append(install_result.stderr.strip())
        transcript.append("- FAIL: APK install failed.")
        artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: Android install failed. Transcript: {rel(artifact)}")
        return 1

    subprocess.run(
        [adb, "-s", device, "shell", "run-as", ANDROID_PACKAGE_ID, "rm", "-f", "files/moonjar-android-self-test.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    self_test_token = f"agent-{uuid.uuid4()}"
    subprocess.run([adb, "-s", device, "shell", "am", "force-stop", ANDROID_PACKAGE_ID], cwd=ROOT, capture_output=True, text=True, check=False)
    launch_result = subprocess.run(
        [
            adb,
            "-s",
            device,
            "shell",
            "am",
            "start",
            "-n",
            f"{ANDROID_PACKAGE_ID}/.MainActivity",
            "-e",
            "moonjar.selfTest",
            "reader-contract",
            "-e",
            "moonjar.selfTestToken",
            self_test_token,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    transcript.append(launch_result.stdout.strip())
    if launch_result.returncode != 0:
        transcript.append(launch_result.stderr.strip())
        transcript.append("- FAIL: app launch failed.")
        artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
        artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"FAIL: Android launch failed. Transcript: {rel(artifact)}")
        return 1

    self_test = None
    payload: dict = {}
    for attempt in range(1, 25):
        time.sleep(0.75)
        candidate = subprocess.run(
            [adb, "-s", device, "exec-out", "run-as", ANDROID_PACKAGE_ID, "cat", "files/moonjar-android-self-test.json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if candidate.returncode == 0 and candidate.stdout.strip() and not candidate.stdout.startswith("cat:"):
            try:
                parsed = json.loads(candidate.stdout)
            except json.JSONDecodeError:
                parsed = {}
            if parsed.get("token") == self_test_token:
                self_test = candidate
                payload = parsed
                transcript.append(f"- self-test ready after {attempt} poll attempt(s).")
                break
            self_test = candidate

    screenshot = ARTIFACT_DIR / "android-smoke-launch.png"
    with screenshot.open("wb") as output:
        subprocess.run([adb, "-s", device, "exec-out", "screencap", "-p"], cwd=ROOT, stdout=output, stderr=subprocess.DEVNULL, check=False)
    transcript.append(f"- launch screenshot: `{rel(screenshot)}`")

    self_test_artifact = ARTIFACT_DIR / "moonjar-android-self-test.json"
    if self_test is not None and self_test.returncode == 0 and self_test.stdout.strip() and not self_test.stdout.startswith("cat:"):
        self_test_artifact.write_text(self_test.stdout, encoding="utf-8")
        transcript.append(f"- self-test result: `{rel(self_test_artifact)}`")
        required_true = [
            "englishFirst",
            "freeBookReadable",
            "premiumBookLocked",
            "sceneAssetResolved",
            "englishNarrationResolved",
            "koreanNarrationResolved",
            "nextAdvanced",
            "previousReturned",
            "realBookModeToggled",
            "spreadNextAdvanced",
            "singlePageFallbackKept",
            "playbackStarted",
        ]
        for key in required_true:
            if payload.get(key) is not True:
                transcript.append(f"- FAIL: Android self-test expected `{key}` to be true.")
        if payload.get("catalogBooks") != 24:
            transcript.append("- FAIL: Android self-test expected 24 catalog books.")
        expected_books = expected_complete_book_count()
        if payload.get("completeBooks") != expected_books:
            transcript.append(f"- FAIL: Android self-test expected {expected_books} complete books.")
        if payload.get("sceneCount") != 32:
            transcript.append("- FAIL: Android self-test expected Sun and Moon to have 32 scenes.")
        if payload.get("token") != self_test_token:
            transcript.append("- FAIL: Android self-test token did not match this smoke run.")
    else:
        if self_test is not None:
            transcript.append((self_test.stderr or self_test.stdout).strip())
        transcript.append("- FAIL: Android self-test artifact was not readable via run-as.")

    artifact = ARTIFACT_DIR / "android-smoke-transcript.md"
    artifact.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    if any(line.startswith("- FAIL:") for line in transcript):
        print(f"FAIL: Android smoke assertions failed. Transcript: {rel(artifact)}")
        return 1
    print(f"PASS: Android smoke installed and launched the app. Transcript: {rel(artifact)}")
    return 0


def garden(_: argparse.Namespace) -> int:
    ensure_tmp()
    lines: list[str] = ["# Agent Garden Report", ""]
    lines.append("## Checks")
    docs_ok = check_docs(argparse.Namespace()) == 0
    arch_ok = check_architecture(argparse.Namespace()) == 0
    lines.append(f"- docs check: {'pass' if docs_ok else 'fail'}")
    lines.append(f"- architecture check: {'pass' if arch_ok else 'fail'}")

    lines.append("")
    lines.append("## Active ExecPlans")
    active = sorted((ROOT / "docs" / "exec-plans" / "active").glob("*.md"))
    if active:
        for plan in active:
            lines.append(f"- {rel(plan)}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## TODO / FIXME / HACK")
    todos = find_todos(limit=80)
    lines.extend(todos or ["- none found in scanned text files"])

    lines.append("")
    lines.append("## Recommended Follow-Ups")
    if not docs_ok:
        lines.append("- Fix docs freshness errors before large feature work.")
    if not arch_ok:
        lines.append("- Fix architecture/taste errors before merging new app changes.")
    lines.append("- Move completed ExecPlans from active to completed after validation.")
    lines.append("- Add UI automation for iOS/Android reader flows when feasible.")

    report = ARTIFACT_DIR / "garden-report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Garden report: {rel(report)}")
    print("\n".join(lines))
    return 0 if docs_ok and arch_ok else 1


def find_todos(limit: int) -> list[str]:
    results: list[str] = []
    pattern = re.compile(r"\b(TODO|FIXME|HACK)\s*:", re.IGNORECASE)
    for path in iter_repo_files():
        if not is_text_file(path):
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            stripped = line.strip()
            if pattern.search(stripped):
                results.append(f"- {rel(path)}:{index}: {line.strip()[:180]}")
                if len(results) >= limit:
                    results.append(f"- truncated at {limit} matches")
                    return results
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Moon Jar Stories agent harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor").set_defaults(func=doctor)
    subparsers.add_parser("check-docs").set_defaults(func=check_docs)
    subparsers.add_parser("check-architecture").set_defaults(func=check_architecture)
    subparsers.add_parser("lint").set_defaults(func=lint)
    subparsers.add_parser("test").set_defaults(func=test)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument(
        "--with-smoke",
        action="store_true",
        help="Also run backend/iOS/Android smoke checks, then require current smoke artifacts for reader/layout scoring.",
    )
    validate_parser.set_defaults(func=validate)
    subparsers.add_parser("garden").set_defaults(func=garden)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("target", nargs="?", default="backend")
    start_parser.set_defaults(func=start)

    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("target", nargs="?", default="backend")
    stop_parser.set_defaults(func=stop)

    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("target", nargs="?", default="backend")
    smoke_parser.set_defaults(func=smoke)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
