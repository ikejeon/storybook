#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
CHARACTER_INDEX = CONTENT / "characters" / "index.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
BOOK_SCHEMA = CONTENT / "schemas" / "book.schema.json"

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

FINAL_IMAGE_STATUSES = {"commissioned_final"}
FINAL_AUDIO_STATUSES = {"human_recorded_final"}
REVIEWED_IMAGE_STATUSES = {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}
REVIEWED_AUDIO_STATUSES = {"synthetic_reviewed", "human_recorded_reviewed", "human_recorded_final"}

REQUIRED_BOOK_FIELDS = {
    "schemaVersion",
    "id",
    "slug",
    "title",
    "access",
    "ageRange",
    "summary",
    "themes",
    "characters",
    "pages",
}

REQUIRED_PAGE_FIELDS = {
    "id",
    "pageNumber",
    "text",
    "koreanText",
    "englishText",
    "narrationScript",
    "vocabulary",
    "storyBeat",
    "imagePrompt",
    "audioPrompt",
    "animation",
}

REQUIRED_TEXT_LEVEL_FIELDS = {
    "enLittle",
    "enStandard",
    "koLittle",
    "koStandard",
}

REQUIRED_STORY_BEAT_FIELDS = {
    "purpose",
    "emotion",
    "pageTurnHook",
    "readAloudCue",
    "childInteraction",
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_status(value: Any, allowed: set[str], context: str, errors: list[str]) -> None:
    require(isinstance(value, str) and value in allowed, f"{context}: invalid status {value!r}", errors)


def validate_page(book_path: Path, book_id: str, page: dict, expected_number: int, seen_page_ids: set[str], errors: list[str]) -> None:
    missing = REQUIRED_PAGE_FIELDS - page.keys()
    require(not missing, f"{book_path}: page {expected_number} missing fields: {sorted(missing)}", errors)
    require(page.get("pageNumber") == expected_number, f"{book_path}: expected pageNumber {expected_number}, got {page.get('pageNumber')}", errors)

    page_id = page.get("id")
    require(isinstance(page_id, str) and page_id, f"{book_path}: page {expected_number} has empty id", errors)
    require(page_id not in seen_page_ids, f"{book_path}: duplicate page id {page_id}", errors)
    if isinstance(page_id, str):
        seen_page_ids.add(page_id)

    for field in ("koreanText", "englishText", "narrationScript", "imagePrompt", "audioPrompt"):
        require(isinstance(page.get(field), str) and page[field].strip(), f"{book_path}: {book_id} page {expected_number} empty {field}", errors)

    text_levels = page.get("text")
    require(isinstance(text_levels, dict), f"{book_path}: {book_id} page {expected_number} text must be an object", errors)
    if isinstance(text_levels, dict):
        missing_text_levels = REQUIRED_TEXT_LEVEL_FIELDS - text_levels.keys()
        require(not missing_text_levels, f"{book_path}: {book_id} page {expected_number} missing text levels: {sorted(missing_text_levels)}", errors)
        for field in REQUIRED_TEXT_LEVEL_FIELDS:
            require(isinstance(text_levels.get(field), str) and text_levels[field].strip(), f"{book_path}: {book_id} page {expected_number} empty text.{field}", errors)
        require(text_levels.get("enStandard") == page.get("englishText"), f"{book_path}: {book_id} page {expected_number} englishText must match text.enStandard", errors)
        require(text_levels.get("koStandard") == page.get("koreanText"), f"{book_path}: {book_id} page {expected_number} koreanText must match text.koStandard", errors)

    story_beat = page.get("storyBeat")
    require(isinstance(story_beat, dict), f"{book_path}: {book_id} page {expected_number} storyBeat must be an object", errors)
    if isinstance(story_beat, dict):
        missing_story_beat = REQUIRED_STORY_BEAT_FIELDS - story_beat.keys()
        require(not missing_story_beat, f"{book_path}: {book_id} page {expected_number} missing storyBeat fields: {sorted(missing_story_beat)}", errors)
        for field in REQUIRED_STORY_BEAT_FIELDS:
            require(isinstance(story_beat.get(field), str) and story_beat[field].strip(), f"{book_path}: {book_id} page {expected_number} empty storyBeat.{field}", errors)

    for field in ("imageAsset", "narrationAudio"):
        value = page.get(field)
        require(isinstance(value, str) and value.strip(), f"{book_path}: {book_id} page {expected_number} missing {field}", errors)
        if isinstance(value, str) and value.strip():
            asset_path = CONTENT / value
            require(asset_path.exists(), f"{book_path}: {book_id} page {expected_number} {field} does not exist: {asset_path}", errors)

    image_status = page.get("imageAssetStatus", "placeholder")
    audio_status = page.get("narrationAudioStatus", "placeholder")
    require_status(image_status, IMAGE_STATUSES, f"{book_path}: {book_id} page {expected_number} imageAssetStatus", errors)
    require_status(audio_status, AUDIO_STATUSES, f"{book_path}: {book_id} page {expected_number} narrationAudioStatus", errors)
    require(
        not (image_status in {"generated_reviewed", "commissioned_final"} and page.get("imageAsset", "").startswith("assets/books/")),
        f"{book_path}: {book_id} page {expected_number} legacy placeholder image path is marked production-ready",
        errors,
    )
    require(
        not (audio_status == "human_recorded_final" and page.get("audioGenerationTool") == "macos_say"),
        f"{book_path}: {book_id} page {expected_number} synthetic TTS is marked human_recorded_final",
        errors,
    )

    for field in ("imageSource", "ambientAudio"):
        value = page.get(field)
        if value:
            asset_path = CONTENT / value
            require(asset_path.exists(), f"{book_path}: {book_id} page {expected_number} {field} does not exist: {asset_path}", errors)

    vocabulary = page.get("vocabulary")
    require(isinstance(vocabulary, list) and vocabulary, f"{book_path}: page {expected_number} needs at least one vocabulary item", errors)
    if isinstance(vocabulary, list):
        for idx, item in enumerate(vocabulary, start=1):
            require(isinstance(item, dict), f"{book_path}: page {expected_number} vocabulary {idx} is not an object", errors)
            require(bool(item.get("ko")) and bool(item.get("en")), f"{book_path}: page {expected_number} vocabulary {idx} needs ko/en", errors)
            require(bool(item.get("definitionEn")) and bool(item.get("definitionKo")), f"{book_path}: page {expected_number} vocabulary {idx} needs definitionEn/definitionKo", errors)

    animation = page.get("animation")
    require(isinstance(animation, dict), f"{book_path}: page {expected_number} animation is not an object", errors)
    if isinstance(animation, dict):
        require(bool(animation.get("type")), f"{book_path}: page {expected_number} animation.type is empty", errors)
        require(isinstance(animation.get("loopDuration"), (int, float)), f"{book_path}: page {expected_number} animation.loopDuration must be numeric", errors)
        layers = animation.get("layers")
        require(isinstance(layers, list) and layers, f"{book_path}: page {expected_number} animation.layers must not be empty", errors)
        if isinstance(layers, list):
            for idx, layer in enumerate(layers, start=1):
                require(isinstance(layer, dict), f"{book_path}: page {expected_number} layer {idx} is not an object", errors)
                require(bool(layer.get("name")) and bool(layer.get("motion")), f"{book_path}: page {expected_number} layer {idx} needs name/motion", errors)


def validate_book(book_path: Path, expected_id: str, expected_access: str, expected_pages: int, errors: list[str]) -> dict:
    book = load_json(book_path)
    missing = REQUIRED_BOOK_FIELDS - book.keys()
    require(not missing, f"{book_path}: missing fields: {sorted(missing)}", errors)
    require(book.get("id") == expected_id, f"{book_path}: expected id {expected_id}, got {book.get('id')}", errors)
    require(book.get("access") == expected_access, f"{book_path}: expected access {expected_access}, got {book.get('access')}", errors)

    cover_asset = book.get("coverAsset")
    require(isinstance(cover_asset, str) and cover_asset.strip(), f"{book_path}: missing coverAsset", errors)
    if isinstance(cover_asset, str) and cover_asset.strip():
        require((CONTENT / cover_asset).exists(), f"{book_path}: coverAsset does not exist: {CONTENT / cover_asset}", errors)
    require_status(book.get("coverAssetStatus", "placeholder"), IMAGE_STATUSES, f"{book_path}: coverAssetStatus", errors)

    character_bible = book.get("characterBible")
    require(isinstance(character_bible, str) and character_bible.strip(), f"{book_path}: missing characterBible", errors)
    if isinstance(character_bible, str) and character_bible.strip():
        require((CONTENT / character_bible).exists(), f"{book_path}: characterBible does not exist: {CONTENT / character_bible}", errors)

    pages = book.get("pages")
    require(isinstance(pages, list), f"{book_path}: pages must be a list", errors)
    if isinstance(pages, list):
        require(20 <= len(pages) <= 40, f"{book_path}: complete books must have 20-40 pages, got {len(pages)}", errors)
        require(len(pages) == expected_pages, f"{book_path}: catalog pageTarget is {expected_pages}, got {len(pages)}", errors)
        seen_page_ids: set[str] = set()
        for expected_number, page in enumerate(pages, start=1):
            validate_page(book_path, expected_id, page, expected_number, seen_page_ids, errors)
            page_bible = page.get("characterBible", character_bible)
            require(page_bible == character_bible, f"{book_path}: page {expected_number} characterBible does not match book characterBible", errors)

    return book


def validate_character_bibles(records: list[tuple[dict, Path, dict]], errors: list[str]) -> None:
    require(CHARACTER_INDEX.exists(), f"missing character index: {CHARACTER_INDEX}", errors)
    if not CHARACTER_INDEX.exists():
        return

    index = load_json(CHARACTER_INDEX)
    entries = {
        item.get("bookId"): item.get("characterBible")
        for item in index.get("books", [])
        if isinstance(item, dict)
    }

    required_fields = {
        "schemaVersion",
        "bookId",
        "slug",
        "characterSheetPrompt",
        "mainCharacterDescriptions",
        "styleRules",
        "forbiddenVisualElements",
        "sceneContinuityNotes",
        "promptPrefix",
        "masterArtStylePrompt",
        "perCharacterVisualIdentity",
        "outfitRules",
        "colorPalette",
        "facialExpressionRules",
        "ageBodyProportionRules",
        "doNotChangeRules",
        "recurringObjectRules",
        "negativePrompt",
    }

    for _catalog_entry, book_path, book in records:
        bible_path_value = entries.get(book["id"])
        require(isinstance(bible_path_value, str) and bible_path_value, f"{CHARACTER_INDEX}: missing bible entry for {book['id']}", errors)
        if not isinstance(bible_path_value, str):
            continue
        require(book.get("characterBible") == bible_path_value, f"{book_path}: book characterBible does not match character index", errors)
        bible_path = CONTENT / bible_path_value
        require(bible_path.exists(), f"{CHARACTER_INDEX}: character bible does not exist: {bible_path}", errors)
        if not bible_path.exists():
            continue
        bible = load_json(bible_path)
        missing = required_fields - bible.keys()
        require(not missing, f"{bible_path}: missing fields: {sorted(missing)}", errors)
        require(bible.get("bookId") == book["id"], f"{bible_path}: expected bookId {book['id']}, got {bible.get('bookId')}", errors)
        require(isinstance(bible.get("mainCharacterDescriptions"), list) and bible["mainCharacterDescriptions"], f"{bible_path}: missing mainCharacterDescriptions", errors)
        for character in bible.get("mainCharacterDescriptions", []):
            require(bool(character.get("id")), f"{bible_path}: character missing id", errors)
            require(bool(character.get("description")), f"{bible_path}: character {character.get('id')} missing description", errors)
            require(bool(character.get("recurringOutfitAndColors")), f"{bible_path}: character {character.get('id')} missing recurringOutfitAndColors", errors)
            require(bool(character.get("continuityNotes")), f"{bible_path}: character {character.get('id')} missing continuityNotes", errors)


def validate_image_manifest(records: list[tuple[dict, Path, dict]], errors: list[str]) -> None:
    require(IMAGE_MANIFEST.exists(), f"missing image manifest: {IMAGE_MANIFEST}", errors)
    if not IMAGE_MANIFEST.exists():
        return
    manifest = load_json(IMAGE_MANIFEST)
    require(set(manifest.get("statusVocabulary", [])) == IMAGE_STATUSES, f"{IMAGE_MANIFEST}: statusVocabulary mismatch", errors)

    scene_entries = manifest.get("sceneEntries")
    cover_entries = manifest.get("coverEntries")
    icon_entries = manifest.get("appIconConcepts")
    require(isinstance(scene_entries, list), f"{IMAGE_MANIFEST}: sceneEntries must be a list", errors)
    require(isinstance(cover_entries, list), f"{IMAGE_MANIFEST}: coverEntries must be a list", errors)
    require(isinstance(icon_entries, list) and len(icon_entries) >= 3, f"{IMAGE_MANIFEST}: expected at least 3 appIconConcepts", errors)
    if not isinstance(scene_entries, list) or not isinstance(cover_entries, list):
        return

    scenes_by_key = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in scene_entries if isinstance(entry, dict)}
    covers_by_story = {entry.get("storyId"): entry for entry in cover_entries if isinstance(entry, dict)}

    for _catalog_entry, _book_path, book in records:
        cover_entry = covers_by_story.get(book["id"])
        require(isinstance(cover_entry, dict), f"{IMAGE_MANIFEST}: missing cover entry for {book['id']}", errors)
        if isinstance(cover_entry, dict):
                validate_image_manifest_entry(cover_entry, f"{IMAGE_MANIFEST}: cover {book['id']}", errors)

        for page in book["pages"]:
            entry = scenes_by_key.get((book["id"], page["id"]))
            require(isinstance(entry, dict), f"{IMAGE_MANIFEST}: missing scene entry for {book['id']} {page['id']}", errors)
            if isinstance(entry, dict):
                validate_image_manifest_entry(entry, f"{IMAGE_MANIFEST}: scene {book['id']} {page['id']}", errors)
                require(bool(entry.get("prompt")), f"{IMAGE_MANIFEST}: scene {book['id']} {page['id']} missing prompt", errors)
                require("style/moonjar_style_bible.json" in entry.get("prompt", ""), f"{IMAGE_MANIFEST}: scene {book['id']} {page['id']} prompt missing global style bible reference", errors)

    for idx, entry in enumerate(icon_entries or [], start=1):
        if isinstance(entry, dict):
            validate_image_manifest_entry(entry, f"{IMAGE_MANIFEST}: app icon {idx}", errors)


