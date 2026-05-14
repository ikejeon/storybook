#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from asset_pipeline_common import (
    AUDIO,
    AUDIO_STATUSES,
    CONTENT,
    REVIEW_FIELDS,
    complete_books,
    content_path,
    existing_or_none,
    page_asset_name,
    utc_now,
    write_json,
)
from providers.macos_say import wav_duration
from providers.registry import get_audio_provider, get_sound_provider

AUDIO_MANIFEST = AUDIO / "manifests" / "audio_manifest.json"
PROMPT_EXPORT = Path("tools/output/audio_prompts.md")


def review_defaults() -> dict:
    return {
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": "",
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }


def audio_priority(status: str) -> int:
    order = ["human_recorded_final", "human_recorded_reviewed", "synthetic_reviewed", "human_recorded_draft", "synthetic_draft", "placeholder"]
    return order.index(status) if status in order else len(order)


def best_candidate(candidates: list[dict]) -> dict | None:
    existing = [item for item in candidates if item.get("outputFile") and (CONTENT / item["outputFile"]).exists()]
    return sorted(existing, key=lambda item: audio_priority(item.get("status", "")))[0] if existing else None


def infer_language(asset_type: str | None) -> str:
    return "en" if asset_type == "english_narration" else "ko"


def existing_narration_entries() -> dict[tuple[str, str, str], dict]:
    if not AUDIO_MANIFEST.exists():
        return {}
    manifest = json.loads(AUDIO_MANIFEST.read_text(encoding="utf-8"))
    entries: dict[tuple[str, str, str], dict] = {}
    for entry in manifest.get("narrationEntries", []):
        if not isinstance(entry, dict):
            continue
        story_id = entry.get("storyId")
        scene_id = entry.get("sceneId")
        if not story_id or not scene_id:
            continue
        language = entry.get("language") or infer_language(entry.get("assetType"))
        normalized = dict(entry)
        normalized["language"] = language
        entries[(story_id, scene_id, language)] = normalized
    return entries


def make_candidate(output_file: str, status: str, result, *, text: str | None = None, source_file: str | None = None) -> dict:
    candidate = {
        "outputFile": output_file,
        "status": status,
        "provider": result.provider if result else "not_run",
        "tool": result.provider if result else "not_run",
        "model": result.model if result else None,
        "generationStatus": result.generation_status if result else "not_run",
        "timestamp": utc_now(),
        "duration": round(result.duration or 0.0, 3) if result and result.duration is not None else None,
        "normalization": result.normalization if result else None,
        "sourceFile": source_file,
        "text": text,
    }
    if result and result.metadata:
        candidate.update(result.metadata)
    candidate.update(review_defaults())
    return candidate


