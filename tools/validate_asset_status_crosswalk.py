#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"
REPORT = ROOT / "tools" / "output" / "asset_status_crosswalk_report.md"

IMAGE_DRAFT_OR_BETTER = {"generated_draft", "generated_reviewed", "commissioned_draft", "commissioned_reviewed", "commissioned_final"}
AUDIO_DRAFT_OR_BETTER = {"synthetic_draft", "synthetic_reviewed", "human_recorded_draft", "human_recorded_reviewed", "human_recorded_final"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    catalog = load(CATALOG)
    image_manifest = load(IMAGE_MANIFEST)
    audio_manifest = load(AUDIO_MANIFEST)
    image_by_key = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in image_manifest.get("sceneEntries", [])}
    audio_by_key = {
        (entry.get("storyId"), entry.get("sceneId"), entry.get("language")): entry
        for entry in audio_manifest.get("narrationEntries", [])
    }
    cover_by_story = {entry.get("storyId"): entry for entry in image_manifest.get("coverEntries", [])}

    errors: list[str] = []
    rows = [
        "# Asset Status Crosswalk Report",
        "",
        "Book JSON asset fields are fallback metadata. Runtime asset status is resolved from manifests by priority: final, reviewed, draft, placeholder.",
        "",
        "| Book | Pages | Manifest scene status | Book image fallback status | Narration status | Cover manifest status |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]

    for catalog_entry in catalog["books"]:
        if catalog_entry.get("status") != "complete":
            continue
        book = load(CONTENT / catalog_entry["bookPath"])
        book_id = book["id"]
        scene_statuses: set[str] = set()
        fallback_image_statuses: set[str] = set()
        narration_statuses: set[str] = set()
        for page in book["pages"]:
            scene_entry = image_by_key.get((book_id, page["id"]))
            if scene_entry is None:
                errors.append(f"{book['slug']} page {page['pageNumber']}: missing image manifest entry.")
            else:
                scene_status = scene_entry.get("status")
                scene_statuses.add(str(scene_status))
                if scene_status not in IMAGE_DRAFT_OR_BETTER:
                    errors.append(f"{book['slug']} page {page['pageNumber']}: manifest image status is not draft-or-better: {scene_status!r}.")
            fallback_image_statuses.add(str(page.get("imageAssetStatus", "missing")))

            for language in ("en", "ko"):
                audio_entry = audio_by_key.get((book_id, page["id"], language))
                if audio_entry is None:
                    errors.append(f"{book['slug']} page {page['pageNumber']} {language}: missing narration manifest entry.")
                else:
                    audio_status = audio_entry.get("status")
                    narration_statuses.add(str(audio_status))
                    if audio_status not in AUDIO_DRAFT_OR_BETTER:
                        errors.append(f"{book['slug']} page {page['pageNumber']} {language}: narration status is not draft-or-better: {audio_status!r}.")

        cover_status = cover_by_story.get(book_id, {}).get("status")
        if cover_status not in IMAGE_DRAFT_OR_BETTER:
            errors.append(f"{book['slug']}: cover manifest status is not draft-or-better: {cover_status!r}.")
        if fallback_image_statuses != {"placeholder"}:
            errors.append(f"{book['slug']}: book JSON imageAssetStatus should remain explicit fallback placeholder metadata, got {sorted(fallback_image_statuses)}.")

        rows.append(
            "| {title} | {pages} | {scene} | {fallback} | {audio} | {cover} |".format(
                title=book["title"]["en"],
                pages=len(book["pages"]),
                scene=", ".join(sorted(scene_statuses)),
                fallback=", ".join(sorted(fallback_image_statuses)),
                audio=", ".join(sorted(narration_statuses)),
                cover=cover_status,
            )
        )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    if errors:
        print("Moon Jar asset status crosswalk failed:")
        for error in errors:
            print(f"- {error}")
        print(f"Report: {REPORT.relative_to(ROOT)}")
        return 1

    print("Moon Jar asset status crosswalk passed: manifests provide draft-or-better runtime assets while book JSON keeps fallback placeholders explicit.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