def validate_review_fields(entry: dict, status: str, final_statuses: set[str], reviewed_statuses: set[str], context: str, errors: list[str]) -> None:
    if status == "rejected":
        require(bool(entry.get("rejectionReason")), f"{context}: rejected asset needs rejectionReason", errors)
    if status in reviewed_statuses:
        require(bool(entry.get("reviewer")), f"{context}: reviewed/final asset needs reviewer", errors)
        require(bool(entry.get("reviewDate")), f"{context}: reviewed/final asset needs reviewDate", errors)
        require(entry.get("culturalReviewStatus") == "approved", f"{context}: reviewed/final asset needs culturalReviewStatus=approved", errors)
        require(entry.get("childSafetyReviewStatus") == "approved", f"{context}: reviewed/final asset needs childSafetyReviewStatus=approved", errors)
    if status in final_statuses:
        require(entry.get("productionApprovalStatus") == "approved", f"{context}: final asset needs productionApprovalStatus=approved", errors)


def validate_candidates(entry: dict, allowed: set[str], final_statuses: set[str], reviewed_statuses: set[str], context: str, errors: list[str]) -> None:
    candidates = entry.get("candidates")
    if candidates is None:
        return
    require(isinstance(candidates, list) and candidates, f"{context}: candidates must be a non-empty list", errors)
    for idx, candidate in enumerate(candidates or [], start=1):
        if not isinstance(candidate, dict):
            errors.append(f"{context}: candidate {idx} is not an object")
            continue
        status = candidate.get("status")
        require_status(status, allowed, f"{context}: candidate {idx} status", errors)
        output = candidate.get("outputFile")
        require(isinstance(output, str) and output, f"{context}: candidate {idx} missing outputFile", errors)
        if isinstance(output, str) and output:
            require((CONTENT / output).exists(), f"{context}: candidate {idx} outputFile does not exist: {CONTENT / output}", errors)
        validate_review_fields(candidate, status, final_statuses, reviewed_statuses, f"{context}: candidate {idx}", errors)


