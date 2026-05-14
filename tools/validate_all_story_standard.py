#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
CHARACTER_INDEX = CONTENT / "characters" / "index.json"
CHARACTER_ART_MANIFEST = CONTENT / "assets" / "manifests" / "character_art_manifest.json"
CULTURAL_REVIEW = CONTENT / "reviews" / "cultural_authenticity_review.json"
VISUAL_REVIEW = CONTENT / "reviews" / "visual_art_readiness_review.json"
ASSET_OWNERSHIP_LEDGER = CONTENT / "assets" / "manifests" / "asset_ownership_ledger.json"

IMAGE_RUNTIME_STATUSES = {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}
AUDIO_RUNTIME_STATUSES = {
    "synthetic_draft",
    "synthetic_reviewed",
    "human_recorded_draft",
    "human_recorded_reviewed",
    "human_recorded_final",
}
BAD_IMAGE_RENDERERS = {"local_static_storyboard_renderer", "deterministic_repo_renderer", "moonjar_static_placeholder_renderer"}
PREMIUM_STORY_SPECIFIC_RENDERER = "local_story_specific_svg_renderer"
PREMIUM_STORY_SPECIFIC_RUNTIME_RENDERERS = {
    PREMIUM_STORY_SPECIFIC_RENDERER,
    "built_in_image_gen_sheet_importer",
    "built_in_image_gen_story_specific_scene",
}
MIN_PREMIUM_STORY_SPECIFIC_BYTES = 180_000

CURRENT_TEXT_FILES = [
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "PRODUCT_SENSE.md",
    ROOT / "docs" / "SCORE_95_REQUIREMENTS.md",
    ROOT / "docs" / "exec-plans" / "active" / "harness-engineering.md",
    ROOT / "docs" / "exec-plans" / "active" / "all-story-standard.md",
    ROOT / "tools" / "complete_premium_content_visuals.py",
    ROOT / "tools" / "generate_product_completion_report.py",
    ROOT / "tools" / "score_art_experience.py",
    ROOT / "tools" / "score_reader_experience.py",
    ROOT / "tools" / "validate_cultural_authenticity.py",
    ROOT / "tools" / "validate_visual_system_readiness.py",
    CONTENT / "reviews" / "cultural_authenticity_review.json",
    CONTENT / "reviews" / "visual_art_readiness_review.json",
    CONTENT / "animation" / "runtime_animation_capabilities.json",
]

