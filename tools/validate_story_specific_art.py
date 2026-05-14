#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
CHARACTER_MANIFEST = CONTENT / "assets" / "manifests" / "character_art_manifest.json"
REPORT = ROOT / "tools" / "output" / "story_specific_art_audit.md"

BAD_RENDERERS = {
    "local_static_storyboard_renderer",
    "deterministic_repo_renderer",
    "moonjar_static_placeholder_renderer",
}
STORY_SPECIFIC_RENDERER = "local_story_specific_svg_renderer"
STORY_SPECIFIC_RUNTIME_RENDERERS = {
    STORY_SPECIFIC_RENDERER,
    "built_in_image_gen_sheet_importer",
    "built_in_image_gen_story_specific_scene",
}
REVIEWED_OR_FINAL = {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}
MIN_STORY_SPECIFIC_BYTES = 180_000


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def asset_exists(relative: str | None) -> bool:
    return isinstance(relative, str) and bool(relative) and (CONTENT / relative).exists()


def bad_renderer(entry: dict[str, Any]) -> str | None:
    fields = [entry.get("generationTool"), entry.get("generationModel")]
    for candidate in entry.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("outputFile") == entry.get("outputFile"):
            fields.extend([candidate.get("provider"), candidate.get("model")])
    for value in fields:
        if isinstance(value, str) and value in BAD_RENDERERS:
            return value
    return None


def file_size(relative: str | None) -> int:
    if not asset_exists(relative):
        return 0
    return (CONTENT / str(relative)).stat().st_size


def dimensions_ok(entry: dict[str, Any]) -> bool:
    dimensions = entry.get("dimensions")
    if not isinstance(dimensions, dict):
        return False
    width = dimensions.get("width")
    height = dimensions.get("height")
    return isinstance(width, int) and isinstance(height, int) and width >= 512 and height >= 512


def selected_candidate(entry: dict[str, Any]) -> dict[str, Any] | None:
    selected = entry.get("outputFile")
    for candidate in entry.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("outputFile") == selected:
            return candidate
    return None


def candidate_has_story_specific_evidence(entry: dict[str, Any]) -> bool:
    candidate = selected_candidate(entry)
    if entry.get("visualSpecificity") == "story_specific_illustration" and entry.get("placeholderLike") is False:
        return True
    return bool(
        isinstance(candidate, dict)
        and candidate.get("visualSpecificity") == "story_specific_illustration"
        and candidate.get("placeholderLike") is False
    )


def validate_art_entry(
    entry: dict[str, Any],
    *,
    context: str,
    premium: bool,
    errors: list[str],
) -> list[str]:
    gaps: list[str] = []
    output = entry.get("outputFile")
    renderer = bad_renderer(entry)
    if entry.get("status") not in REVIEWED_OR_FINAL:
        gaps.append(f"status {entry.get('status')!r} is not reviewed/final")
    if not asset_exists(output):
        gaps.append(f"missing output {output!r}")
    if not dimensions_ok(entry):
        gaps.append("missing or unsafe dimensions")
    if renderer:
        gaps.append(f"selected old abstract renderer `{renderer}`")
    if entry.get("placeholderLike") is True:
        gaps.append("placeholderLike is true")
    if premium:
        if entry.get("generationTool") not in STORY_SPECIFIC_RUNTIME_RENDERERS:
            expected = ", ".join(sorted(STORY_SPECIFIC_RUNTIME_RENDERERS))
            gaps.append(f"premium selected generationTool is {entry.get('generationTool')!r}, expected one of `{expected}`")
        if not candidate_has_story_specific_evidence(entry):
            gaps.append("missing story-specific illustration evidence")
        if file_size(output) < MIN_STORY_SPECIFIC_BYTES:
            gaps.append(f"selected file is too small for generated story-specific art: {file_size(output)} bytes")
    for gap in gaps:
        errors.append(f"{context}: {gap}")
    return gaps