def validate_image_manifest_entry(entry: dict, context: str, errors: list[str]) -> None:
    for field in ("outputFile", "generationTool", "timestamp", "status", "generationStatus"):
        require(bool(entry.get(field)), f"{context}: missing {field}", errors)
    status = entry.get("status")
    require_status(status, IMAGE_STATUSES, f"{context} status", errors)
    output = entry.get("outputFile")
    if isinstance(output, str) and output:
        require((CONTENT / output).exists(), f"{context}: outputFile does not exist: {CONTENT / output}", errors)
    generation_text = f"{entry.get('generationTool')} {entry.get('generationStatus')}".lower()
    require(
        not (entry.get("status") in REVIEWED_IMAGE_STATUSES and "placeholder" in generation_text),
        f"{context}: placeholder generation is marked production-ready",
        errors,
    )
    validate_review_fields(entry, status, FINAL_IMAGE_STATUSES, REVIEWED_IMAGE_STATUSES, context, errors)
    validate_candidates(entry, IMAGE_STATUSES, FINAL_IMAGE_STATUSES, REVIEWED_IMAGE_STATUSES, context, errors)


def validate_audio_manifest(records: list[tuple[dict, Path, dict]], errors: list[str]) -> None:
    require(AUDIO_MANIFEST.exists(), f"missing audio manifest: {AUDIO_MANIFEST}", errors)
    if not AUDIO_MANIFEST.exists():
        return
    manifest = load_json(AUDIO_MANIFEST)
    require(set(manifest.get("statusVocabulary", [])) == AUDIO_STATUSES, f"{AUDIO_MANIFEST}: statusVocabulary mismatch", errors)

    narration_entries = manifest.get("narrationEntries")
    require(isinstance(narration_entries, list), f"{AUDIO_MANIFEST}: narrationEntries must be a list", errors)
    if not isinstance(narration_entries, list):
        return
    entries_by_key = {}
    for entry in narration_entries:
        if not isinstance(entry, dict):
            continue
        language = entry.get("language") or ("en" if entry.get("assetType") == "english_narration" else "ko")
        key = (entry.get("storyId"), entry.get("sceneId"), language)
        require(key not in entries_by_key, f"{AUDIO_MANIFEST}: duplicate narration entry for {key}", errors)
        entries_by_key[key] = entry

    for _catalog_entry, _book_path, book in records:
        for page in book["pages"]:
            english_entry = entries_by_key.get((book["id"], page["id"], "en"))
            require(isinstance(english_entry, dict), f"{AUDIO_MANIFEST}: missing English narration entry for {book['id']} {page['id']}", errors)
            if isinstance(english_entry, dict):
                validate_audio_manifest_entry(english_entry, f"{AUDIO_MANIFEST}: English narration {book['id']} {page['id']}", errors)
                require(english_entry.get("assetType") == "english_narration", f"{AUDIO_MANIFEST}: English narration has wrong assetType for {book['id']} {page['id']}", errors)
                require(english_entry.get("englishNarrationText") == page.get("englishText"), f"{AUDIO_MANIFEST}: English narration text mismatch for {book['id']} {page['id']}", errors)

            korean_entry = entries_by_key.get((book["id"], page["id"], "ko"))
            if isinstance(korean_entry, dict):
                validate_audio_manifest_entry(korean_entry, f"{AUDIO_MANIFEST}: Korean narration {book['id']} {page['id']}", errors)
                require(korean_entry.get("assetType") == "korean_narration", f"{AUDIO_MANIFEST}: Korean narration has wrong assetType for {book['id']} {page['id']}", errors)
                require(korean_entry.get("koreanNarrationText") == page.get("narrationScript"), f"{AUDIO_MANIFEST}: Korean narration text mismatch for {book['id']} {page['id']}", errors)

    for group in ("ambientEntries", "uiSoundEntries"):
        value = manifest.get(group)
        require(isinstance(value, list), f"{AUDIO_MANIFEST}: {group} must be a list", errors)
        for idx, entry in enumerate(value or [], start=1):
            if isinstance(entry, dict):
                validate_audio_manifest_entry(entry, f"{AUDIO_MANIFEST}: {group} {idx}", errors)


