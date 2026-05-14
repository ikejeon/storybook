#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"
VOICE_BAKEOFF_MANIFEST = CONTENT / "audio" / "manifests" / "voice_bakeoff_manifest.json"
COMPLIANCE_FLAGS = CONTENT / "compliance" / "app_behavior_flags.json"
DESIGN_TOKENS = CONTENT / "design" / "moonjar_design_tokens.json"

IMAGE_STATUSES = {
    "placeholder",
    "generated_draft",
    "generated_reviewed",
    "commissioned_draft",
    "commissioned_reviewed",
    "commissioned_final",
    "rejected",
}

AUDIO_STATUSES = {
    "placeholder",
    "synthetic_draft",
    "synthetic_reviewed",
    "human_recorded_draft",
    "human_recorded_reviewed",
    "human_recorded_final",
    "rejected",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def is_approved_final(entry: dict[str, Any]) -> bool:
    return (
        bool(entry.get("reviewer"))
        and bool(entry.get("reviewDate"))
        and entry.get("culturalReviewStatus") == "approved"
        and entry.get("childSafetyReviewStatus") == "approved"
        and entry.get("productionApprovalStatus") == "approved"
    )


def png_dimensions(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() != ".png":
        return None
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def validate_image_ratio(path: Path, context: str, errors: list[str]) -> None:
    dimensions = png_dimensions(path)
    if dimensions is None:
        return
    width, height = dimensions
    require(width > 0 and height > 0, f"{context}: invalid image dimensions {width}x{height}", errors)
    ratio = width / height
    if "app-icon" in str(path):
        require(0.90 <= ratio <= 1.10, f"{context}: app icon candidate should be square, got {width}x{height}", errors)
    else:
        require(1.25 <= ratio <= 2.10, f"{context}: story art aspect ratio is outside the supported fit-safe range, got {width}x{height}", errors)


def validate_image_prompt_safety(entry: dict[str, Any], context: str, errors: list[str]) -> None:
    prompt = f"{entry.get('prompt', '')} {entry.get('rawPrompt', '')}".lower()
    require("no text" in prompt or "no text or letters" in prompt, f"{context}: image prompt must explicitly forbid text in image", errors)
    require("watermark" in prompt or entry.get("status") == "placeholder", f"{context}: image prompt should explicitly forbid watermarks", errors)
    if entry.get("storySlug") == "sun-and-moon" and entry.get("assetType") == "scene":
        page_number = entry.get("pageNumber")
        if page_number in {3, 4, 7, 11, 16}:
            require(
                any(word in prompt for word in ("cunning", "hungry", "watchful", "dangerous", "unsettling", "threatening")),
                f"{context}: Sun and Moon tiger anchor prompt missing revised antagonist tone",
                errors,
            )


def validate_entry(entry: dict[str, Any], allowed_statuses: set[str], final_status: str, context: str, errors: list[str], *, image_entry: bool = False, audio_entry: bool = False) -> Counter:
    counts: Counter = Counter()
    status = entry.get("status")
    require(status in allowed_statuses, f"{context}: invalid status {status!r}", errors)
    output = entry.get("outputFile")
    require(isinstance(output, str) and output, f"{context}: missing outputFile", errors)
    if isinstance(output, str) and output:
        output_path = CONTENT / output
        require(output_path.exists(), f"{context}: outputFile does not exist: {output_path}", errors)
        if image_entry and output_path.exists():
            validate_image_ratio(output_path, context, errors)
        if status == final_status:
            require("final" in output or "human-recorded-final" in output, f"{context}: final status points outside final folder: {output}", errors)
    if status == final_status:
        require(is_approved_final(entry), f"{context}: final asset missing required review approvals", errors)
    if status == "rejected":
        require(bool(entry.get("rejectionReason")), f"{context}: rejected asset missing rejectionReason", errors)

    candidates = entry.get("candidates", [])
    require(isinstance(candidates, list) and candidates, f"{context}: candidates must be a non-empty list", errors)
    for idx, candidate in enumerate(candidates if isinstance(candidates, list) else [], start=1):
        candidate_status = candidate.get("status")
        counts[candidate_status] += 1
        require(candidate_status in allowed_statuses, f"{context}: candidate {idx} invalid status {candidate_status!r}", errors)
        candidate_output = candidate.get("outputFile")
        require(isinstance(candidate_output, str) and candidate_output, f"{context}: candidate {idx} missing outputFile", errors)
        if isinstance(candidate_output, str) and candidate_output:
            candidate_path = CONTENT / candidate_output
            require(candidate_path.exists(), f"{context}: candidate {idx} output missing: {candidate_path}", errors)
            if image_entry and candidate_path.exists():
                validate_image_ratio(candidate_path, f"{context}: candidate {idx}", errors)
        if candidate_status == final_status:
            require(is_approved_final(candidate), f"{context}: candidate {idx} final asset missing required review approvals", errors)
        if audio_entry and "narrationEntries" not in context and candidate_status not in {None, "placeholder"}:
            require(
                bool(candidate.get("sourceLicense") or candidate.get("license")),
                f"{context}: candidate {idx} non-placeholder audio missing sourceLicense/license",
                errors,
            )
        if candidate_status == "rejected":
            require(bool(candidate.get("rejectionReason")), f"{context}: candidate {idx} rejected asset missing rejectionReason", errors)
        provider_text = f"{candidate.get('provider')} {candidate.get('tool')} {candidate.get('generationStatus')}".lower()
        require(
            not (candidate_status in {"generated_reviewed", "commissioned_reviewed", "commissioned_final", "synthetic_reviewed", "human_recorded_reviewed", "human_recorded_final"} and "placeholder" in provider_text),
            f"{context}: candidate {idx} placeholder provider marked reviewed/final",
            errors,
        )
    return counts


def validate_image_manifest(errors: list[str]) -> Counter:
    manifest = load_json(IMAGE_MANIFEST)
    require(set(manifest.get("statusVocabulary", [])) == IMAGE_STATUSES, f"{IMAGE_MANIFEST}: status vocabulary mismatch", errors)
    counts: Counter = Counter()
    seen_outputs: set[str] = set()
    for group in ("sceneEntries", "coverEntries", "appIconConcepts", "approvalAnchorEntries"):
        entries = manifest.get(group)
        if group == "approvalAnchorEntries" and entries is None:
            continue
        require(isinstance(entries, list) and entries, f"{IMAGE_MANIFEST}: {group} missing", errors)
        for idx, entry in enumerate(entries or [], start=1):
            context = f"{IMAGE_MANIFEST}: {group} {idx}"
            validate_image_prompt_safety(entry, context, errors)
            output = entry.get("outputFile")
            if isinstance(output, str):
                require(output not in seen_outputs, f"{context}: duplicate best outputFile {output}", errors)
                seen_outputs.add(output)
            counts.update(validate_entry(entry, IMAGE_STATUSES, "commissioned_final", context, errors, image_entry=True))
    return counts


def validate_audio_manifest(errors: list[str]) -> Counter:
    manifest = load_json(AUDIO_MANIFEST)
    require(set(manifest.get("statusVocabulary", [])) == AUDIO_STATUSES, f"{AUDIO_MANIFEST}: status vocabulary mismatch", errors)
    counts: Counter = Counter()
    for group in ("narrationEntries", "ambientEntries", "uiSoundEntries"):
        entries = manifest.get(group)
        require(isinstance(entries, list) and entries, f"{AUDIO_MANIFEST}: {group} missing", errors)
        for idx, entry in enumerate(entries or [], start=1):
            counts.update(validate_entry(entry, AUDIO_STATUSES, "human_recorded_final", f"{AUDIO_MANIFEST}: {group} {idx}", errors, audio_entry=True))
    for idx, entry in enumerate(manifest.get("sfxEntries", []) or [], start=1):
        counts.update(validate_entry(entry, AUDIO_STATUSES, "human_recorded_final", f"{AUDIO_MANIFEST}: sfxEntries {idx}", errors, audio_entry=True))
    return counts


def validate_folder_separation(errors: list[str]) -> None:
    required_dirs = [
        CONTENT / "assets" / "placeholders",
        CONTENT / "assets" / "generated-draft",
        CONTENT / "assets" / "reviewed",
        CONTENT / "assets" / "final",
        CONTENT / "assets" / "manifests",
        CONTENT / "audio" / "placeholders",
        CONTENT / "audio" / "synthetic-draft",
        CONTENT / "audio" / "reviewed",
        CONTENT / "audio" / "human-recorded-final",
        CONTENT / "audio" / "manifests",
    ]
    for directory in required_dirs:
        require(directory.exists(), f"missing production asset directory: {directory}", errors)


def validate_compliance(errors: list[str]) -> None:
    flags = load_json(COMPLIANCE_FLAGS)
    for flag in flags.get("disallowedFutureFlags", []):
        require(flags.get(flag) is False, f"{COMPLIANCE_FLAGS}: disallowed child-safety flag enabled: {flag}", errors)
    require(flags.get("parentGateRequiredForPurchases") is True, f"{COMPLIANCE_FLAGS}: parent gate must be required for purchases", errors)
    for item in flags.get("dataCollected", []):
        require(item.get("childData") is False, f"{COMPLIANCE_FLAGS}: child data collection is not allowed: {item.get('name')}", errors)
        require(item.get("sharedWithThirdParties") is False, f"{COMPLIANCE_FLAGS}: third-party sharing is not allowed: {item.get('name')}", errors)


def validate_design_tokens(errors: list[str]) -> None:
    require(DESIGN_TOKENS.exists(), f"missing shared design tokens: {DESIGN_TOKENS}", errors)
    if not DESIGN_TOKENS.exists():
        return
    tokens = load_json(DESIGN_TOKENS)
    for key in ("moonIvory", "deepIndigo", "persimmonOrange", "jadeGreen", "lotusPink", "warmHanjiBeige", "softInkBlack"):
        require(bool(tokens.get("colors", {}).get(key)), f"{DESIGN_TOKENS}: missing color token {key}", errors)
    layout = tokens.get("layout", {})
    require(layout.get("coverAspectRatio") == 1.5, f"{DESIGN_TOKENS}: coverAspectRatio should be 1.5", errors)
    require(layout.get("thumbnailAspectRatio") == 1.5, f"{DESIGN_TOKENS}: thumbnailAspectRatio should be 1.5", errors)


def validate_voice_bakeoff_manifest(errors: list[str]) -> Counter:
    counts: Counter = Counter()
    if not VOICE_BAKEOFF_MANIFEST.exists():
        return counts
    manifest = load_json(VOICE_BAKEOFF_MANIFEST)
    sample_lines = manifest.get("sampleLines", {})
    require(isinstance(sample_lines, dict) and sample_lines, f"{VOICE_BAKEOFF_MANIFEST}: sampleLines missing", errors)
    for idx, entry in enumerate(manifest.get("entries", []) or [], start=1):
        context = f"{VOICE_BAKEOFF_MANIFEST}: entries {idx}"
        status = entry.get("status")
        counts[status] += 1
        require(status in AUDIO_STATUSES, f"{context}: invalid status {status!r}", errors)
        output = entry.get("outputFile")
        require(isinstance(output, str) and output, f"{context}: missing outputFile", errors)
        if isinstance(output, str) and output:
            require((CONTENT / output).exists(), f"{context}: outputFile does not exist: {output}", errors)
        require(entry.get("sampleId") in sample_lines, f"{context}: sampleId is not in sampleLines", errors)
        require(entry.get("language") in {"en", "ko"}, f"{context}: invalid language {entry.get('language')!r}", errors)
        if status == "human_recorded_final":
            require(is_approved_final(entry), f"{context}: final voice sample missing required review approvals", errors)
    return counts


def main() -> int:
    errors: list[str] = []
    validate_folder_separation(errors)
    image_counts = validate_image_manifest(errors)
    audio_counts = validate_audio_manifest(errors)
    voice_counts = validate_voice_bakeoff_manifest(errors)
    validate_compliance(errors)
    validate_design_tokens(errors)

    if errors:
        print("Moon Jar asset validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Moon Jar asset validation passed.")
    print(f"Image candidates by status: {dict(sorted(image_counts.items()))}")
    print(f"Audio candidates by status: {dict(sorted(audio_counts.items()))}")
    if voice_counts:
        print(f"Voice bakeoff samples by status: {dict(sorted(voice_counts.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