def manifest_for_sound(asset_type: str, source_relative: str, output_relative: str, description: str, *, dry_run: bool) -> dict:
    source = existing_or_none(source_relative)
    result = None
    if not dry_run and source:
        provider = get_sound_provider("placeholder")
        result = provider.generate_or_import(description, content_path(output_relative), source_file=source)
    candidate = make_candidate(output_relative, "placeholder", result, text=description, source_file=source_relative)
    best = best_candidate([candidate])
    return {
        "assetType": asset_type,
        "outputFile": best["outputFile"] if best else output_relative,
        "tool": best["tool"] if best else "placeholder",
        "model": best["model"] if best else None,
        "duration": best.get("duration") if best else (round(wav_duration(content_path(output_relative)) or 0.0, 3) if content_path(output_relative).exists() else None),
        "status": best["status"] if best else "placeholder",
        "generationStatus": best["generationStatus"] if best else "not_run",
        "candidates": [candidate],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate offline narration audio for Moon Jar Stories.")
    parser.add_argument("--provider", default="macos_say", choices=["macos_say", "external_korean_tts", "external_english_tts"])
    parser.add_argument("--languages", default="en", help="Comma-separated narration languages to generate: en, ko, or both. Existing entries for other languages are preserved.")
    parser.add_argument("--voice", default="Grandma (Korean (South Korea))")
    parser.add_argument("--english-voice", default="Samantha")
    parser.add_argument("--rate", type=int, default=155)
    parser.add_argument("--target-peak-db", type=float, default=-3.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    requested_languages = {item.strip().lower() for item in args.languages.split(",") if item.strip()}
    if "both" in requested_languages:
        requested_languages = {"en", "ko"}
    invalid_languages = requested_languages - {"en", "ko"}
    if invalid_languages:
        parser.error(f"Unsupported language(s): {', '.join(sorted(invalid_languages))}")
    if not requested_languages:
        parser.error("--languages must include en, ko, or both")

    generated_at = utc_now()
    narration_entries: list[dict] = []
    ambient_entries: list[dict] = []
    seen_ambient: set[str] = set()
    generated_now = 0

    provider = get_audio_provider(
        args.provider,
        korean_voice=args.voice,
        english_voice=args.english_voice,
        rate=args.rate,
        target_peak_db=args.target_peak_db,
    )
    preserved_entries = existing_narration_entries()

    for _catalog_entry, _book_path, book in complete_books():
        for page in book["pages"]:
            for language in ("en", "ko"):
                existing = preserved_entries.get((book["id"], page["id"], language))
                if language not in requested_languages and existing:
                    narration_entries.append(existing)
                    continue

                output = f"audio/synthetic-draft/narration/{book['slug']}/{language}/{page_asset_name(page['pageNumber'], 'wav')}"
                text = page["englishText"] if language == "en" else page["narrationScript"]
                result = None
                if not args.dry_run:
                    if language == "en":
                        result = provider.synthesize_english(text, content_path(output))
                    else:
                        result = provider.synthesize_korean(text, content_path(output))
                    if result.generation_status == "generated":
                        generated_now += 1
                candidate = make_candidate(output, "synthetic_draft", result, text=text)
                best = best_candidate([candidate])
                voice = args.english_voice if language == "en" else args.voice
                narration_entries.append(
                    {
                        "assetType": "english_narration" if language == "en" else "korean_narration",
                        "language": language,
                        "storyId": book["id"],
                        "storySlug": book["slug"],
                        "sceneId": page["id"],
                        "pageNumber": page["pageNumber"],
                        "koreanNarrationText": page["narrationScript"],
                        "englishNarrationText": page["englishText"],
                        "outputFile": best["outputFile"] if best else output,
                        "voice": best.get("voice", voice) if best else voice,
                        "tool": best["tool"] if best else args.provider,
                        "model": best["model"] if best else None,
                        "timestamp": generated_at,
                        "duration": best.get("duration") if best else None,
                        "normalization": best.get("normalization") if best else None,
                        "status": best["status"] if best else "synthetic_draft",
                        "generationStatus": best["generationStatus"] if best else "not_run",
                        "candidates": [candidate],
                    }
                )

            ambient = page.get("ambientAudio")
            if ambient and ambient not in seen_ambient:
                seen_ambient.add(ambient)
                slug = book["slug"]
                ambient_entries.append(
                    manifest_for_sound(
                        "ambient_loop",
                        ambient,
                        f"audio/placeholders/books/{slug}/ambient/ambient-loop.wav",
                        f"Soft bedtime ambient loop for {book['title']['en']}",
                        dry_run=args.dry_run,
                    )
                )

    ui_sound_entries = [
        manifest_for_sound("page_flip_sound", "audio/ui/page-flip.wav", "audio/placeholders/ui/page-flip.wav", "Quiet child-safe page turn", dry_run=args.dry_run),
        manifest_for_sound("button_tap_sound", "audio/ui/button-tap.wav", "audio/placeholders/ui/button-tap.wav", "Quiet child-safe button tap", dry_run=args.dry_run),
    ]

    manifest = {
        "schemaVersion": "1.1.0",
        "generatedAt": generated_at,
        "promptSource": str(PROMPT_EXPORT),
        "provider": args.provider,
        "defaultNarrationLanguage": "en",
        "optionalNarrationLanguages": ["ko"],
        "assetPriority": ["final", "reviewed", "synthetic_draft", "placeholder"],
        "statusVocabulary": sorted(AUDIO_STATUSES),
        "reviewFields": REVIEW_FIELDS,
        "notes": [
            "No TTS or audio generation runs inside the child app.",
            "English narration is the default demo experience; Korean narration remains optional.",
            "Apps resolve outputFile from this manifest; story JSON can stay stable as audio improves.",
            "Synthetic drafts must be replaced or reviewed before production release.",
        ],
        "narrationEntries": narration_entries,
        "ambientEntries": ambient_entries,
        "uiSoundEntries": ui_sound_entries,
    }
    if not args.dry_run:
        write_json(AUDIO_MANIFEST, manifest)

    print(f"Audio manifest ready: {AUDIO_MANIFEST.relative_to(CONTENT.parent)} ({len(narration_entries)} entries, generated this run {generated_now}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