def validate_audio_manifest_entry(entry: dict, context: str, errors: list[str]) -> None:
    for field in ("outputFile", "tool", "status", "generationStatus"):
        require(bool(entry.get(field)), f"{context}: missing {field}", errors)
    status = entry.get("status")
    require_status(status, AUDIO_STATUSES, f"{context} status", errors)
    output = entry.get("outputFile")
    if isinstance(output, str) and output:
        require((CONTENT / output).exists(), f"{context}: outputFile does not exist: {CONTENT / output}", errors)
    require(
        not (entry.get("status") == "human_recorded_final" and entry.get("tool") == "macos_say"),
        f"{context}: macOS synthetic narration is marked human_recorded_final",
        errors,
    )
    validate_review_fields(entry, status, FINAL_AUDIO_STATUSES, REVIEWED_AUDIO_STATUSES, context, errors)
    validate_candidates(entry, AUDIO_STATUSES, FINAL_AUDIO_STATUSES, REVIEWED_AUDIO_STATUSES, context, errors)


def validate_layer_manifest(records: list[tuple[dict, Path, dict]], errors: list[str]) -> None:
    require(LAYER_MANIFEST.exists(), f"missing layer manifest: {LAYER_MANIFEST}", errors)
    if not LAYER_MANIFEST.exists():
        return
    manifest = load_json(LAYER_MANIFEST)
    valid_types = set(manifest.get("validAnimationTypes", []))
    scenes = manifest.get("scenes")
    require(isinstance(scenes, list), f"{LAYER_MANIFEST}: scenes must be a list", errors)
    if not isinstance(scenes, list):
        return
    scenes_by_key = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in scenes if isinstance(entry, dict)}
    required_roles = {"background", "midground", "character", "foreground", "effect", "particle_glow"}

    for _catalog_entry, _book_path, book in records:
        for page in book["pages"]:
            animation_type = page.get("animation", {}).get("type")
            require(animation_type in valid_types, f"{LAYER_MANIFEST}: animation type not registered: {animation_type}", errors)
            entry = scenes_by_key.get((book["id"], page["id"]))
            require(isinstance(entry, dict), f"{LAYER_MANIFEST}: missing layer plan for {book['id']} {page['id']}", errors)
            if isinstance(entry, dict):
                require(entry.get("animationType") == animation_type, f"{LAYER_MANIFEST}: animation mismatch for {book['id']} {page['id']}", errors)
                planned = entry.get("plannedLayers")
                require(isinstance(planned, list), f"{LAYER_MANIFEST}: plannedLayers missing for {book['id']} {page['id']}", errors)
                roles = {layer.get("role") for layer in planned or [] if isinstance(layer, dict)}
                require(required_roles <= roles, f"{LAYER_MANIFEST}: missing layer roles for {book['id']} {page['id']}: {sorted(required_roles - roles)}", errors)
                for layer in planned or []:
                    if not isinstance(layer, dict):
                        continue
                    output = layer.get("outputFile")
                    require(isinstance(output, str) and output, f"{LAYER_MANIFEST}: layer outputFile missing for {book['id']} {page['id']} {layer.get('role')}", errors)
                    if isinstance(output, str) and output:
                        require((CONTENT / output).exists(), f"{LAYER_MANIFEST}: layer outputFile does not exist for {book['id']} {page['id']} {layer.get('role')}: {output}", errors)
                    require(layer.get("status") == "generated_reviewed", f"{LAYER_MANIFEST}: layer status must be generated_reviewed for {book['id']} {page['id']} {layer.get('role')}", errors)


