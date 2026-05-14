#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def best_status(entry: dict) -> str:
    return entry.get("status", "missing")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate demo, generated-draft, or production readiness.")
    parser.add_argument("--level", choices=["demo", "generated-draft", "production", "release-candidate"], default="generated-draft")
    args = parser.parse_args()

    catalog = load(CONTENT / "catalog.json")
    images = load(CONTENT / "assets/manifests/image_manifest.json")
    audio = load(CONTENT / "audio/manifests/audio_manifest.json")

    complete_ids = {entry["id"] for entry in catalog["books"] if entry.get("status") == "complete"}
    expected_scene_count = 0
    expected_narration_entries = 0
    complete_slugs: set[str] = set()
    for entry in catalog["books"]:
        if entry.get("status") != "complete":
            continue
        book_path = entry.get("bookPath")
        if not book_path:
            continue
        book = load(CONTENT / book_path)
        pages = book.get("pages", [])
        expected_scene_count += len(pages)
        expected_narration_entries += len(pages) * 2
        complete_slugs.add(book.get("slug"))
    scene_entries = [entry for entry in images.get("sceneEntries", []) if entry.get("storyId") in complete_ids]
    cover_entries = [entry for entry in images.get("coverEntries", []) if entry.get("storyId") in complete_ids]
    narration_entries = [entry for entry in audio.get("narrationEntries", []) if entry.get("storyId") in complete_ids]
    page_turn = next((entry for entry in audio.get("uiSoundEntries", []) if entry.get("assetType") == "page_flip_sound"), None)
    ambient_entries = [entry for entry in audio.get("ambientEntries", []) if entry.get("storyId") in complete_ids or any(f"/books/{slug}/" in entry.get("outputFile", "") for slug in complete_slugs)]
    sfx_entries = audio.get("sfxEntries", [])

    errors: list[str] = []
    warnings: list[str] = []

    if args.level in {"demo", "generated-draft", "production", "release-candidate"}:
        if len(scene_entries) != expected_scene_count:
            errors.append(f"Expected {expected_scene_count} complete-book scene entries, found {len(scene_entries)}.")
        missing_files = [entry.get("outputFile") for entry in scene_entries if not entry.get("outputFile") or not (CONTENT / entry["outputFile"]).exists()]
        if missing_files:
            errors.append(f"Scene entries with missing output files: {len(missing_files)}.")
        if len(cover_entries) != len(complete_ids):
            errors.append(f"Expected {len(complete_ids)} complete-book cover entries, found {len(cover_entries)}.")
        missing_cover_files = [entry.get("outputFile") for entry in cover_entries if not entry.get("outputFile") or not (CONTENT / entry["outputFile"]).exists()]
        if missing_cover_files:
            errors.append(f"Cover entries with missing output files: {len(missing_cover_files)}.")
        if len(narration_entries) != expected_narration_entries:
            errors.append(f"Expected {expected_narration_entries} complete-book narration entries, found {len(narration_entries)}.")
        missing_narration_files = [entry.get("outputFile") for entry in narration_entries if not entry.get("outputFile") or not (CONTENT / entry["outputFile"]).exists()]
        if missing_narration_files:
            errors.append(f"Narration entries with missing output files: {len(missing_narration_files)}.")
        placeholder_narration = [entry for entry in narration_entries if best_status(entry) == "placeholder"]
        if args.level in {"generated-draft", "production"} and placeholder_narration:
            errors.append(f"{len(placeholder_narration)} narration entries still resolve to placeholder audio.")
        if page_turn is None:
            errors.append("Page-turn sound entry is missing.")
        elif not page_turn.get("outputFile") or not (CONTENT / page_turn["outputFile"]).exists():
            errors.append("Page-turn sound output file is missing.")
        if len(ambient_entries) < len(complete_ids):
            errors.append(f"Expected ambient loops for {len(complete_ids)} complete books, found {len(ambient_entries)}.")
        missing_ambient_files = [entry.get("outputFile") for entry in ambient_entries if not entry.get("outputFile") or not (CONTENT / entry["outputFile"]).exists()]
        if missing_ambient_files:
            errors.append(f"Ambient entries with missing output files: {len(missing_ambient_files)}.")

    if args.level in {"generated-draft", "production", "release-candidate"}:
        placeholder_scenes = [entry for entry in scene_entries if best_status(entry) == "placeholder"]
        placeholder_covers = [entry for entry in cover_entries if best_status(entry) == "placeholder"]
        if placeholder_scenes:
            errors.append(f"{len(placeholder_scenes)} complete-book scenes still resolve to placeholder art.")
        if placeholder_covers:
            errors.append(f"{len(placeholder_covers)} complete-book covers still resolve to placeholder art.")
        if page_turn and best_status(page_turn) == "placeholder":
            errors.append("Page-turn sound still resolves to placeholder.")
        placeholder_ambient = [entry for entry in ambient_entries if best_status(entry) == "placeholder"]
        if placeholder_ambient:
            errors.append(f"{len(placeholder_ambient)} ambient loops still resolve to placeholder.")
        placeholder_sfx = [entry for entry in sfx_entries if best_status(entry) == "placeholder"]
        if placeholder_sfx:
            errors.append(f"{len(placeholder_sfx)} sound-design SFX entries still resolve to placeholder.")
        if not sfx_entries:
            errors.append("Sound-design SFX entries are missing.")
        missing_sfx_files = [entry.get("outputFile") for entry in sfx_entries if not entry.get("outputFile") or not (CONTENT / entry["outputFile"]).exists()]
        if missing_sfx_files:
            errors.append(f"Sound-design SFX entries with missing output files: {len(missing_sfx_files)}.")
        missing_drafts = [entry for entry in scene_entries if best_status(entry) not in {"generated_draft", "generated_reviewed", "commissioned_draft", "commissioned_reviewed", "commissioned_final"}]
        if missing_drafts:
            errors.append(f"{len(missing_drafts)} scenes do not have generated-draft-or-better art.")

    if args.level in {"production", "release-candidate"}:
        nonfinal_scenes = [entry for entry in scene_entries if best_status(entry) != "commissioned_final"]
        nonfinal_covers = [entry for entry in cover_entries if best_status(entry) != "commissioned_final"]
        nonfinal_narration = [entry for entry in narration_entries if best_status(entry) != "human_recorded_final"]
        if nonfinal_scenes:
            errors.append(f"{len(nonfinal_scenes)} scene images are not commissioned_final.")
        if nonfinal_covers:
            errors.append(f"{len(nonfinal_covers)} covers are not commissioned_final.")
        if nonfinal_narration:
            errors.append(f"{len(nonfinal_narration)} narration files are not human_recorded_final.")

    if args.level == "release-candidate":
        required_repo_files = [
            "backend/openapi.yaml",
            "docs/compliance_kids_safety.md",
            "docs/payments_native_vs_revenuecat_decision.md",
            "docs/entitlement_rules.md",
            "ios/MoonJarStoriesiOSApp/Config/Production.xcconfig",
            "android/MoonJarStoriesAndroid/build.gradle.kts",
        ]
        for relative in required_repo_files:
            if not (ROOT / relative).exists():
                errors.append(f"Release-candidate gate requires `{relative}`.")
        errors.extend(
            [
                "Release-candidate gate requires deployed backend receipt/token verification evidence.",
                "Release-candidate gate requires App Store / Play Console product IDs configured and tested.",
                "Release-candidate gate requires privacy policy/legal review signoff.",
                "Release-candidate gate requires human creative, cultural, child-safety, and audio review signoff.",
                "Release-candidate gate requires release signing and store screenshot/listing evidence.",
            ]
        )
    else:
        final_scene_count = sum(1 for entry in scene_entries if best_status(entry) == "commissioned_final")
        final_narration_count = sum(1 for entry in narration_entries if best_status(entry) == "human_recorded_final")
        if final_scene_count == 0:
            warnings.append("No scene images are final; this is not production-ready.")
        if final_narration_count == 0:
            warnings.append("No narration files are human-recorded final; this is not production-ready.")

    image_counts = Counter(best_status(entry) for entry in scene_entries)
    audio_counts = Counter(best_status(entry) for entry in narration_entries)
    print(f"Moon Jar {args.level} readiness check")
    print(f"Scene image statuses: {dict(sorted(image_counts.items()))}")
    print(f"Narration statuses: {dict(sorted(audio_counts.items()))}")
    print(f"Page-turn status: {best_status(page_turn or {})}")
    print(f"Ambient statuses: {dict(sorted(Counter(best_status(entry) for entry in ambient_entries).items()))}")
    if sfx_entries:
        print(f"SFX statuses: {dict(sorted(Counter(best_status(entry) for entry in sfx_entries).items()))}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Moon Jar {args.level} readiness passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