STALE_SUBSET_PATTERNS = {
    r"\bfive complete books\b": "Use all complete catalog books, not the old five-book subset.",
    r"\ball five complete\b": "Use all complete catalog books, not the old five-book subset.",
    r"\ball 5 complete\b": "Use all complete catalog books, not the old five-book subset.",
    r"\b5 complete books\b": "Use all complete catalog books, not the old five-book subset.",
    r"\b138[- ]scene\b": "Use current catalog-derived scene counts, not the old 138-scene subset.",
    r"\b138 scenes\b": "Use current catalog-derived scene counts, not the old 138-scene subset.",
    r"\b276[- ]narration\b": "Use current catalog-derived narration counts, not the old 276-narration subset.",
    r"\b276 narration\b": "Use current catalog-derived narration counts, not the old 276-narration subset.",
    r"\bmetadata-only\b": "Current app catalog stories should not be treated as metadata-only.",
    r"\bmetadata only\b": "Current app catalog stories should not be treated as metadata-only.",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def selected_output_exists(entry: dict[str, Any], context: str, errors: list[str]) -> None:
    output = entry.get("outputFile")
    require(isinstance(output, str) and output, f"{context}: missing outputFile", errors)
    if isinstance(output, str) and output:
        require((CONTENT / output).exists(), f"{context}: selected outputFile does not exist: {output}", errors)


def selected_output_size(entry: dict[str, Any]) -> int:
    output = entry.get("outputFile")
    if isinstance(output, str) and output and (CONTENT / output).exists():
        return (CONTENT / output).stat().st_size
    return 0


def uses_bad_image_renderer(entry: dict[str, Any]) -> str | None:
    values = [entry.get("generationTool"), entry.get("generationModel")]
    for candidate in entry.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("outputFile") == entry.get("outputFile"):
            values.extend([candidate.get("provider"), candidate.get("model")])
    for value in values:
        if isinstance(value, str) and value in BAD_IMAGE_RENDERERS:
            return value
    return None


def premium_story_specific_image(entry: dict[str, Any]) -> bool:
    return (
        entry.get("generationTool") in PREMIUM_STORY_SPECIFIC_RUNTIME_RENDERERS
        and entry.get("visualSpecificity") == "story_specific_illustration"
        and entry.get("placeholderLike") is False
        and selected_output_size(entry) >= MIN_PREMIUM_STORY_SPECIFIC_BYTES
    )


def catalog_books(errors: list[str]) -> list[dict[str, Any]]:
    catalog = load(CATALOG)
    books = catalog.get("books", [])
    require(isinstance(books, list) and books, "catalog: books must be a non-empty list", errors)
    ids = [book.get("id") for book in books]
    duplicates = [book_id for book_id, count in Counter(ids).items() if count > 1]
    require(not duplicates, f"catalog: duplicate book ids {duplicates}", errors)
    non_complete = [book.get("id") for book in books if book.get("status") != "complete"]
    require(
        not non_complete,
        "catalog: every app story must be complete; non-complete entries found: "
        + ", ".join(str(book_id) for book_id in non_complete),
        errors,
    )
    return books


def expected_pages(books: list[dict[str, Any]], errors: list[str]) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, str]]:
    pages: list[dict[str, Any]] = []
    page_counts: dict[str, int] = {}
    slugs: dict[str, str] = {}
    for entry in books:
        book_id = entry.get("id")
        slug = entry.get("slug")
        book_path = entry.get("bookPath")
        context = f"catalog[{book_id}]"
        require(isinstance(book_id, str) and book_id, f"{context}: missing id", errors)
        require(isinstance(slug, str) and slug, f"{context}: missing slug", errors)
        require(isinstance(book_path, str) and book_path, f"{context}: missing bookPath", errors)
        if not isinstance(book_id, str) or not isinstance(slug, str) or not isinstance(book_path, str):
            continue
        path = CONTENT / book_path
        require(path.exists(), f"{context}: bookPath does not exist: {book_path}", errors)
        if not path.exists():
            continue
        book = load(path)
        require(book.get("id") == book_id, f"{book_path}: id does not match catalog id {book_id}", errors)
        require(book.get("slug") == slug, f"{book_path}: slug does not match catalog slug {slug}", errors)
        book_pages = book.get("pages", [])
        require(isinstance(book_pages, list) and book_pages, f"{book_path}: pages must be non-empty", errors)
        target = entry.get("pageTarget")
        require(len(book_pages) == target, f"{book_path}: page count {len(book_pages)} does not match catalog pageTarget {target}", errors)
        seen_page_ids: set[str] = set()
        for expected_number, page in enumerate(book_pages if isinstance(book_pages, list) else [], start=1):
            page_id = page.get("id")
            require(isinstance(page_id, str) and page_id, f"{book_path}: page {expected_number} missing id", errors)
            require(page.get("pageNumber") == expected_number, f"{book_path}: page {page_id} has non-sequential pageNumber", errors)
            require(page_id not in seen_page_ids, f"{book_path}: duplicate page id {page_id}", errors)
            seen_page_ids.add(page_id)
            require(bool(page.get("englishText")), f"{book_path}: page {page_id} missing englishText", errors)
            require(bool(page.get("koreanText")), f"{book_path}: page {page_id} missing koreanText", errors)
            require(isinstance(page.get("storyBeat"), dict), f"{book_path}: page {page_id} missing storyBeat", errors)
            pages.append({"bookId": book_id, "slug": slug, "sceneId": page_id, "pageNumber": expected_number})
        page_counts[book_id] = len(book_pages) if isinstance(book_pages, list) else 0
        slugs[book_id] = slug
    return pages, page_counts, slugs


def validate_images(pages: list[dict[str, Any]], books: list[dict[str, Any]], errors: list[str]) -> None:
    manifest = load(IMAGE_MANIFEST)
    scene_entries = manifest.get("sceneEntries", [])
    cover_entries = manifest.get("coverEntries", [])
    access_by_book = {book.get("id"): book.get("access") for book in books}
    scene_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in (scene_entries if isinstance(scene_entries, list) else []):
        scene_by_key[(entry.get("storyId"), entry.get("sceneId"))].append(entry)
    for page in pages:
        context = f"image scene {page['bookId']} {page['sceneId']}"
        matches = scene_by_key.get((page["bookId"], page["sceneId"]), [])
        require(matches, f"{context}: missing manifest entry", errors)
        if matches:
            selected = matches[0]
            require(selected.get("status") in IMAGE_RUNTIME_STATUSES, f"{context}: status must be reviewed/final, got {selected.get('status')!r}", errors)
            require(selected.get("pageNumber") == page["pageNumber"], f"{context}: pageNumber mismatch", errors)
            selected_output_exists(selected, context, errors)
            require(bool(selected.get("characterBible")), f"{context}: missing characterBible", errors)
            bad_renderer = uses_bad_image_renderer(selected)
            require(not bad_renderer, f"{context}: selected runtime art still uses abstract renderer {bad_renderer!r}", errors)
            if access_by_book.get(page["bookId"]) == "premium":
                require(premium_story_specific_image(selected), f"{context}: premium selected runtime art must be story-specific, non-placeholder-like, and generated by an approved story-specific renderer/importer", errors)
    cover_by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in (cover_entries if isinstance(cover_entries, list) else []):
        cover_by_book[entry.get("storyId")].append(entry)
    for book in books:
        book_id = book["id"]
        context = f"image cover {book_id}"
        matches = cover_by_book.get(book_id, [])
        require(matches, f"{context}: missing cover entry", errors)
        if matches:
            selected = matches[0]
            require(selected.get("status") in IMAGE_RUNTIME_STATUSES, f"{context}: status must be reviewed/final, got {selected.get('status')!r}", errors)
            selected_output_exists(selected, context, errors)
            bad_renderer = uses_bad_image_renderer(selected)
            require(not bad_renderer, f"{context}: selected cover art still uses abstract renderer {bad_renderer!r}", errors)
            if access_by_book.get(book_id) == "premium":
                require(premium_story_specific_image(selected), f"{context}: premium selected cover art must be story-specific, non-placeholder-like, and generated by an approved story-specific renderer/importer", errors)