def main() -> int:
    catalog = load(CATALOG)
    image_manifest = load(IMAGE_MANIFEST)
    character_manifest = load(CHARACTER_MANIFEST) if CHARACTER_MANIFEST.exists() else {"entries": []}
    character_entries = {
        entry.get("bookId"): entry
        for entry in character_manifest.get("entries", [])
        if isinstance(entry, dict)
    }

    scenes_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    scenes_by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in image_manifest.get("sceneEntries", []):
        if isinstance(entry, dict):
            scenes_by_key[(entry.get("storyId"), entry.get("sceneId"))] = entry
            scenes_by_book[str(entry.get("storyId"))].append(entry)

    covers_by_book = {
        entry.get("storyId"): entry
        for entry in image_manifest.get("coverEntries", [])
        if isinstance(entry, dict)
    }

    errors: list[str] = []
    rows = [
        "# Story-Specific Art Audit",
        "",
        "This audit validates current repo artifacts. It fails if selected runtime art still uses the old abstract static renderer or if premium catalog art lacks story-specific evidence.",
        "",
        "| Book | Access | Scenes | Scene Art | Cover Art | Character Sheet | Gaps |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]

    total_scenes = 0
    story_specific_premium_scenes = 0
    story_specific_premium_covers = 0

    for catalog_entry in catalog.get("books", []):
        if catalog_entry.get("status") != "complete":
            continue
        book_path = catalog_entry.get("bookPath")
        if not isinstance(book_path, str):
            errors.append(f"{catalog_entry.get('id')}: missing bookPath")
            continue
        book = load(CONTENT / book_path)
        book_id = book["id"]
        premium = catalog_entry.get("access") == "premium"
        pages = book.get("pages", [])
        total_scenes += len(pages)

        book_gaps: list[str] = []
        scene_gaps = 0
        for page in pages:
            entry = scenes_by_key.get((book_id, page.get("id")))
            if not entry:
                errors.append(f"{book_id} {page.get('id')}: missing scene image manifest entry")
                book_gaps.append("missing scene manifest entry")
                scene_gaps += 1
                continue
            gaps = validate_art_entry(
                entry,
                context=f"{book_id} {page.get('id')}",
                premium=premium,
                errors=errors,
            )
            if gaps:
                scene_gaps += 1
            elif premium:
                story_specific_premium_scenes += 1

        cover = covers_by_book.get(book_id)
        cover_ok = False
        if not cover:
            errors.append(f"{book_id}: missing cover manifest entry")
            book_gaps.append("missing cover manifest entry")
        else:
            gaps = validate_art_entry(cover, context=f"{book_id} cover", premium=premium, errors=errors)
            cover_ok = not gaps
            if gaps:
                book_gaps.append("cover")
            elif premium:
                story_specific_premium_covers += 1

        bible_relative = book.get("characterBible")
        sheet_ok = False
        if not isinstance(bible_relative, str) or not (CONTENT / bible_relative).exists():
            errors.append(f"{book_id}: missing character bible")
            book_gaps.append("missing character bible")
        else:
            bible = load(CONTENT / bible_relative)
            sheet = bible.get("characterSheetAsset")
            manifest_entry = character_entries.get(book_id)
            if not asset_exists(sheet):
                errors.append(f"{book_id}: characterSheetAsset missing on disk: {sheet!r}")
                book_gaps.append("missing character sheet file")
            elif not manifest_entry:
                errors.append(f"{book_id}: missing character art manifest entry")
                book_gaps.append("missing character art manifest entry")
            elif manifest_entry.get("outputFile") != sheet:
                errors.append(f"{book_id}: character art manifest output does not match bible characterSheetAsset")
                book_gaps.append("character manifest mismatch")
            elif manifest_entry.get("status") not in REVIEWED_OR_FINAL:
                errors.append(f"{book_id}: character sheet status is not reviewed/final")
                book_gaps.append("character sheet status")
            elif manifest_entry.get("generationTool") == STORY_SPECIFIC_RENDERER:
                sheet_ok = True
            else:
                errors.append(f"{book_id}: character sheet generationTool is not story-specific")
                book_gaps.append("character sheet renderer")

        scene_status = "pass" if scene_gaps == 0 else f"{scene_gaps} gap(s)"
        cover_status = "pass" if cover_ok else "gap"
        sheet_status = "pass" if sheet_ok else "gap"
        rows.append(
            "| "
            f"{catalog_entry.get('slug')} | "
            f"{catalog_entry.get('access')} | "
            f"{len(pages)} | "
            f"{scene_status} | "
            f"{cover_status} | "
            f"{sheet_status} | "
            f"{'; '.join(sorted(set(book_gaps))) if book_gaps else 'none'} |"
        )

    rows.extend(
        [
            "",
            "## Totals",
            "",
            f"- Complete scenes checked: {total_scenes}",
            f"- Premium story-specific scenes checked: {story_specific_premium_scenes}",
            f"- Premium story-specific covers checked: {story_specific_premium_covers}",
            f"- Character sheets checked: {len(character_entries)}",
            "",
            "## Rule",
            "",
            "- Free-book imported/image-generated art may remain as selected runtime art.",
            "- Premium-book selected runtime art must use either the story-specific local renderer or the reviewed built-in sheet importer, and carry `visualSpecificity: story_specific_illustration`.",
            "- No selected runtime art may use `local_static_storyboard_renderer` or `deterministic_repo_renderer`.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    if errors:
        print("Story-specific art validation failed:")
        for error in errors[:80]:
            print(f"- {error}")
        if len(errors) > 80:
            print(f"... {len(errors) - 80} more issue(s)")
        print(f"Report: {REPORT.relative_to(ROOT)}")
        return 1

    print("Story-specific art validation passed.")
    print(f"- Complete scenes checked: {total_scenes}")
    print(f"- Premium story-specific scenes: {story_specific_premium_scenes}")
    print(f"- Premium story-specific covers: {story_specific_premium_covers}")
    print(f"- Character sheets: {len(character_entries)}")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
