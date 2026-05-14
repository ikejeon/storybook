#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
ARTIFACTS = ROOT / ".agent" / "tmp" / "artifacts"
REPORT = ROOT / "tools" / "output" / "visual_layout_qa_report.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def prompt_has_any(prompt: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in prompt for phrase in phrases)


def validate_art_entry(entry: dict, group: str, errors: list[str], critical_warnings: list[str], review_notes: list[str]) -> tuple[str, str, str]:
    output = entry.get("outputFile")
    context = f"{group} {entry.get('storySlug') or entry.get('storyId')} {entry.get('sceneId') or entry.get('assetType')}"
    if not output:
        errors.append(f"{context}: missing outputFile.")
        return context, "missing", "missing"
    path = CONTENT / output
    if not path.exists():
        errors.append(f"{context}: output file does not exist: {output}")
        return context, "missing", "missing"
    dimensions = png_dimensions(path)
    if dimensions is None:
        if path.suffix.lower() == ".svg":
            return context, "svg", "skipped-vector"
        errors.append(f"{context}: expected PNG or SVG asset, got {output}.")
        return context, "unknown", "invalid"
    width, height = dimensions
    ratio = width / height
    status = entry.get("status", "missing")
    prompt = f"{entry.get('prompt', '')} {entry.get('rawPrompt', '')}".lower()
    if not 1.25 <= ratio <= 2.10:
        errors.append(f"{context}: image ratio {ratio:.2f} is outside fit-safe reader/card range for {width}x{height}.")
    if width < 900 or height < 650:
        review_notes.append(f"{context}: draft image is lower than preferred review size: {width}x{height}.")
    prompt_requirements = [
        ("safe margins", ("safe margin", "safe margins", "fit-safe", "fit safe", "generous margin", "edge padding")),
        ("no cropping", ("no cropped", "not cropped", "no accidental cropping", "no face crop", "no cut off", "no cut-off", "uncropped")),
        ("no text", ("no text", "no letters", "without text", "text-free")),
        ("no watermark", ("no watermark", "without watermark", "no logo")),
    ]
    for label, phrases in prompt_requirements:
        if not prompt_has_any(prompt, phrases) and status != "placeholder":
            critical_warnings.append(f"{context}: prompt does not explicitly include `{label}` guidance.")
    return context, f"{width}x{height}", status


def validate_smoke_screenshot(path: Path, errors: list[str], review_notes: list[str]) -> tuple[str, str]:
    dimensions = png_dimensions(path)
    if dimensions is None:
        errors.append(f"{path.relative_to(ROOT)}: smoke screenshot is missing or not a PNG.")
        return path.name, "missing"
    width, height = dimensions
    if width < 900 or height < 900:
        review_notes.append(f"{path.relative_to(ROOT)}: screenshot is smaller than preferred manual QA size: {width}x{height}.")
    if path.stat().st_size < 200_000:
        errors.append(f"{path.relative_to(ROOT)}: screenshot file is suspiciously small and may be blank.")
    return path.name, f"{width}x{height}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Moon Jar art/layout dimensions and smoke screenshots.")
    parser.add_argument("--strict", action="store_true", help="Fail on critical prompt/screenshot warnings as well as hard errors.")
    args = parser.parse_args()

    manifest = load(MANIFEST)
    errors: list[str] = []
    critical_warnings: list[str] = []
    review_notes: list[str] = []
    rows = [
        "# Visual Layout QA Report",
        "",
        "This check verifies fit-safe image dimensions, prompt-level no-crop guidance, and smoke screenshot artifacts when present. It is a repo-local heuristic, not a replacement for human art/layout review.",
        "",
        "## Art Assets",
        "",
        "| Asset | Dimensions | Status |",
        "| --- | --- | --- |",
    ]

    for group in ("sceneEntries", "coverEntries"):
        for entry in manifest.get(group, []):
            context, dimensions, status = validate_art_entry(entry, group, errors, critical_warnings, review_notes)
            rows.append(f"| {context} | {dimensions} | {status} |")

    rows.extend(["", "## Smoke Screenshots", "", "| Screenshot | Dimensions |", "| --- | --- |"])
    for name in ("ios-smoke-real-book-page3.png", "ios-smoke-reader-playback.png", "android-smoke-launch.png"):
        path = ARTIFACTS / name
        if path.exists():
            screenshot_name, dimensions = validate_smoke_screenshot(path, errors, review_notes)
            rows.append(f"| {screenshot_name} | {dimensions} |")
        else:
            critical_warnings.append(f".agent/tmp/artifacts/{name}: screenshot is not present yet; run the matching smoke command for visual evidence.")
            rows.append(f"| {name} | not present |")

    if critical_warnings:
        rows.extend(["", "## Critical Warnings", ""])
        rows.extend(f"- {warning}" for warning in critical_warnings[:80])
        if len(critical_warnings) > 80:
            rows.append(f"- ... {len(critical_warnings) - 80} additional critical warning(s)")

    if review_notes:
        rows.extend(["", "## Review Notes", ""])
        rows.extend(f"- {warning}" for warning in review_notes[:80])
        if len(review_notes) > 80:
            rows.append(f"- ... {len(review_notes) - 80} additional review note(s)")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    if errors:
        print("Moon Jar visual layout QA failed:")
        for error in errors:
            print(f"- {error}")
        print(f"Report: {REPORT.relative_to(ROOT)}")
        return 1
    if args.strict and critical_warnings:
        print("Moon Jar visual layout strict QA failed:")
        for warning in critical_warnings:
            print(f"- {warning}")
        print(f"Report: {REPORT.relative_to(ROOT)}")
        return 1

    print("Moon Jar visual layout QA passed: art dimensions and available smoke screenshots are fit-safe.")
    if critical_warnings or review_notes:
        print(
            f"Critical warnings: {len(critical_warnings)}; review notes: {len(review_notes)}. "
            f"Report: {REPORT.relative_to(ROOT)}"
        )
    else:
        print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