def validate_audio(pages: list[dict[str, Any]], books: list[dict[str, Any]], slugs: dict[str, str], errors: list[str]) -> None:
    manifest = load(AUDIO_MANIFEST)
    narration_entries = manifest.get("narrationEntries", [])
    narration_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in (narration_entries if isinstance(narration_entries, list) else []):
        narration_by_key[(entry.get("storyId"), entry.get("sceneId"), entry.get("language"))].append(entry)
    for page in pages:
        for language in ("en", "ko"):
            context = f"audio narration {page['bookId']} {page['sceneId']} {language}"
            matches = narration_by_key.get((page["bookId"], page["sceneId"], language), [])
            require(matches, f"{context}: missing narration entry", errors)
            if matches:
                selected = matches[0]
                require(selected.get("status") in AUDIO_RUNTIME_STATUSES, f"{context}: invalid status {selected.get('status')!r}", errors)
                selected_output_exists(selected, context, errors)
    ambient_entries = manifest.get("ambientEntries", [])
    ambient_outputs = [entry.get("outputFile", "") for entry in ambient_entries if isinstance(entry, dict)]
    for book in books:
        book_id = book["id"]
        slug = slugs[book_id]
        context = f"audio ambient {book_id}"
        matches = [entry for entry in ambient_entries if isinstance(entry, dict) and f"/{slug}/ambient/" in str(entry.get("outputFile", ""))]
        require(matches, f"{context}: missing ambient loop entry for slug {slug}", errors)
        if matches:
            selected = matches[0]
            require(selected.get("status") in AUDIO_RUNTIME_STATUSES, f"{context}: invalid status {selected.get('status')!r}", errors)
            selected_output_exists(selected, context, errors)
    require(len(ambient_outputs) >= len(books), "audio ambient: fewer ambient outputs than catalog books", errors)


def validate_layers(pages: list[dict[str, Any]], errors: list[str]) -> None:
    manifest = load(LAYER_MANIFEST)
    entries = manifest.get("scenes", [])
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in (entries if isinstance(entries, list) else []):
        by_key[(entry.get("storyId"), entry.get("sceneId"))].append(entry)
    for page in pages:
        context = f"layer plan {page['bookId']} {page['sceneId']}"
        matches = by_key.get((page["bookId"], page["sceneId"]), [])
        require(matches, f"{context}: missing layer plan", errors)
        if matches:
            selected = matches[0]
            require(selected.get("pageNumber") == page["pageNumber"], f"{context}: pageNumber mismatch", errors)
            require(isinstance(selected.get("plannedLayers"), list) and selected.get("plannedLayers"), f"{context}: missing plannedLayers", errors)
            for layer in selected.get("plannedLayers", []):
                if not isinstance(layer, dict):
                    continue
                output = layer.get("outputFile")
                role = layer.get("role")
                require(layer.get("status") == "generated_reviewed", f"{context}: layer {role} must be generated_reviewed", errors)
                require(isinstance(output, str) and output, f"{context}: layer {role} missing outputFile", errors)
                if isinstance(output, str) and output:
                    require((CONTENT / output).exists(), f"{context}: layer {role} outputFile missing on disk: {output}", errors)