def validate_schema_alignment(errors: list[str]) -> None:
    require(BOOK_SCHEMA.exists(), f"missing book schema: {BOOK_SCHEMA}", errors)
    if not BOOK_SCHEMA.exists():
        return

    schema = load_json(BOOK_SCHEMA)
    book_required = set(schema.get("required", []))
    require(REQUIRED_BOOK_FIELDS <= book_required, f"{BOOK_SCHEMA}: schema required fields lag validator: {sorted(REQUIRED_BOOK_FIELDS - book_required)}", errors)
    for field in ("coverAsset", "coverAssetStatus", "characterBible", "narrationAudioStatus"):
        require(field in book_required, f"{BOOK_SCHEMA}: schema should require `{field}` because validate_books.py enforces it", errors)

    page_schema = schema.get("properties", {}).get("pages", {}).get("items", {})
    page_properties = set(page_schema.get("properties", {}).keys())
    page_required = set(page_schema.get("required", []))
    require(REQUIRED_PAGE_FIELDS <= page_required, f"{BOOK_SCHEMA}: page required fields lag validator: {sorted(REQUIRED_PAGE_FIELDS - page_required)}", errors)
    require("refrain" in page_properties, f"{BOOK_SCHEMA}: page schema should allow optional read-aloud `refrain` fields", errors)

    text_required = set(page_schema.get("properties", {}).get("text", {}).get("required", []))
    require(REQUIRED_TEXT_LEVEL_FIELDS <= text_required, f"{BOOK_SCHEMA}: text variant required fields lag validator: {sorted(REQUIRED_TEXT_LEVEL_FIELDS - text_required)}", errors)

    story_beat_required = set(page_schema.get("properties", {}).get("storyBeat", {}).get("required", []))
    require(REQUIRED_STORY_BEAT_FIELDS <= story_beat_required, f"{BOOK_SCHEMA}: storyBeat required fields lag validator: {sorted(REQUIRED_STORY_BEAT_FIELDS - story_beat_required)}", errors)

    vocabulary_required = set(page_schema.get("properties", {}).get("vocabulary", {}).get("items", {}).get("required", []))
    require({"ko", "en", "definitionEn", "definitionKo"} <= vocabulary_required, f"{BOOK_SCHEMA}: vocabulary schema must require child-friendly definitions", errors)

    image_status_schema = set(page_schema.get("properties", {}).get("imageAssetStatus", {}).get("enum", []))
    audio_status_schema = set(page_schema.get("properties", {}).get("narrationAudioStatus", {}).get("enum", []))
    require(IMAGE_STATUSES <= image_status_schema, f"{BOOK_SCHEMA}: imageAssetStatus enum missing statuses: {sorted(IMAGE_STATUSES - image_status_schema)}", errors)
    require(AUDIO_STATUSES <= audio_status_schema, f"{BOOK_SCHEMA}: narrationAudioStatus enum missing statuses: {sorted(AUDIO_STATUSES - audio_status_schema)}", errors)