def validate_book_level_artifacts(books: list[dict[str, Any]], page_counts: dict[str, int], errors: list[str]) -> None:
    complete_ids = {book["id"] for book in books}
    character_index = load(CHARACTER_INDEX)
    character_art = load(CHARACTER_ART_MANIFEST)
    character_books = character_index.get("books", [])
    character_ids = {entry.get("bookId") for entry in character_books if isinstance(entry, dict)}
    require(character_ids == complete_ids, f"character index: expected exactly {len(complete_ids)} catalog books, got missing {sorted(complete_ids - character_ids)} extra {sorted(character_ids - complete_ids)}", errors)
    for entry in (character_books if isinstance(character_books, list) else []):
        bible = entry.get("characterBible")
        if isinstance(bible, str):
            require((CONTENT / bible).exists(), f"character index {entry.get('bookId')}: bible file missing {bible}", errors)
            if (CONTENT / bible).exists():
                bible_data = load(CONTENT / bible)
                sheet = bible_data.get("characterSheetAsset")
                require(isinstance(sheet, str) and (CONTENT / sheet).exists(), f"character bible {entry.get('bookId')}: missing characterSheetAsset file", errors)
                require(bible_data.get("characterConsistencyStatus") == "generated_reviewed_story_specific_internal_demo", f"character bible {entry.get('bookId')}: missing story-specific character consistency status", errors)

    character_art_entries = character_art.get("entries", [])
    character_art_ids = {entry.get("bookId") for entry in character_art_entries if isinstance(entry, dict)}
    require(character_art_ids == complete_ids, f"character art manifest: expected exactly all catalog books; missing {sorted(complete_ids - character_art_ids)} extra {sorted(character_art_ids - complete_ids)}", errors)
    for entry in (character_art_entries if isinstance(character_art_entries, list) else []):
        output = entry.get("outputFile")
        require(entry.get("status") in IMAGE_RUNTIME_STATUSES, f"character art manifest {entry.get('bookId')}: status must be reviewed/final", errors)
        require(entry.get("generationTool") == PREMIUM_STORY_SPECIFIC_RENDERER, f"character art manifest {entry.get('bookId')}: expected story-specific renderer", errors)
        require(isinstance(output, str) and (CONTENT / output).exists(), f"character art manifest {entry.get('bookId')}: output missing on disk", errors)

    cultural_books = load(CULTURAL_REVIEW).get("books", {})
    visual_books = load(VISUAL_REVIEW).get("books", {})
    ownership_entries = load(ASSET_OWNERSHIP_LEDGER).get("entries", [])
    ownership_ids = {entry.get("bookId") for entry in ownership_entries if isinstance(entry, dict)}
    for label, found_ids in (
        ("cultural review", set(cultural_books.keys()) if isinstance(cultural_books, dict) else set()),
        ("visual review", set(visual_books.keys()) if isinstance(visual_books, dict) else set()),
        ("asset ownership ledger", ownership_ids),
    ):
        require(found_ids == complete_ids, f"{label}: expected exactly all catalog books; missing {sorted(complete_ids - found_ids)} extra {sorted(found_ids - complete_ids)}", errors)
    if isinstance(cultural_books, dict):
        for book_id, count in page_counts.items():
            entry = cultural_books.get(book_id, {})
            require(entry.get("sceneCount") == count, f"cultural review {book_id}: sceneCount {entry.get('sceneCount')} does not match {count}", errors)
    if isinstance(visual_books, dict):
        for book_id, count in page_counts.items():
            entry = visual_books.get(book_id, {})
            require(entry.get("sceneCount") == count, f"visual review {book_id}: sceneCount {entry.get('sceneCount')} does not match {count}", errors)
    for entry in (ownership_entries if isinstance(ownership_entries, list) else []):
        book_id = entry.get("bookId")
        if book_id in page_counts:
            require(entry.get("sceneCount") == page_counts[book_id], f"asset ownership ledger {book_id}: sceneCount {entry.get('sceneCount')} does not match {page_counts[book_id]}", errors)
            require(entry.get("coverCount") == 1, f"asset ownership ledger {book_id}: coverCount must be 1", errors)


def validate_current_text(errors: list[str]) -> None:
    for path in CURRENT_TEXT_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for pattern, fix in STALE_SUBSET_PATTERNS.items():
            match = re.search(pattern, text)
            if match:
                errors.append(f"{path.relative_to(ROOT)}: stale demo-subset phrase {match.group(0)!r}. {fix}")


def main() -> int:
    errors: list[str] = []
    books = catalog_books(errors)
    pages, page_counts, slugs = expected_pages(books, errors)
    validate_images(pages, books, errors)
    validate_audio(pages, books, slugs, errors)
    validate_layers(pages, errors)
    validate_book_level_artifacts(books, page_counts, errors)
    validate_current_text(errors)

    if errors:
        print("All-story standard validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    total_scenes = sum(page_counts.values())
    print("All-story standard validation passed.")
    print(f"- Catalog books covered: {len(books)}")
    print(f"- Complete scenes covered: {total_scenes}")
    print(f"- Required narration entries covered: {total_scenes * 2}")
    print("- Scene art, cover art, story-specific premium art, narration, ambient audio, layers, character bibles, character sheets, reviews, and ownership ledger are all catalog-wide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