def main() -> int:
    errors: list[str] = []
    catalog = load_json(CATALOG)
    books = catalog.get("books")
    require(isinstance(books, list) and books, f"{CATALOG}: books must be a non-empty list", errors)

    seen_book_ids: set[str] = set()
    complete_count = 0
    free_count = 0
    complete_book_ids: set[str] = set()
    premium_entries = 0
    complete_records: list[tuple[dict, Path, dict]] = []

    if isinstance(books, list):
        for entry in books:
            book_id = entry.get("id")
            require(isinstance(book_id, str) and book_id, f"{CATALOG}: catalog entry missing id", errors)
            require(book_id not in seen_book_ids, f"{CATALOG}: duplicate book id {book_id}", errors)
            if isinstance(book_id, str):
                seen_book_ids.add(book_id)

            if entry.get("access") == "free":
                free_count += 1
            if entry.get("access") == "premium":
                premium_entries += 1

            if entry.get("status") == "complete":
                complete_count += 1
                if isinstance(book_id, str):
                    complete_book_ids.add(book_id)
                path_value = entry.get("bookPath")
                require(isinstance(path_value, str) and path_value, f"{CATALOG}: complete book {book_id} missing bookPath", errors)
                if isinstance(path_value, str):
                    book_path = CONTENT / path_value
                    require(book_path.exists(), f"{CATALOG}: complete book path does not exist: {book_path}", errors)
                    if book_path.exists():
                        book = validate_book(book_path, book_id, entry.get("access"), entry.get("pageTarget"), errors)
                        complete_records.append((entry, book_path, book))

    require(free_count == catalog.get("monetization", {}).get("freeBooks"), f"{CATALOG}: freeBooks count mismatch", errors)
    require(complete_count == len(seen_book_ids), f"{CATALOG}: expected all catalog books to be complete, got {complete_count}/{len(seen_book_ids)}", errors)
    require(premium_entries == len(seen_book_ids) - free_count, f"{CATALOG}: premium/free access mismatch", errors)
    require(all(book_id.startswith("book.") for book_id in complete_book_ids), f"{CATALOG}: complete book ids must be stable book.* ids", errors)
    for entry in books or []:
        if entry.get("access") == "premium":
            require(entry.get("status") == "complete", f"{CATALOG}: premium book {entry.get('id')} should have complete shared-content payload", errors)
            require(isinstance(entry.get("bookPath"), str) and entry.get("bookPath"), f"{CATALOG}: premium book {entry.get('id')} should stay entitlement-locked by access, not by missing content", errors)

    validate_character_bibles(complete_records, errors)
    validate_image_manifest(complete_records, errors)
    validate_audio_manifest(complete_records, errors)
    validate_layer_manifest(complete_records, errors)
    validate_schema_alignment(errors)

    if errors:
        print("Moon Jar content validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Moon Jar content validation passed: {len(seen_book_ids)} catalog books, {complete_count} complete books.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
