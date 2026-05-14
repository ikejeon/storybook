#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
from hashlib import sha256
from pathlib import Path
from typing import Any

from story_asset_semantic_expectations import expected_panel_for_page

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
REPORT = ROOT / "tools" / "output" / "premium_asset_quality_parity_report.md"

SHEET_IMPORTER = "built_in_image_gen_sheet_importer"
LOCAL_STORY_RENDERER = "local_story_specific_svg_renderer"
SINGLE_SCENE_IMAGEGEN = "built_in_image_gen_story_specific_scene"
ACCEPTED_SELECTED_RENDERERS = {LOCAL_STORY_RENDERER, SINGLE_SCENE_IMAGEGEN}
MIN_PREMIUM_BYTES = 180_000
EXPECTED_SIZE = (960, 640)

SINGLE_SCENE_EXCEPTIONS: dict[tuple[str, int], str] = {
    ("fairy-and-woodcutter", 16): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-016.png",
    ("fairy-and-woodcutter", 28): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-028.png",
}


def runtime_priority(status: str | None) -> int:
    if status in {"commissioned_final", "human_recorded_final"}:
        return 0
    if status in {"commissioned_reviewed", "generated_reviewed", "human_recorded_reviewed", "synthetic_reviewed"}:
        return 1
    if status in {"commissioned_draft", "generated_draft", "human_recorded_draft", "synthetic_draft"}:
        return 2
    if status == "placeholder":
        return 3
    return 9


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def asset_gaps(entry: dict[str, Any], *, context: str) -> list[str]:
    gaps: list[str] = []
    output = entry.get("outputFile")
    if not isinstance(output, str) or not output:
        return [f"{context}: missing outputFile"]
    path = CONTENT / output
    if not path.exists():
        return [f"{context}: missing selected file {output!r}"]
    if path.stat().st_size < MIN_PREMIUM_BYTES:
        gaps.append(f"{context}: selected file is too small for premium demo art ({path.stat().st_size} bytes)")
    dimensions = png_dimensions(path)
    if dimensions != EXPECTED_SIZE:
        gaps.append(f"{context}: selected PNG dimensions are {dimensions}, expected {EXPECTED_SIZE}")
    if entry.get("status") != "generated_reviewed":
        gaps.append(f"{context}: status is {entry.get('status')!r}, expected generated_reviewed")
    if entry.get("productionApprovalStatus") != "not_approved":
        gaps.append(f"{context}: generated art must remain productionApprovalStatus not_approved")
    if entry.get("visualSpecificity") != "story_specific_illustration" or entry.get("placeholderLike") is not False:
        gaps.append(f"{context}: missing story-specific non-placeholder evidence")
    return gaps


def file_hash(relative: str | None) -> str | None:
    if not isinstance(relative, str) or not relative:
        return None
    path = CONTENT / relative
    if not path.exists():
        return None
    return sha256(path.read_bytes()).hexdigest()


def runtime_selected_candidate(entry: dict[str, Any]) -> dict[str, Any] | None:
    existing_candidates = [
        candidate
        for candidate in entry.get("candidates", [])
        if isinstance(candidate, dict)
        and isinstance(candidate.get("outputFile"), str)
        and (CONTENT / candidate["outputFile"]).exists()
    ]
    if existing_candidates:
        return min(existing_candidates, key=lambda candidate: runtime_priority(candidate.get("status")))
    output = entry.get("outputFile")
    if isinstance(output, str) and (CONTENT / output).exists():
        return {
            "outputFile": output,
            "status": entry.get("status"),
            "provider": entry.get("generationTool"),
            "generationStatus": entry.get("generationStatus"),
        }
    return None


def runtime_selection_gaps(
    entry: dict[str, Any],
    *,
    context: str,
    expected_output: str | None = None,
) -> list[str]:
    selected = runtime_selected_candidate(entry)
    if selected is None:
        return [f"{context}: Android runtime resolver has no existing selected candidate"]
    gaps: list[str] = []
    if expected_output is not None and selected.get("outputFile") != expected_output:
        gaps.append(
            f"{context}: Android runtime would select {selected.get('outputFile')!r}, expected {expected_output!r}"
        )
    provider = selected.get("provider")
    if provider not in ACCEPTED_SELECTED_RENDERERS:
        gaps.append(
            f"{context}: Android runtime selected provider {provider!r}, expected one of {sorted(ACCEPTED_SELECTED_RENDERERS)!r}"
        )
    return gaps


def main() -> int:
    catalog = load(CATALOG)
    manifest = load(IMAGE_MANIFEST)
    scene_entries = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in manifest.get("sceneEntries", [])}
    cover_entries = {entry.get("storyId"): entry for entry in manifest.get("coverEntries", [])}

    errors: list[str] = []
    rows = [
        "# Premium Asset Quality Parity Report",
        "",
        "This gate prevents the premium catalog from selecting a small set of reused sheet panels or stale flat assets as if they were page-specific premium reader art. It does not claim final commissioned art.",
        "",
        "| Story | Pages | Cover Renderer | Scene Renderers | Gaps |",
        "| --- | ---: | --- | --- | --- |",
    ]

    for catalog_entry in catalog.get("books", []):
        if catalog_entry.get("status") != "complete" or catalog_entry.get("access") != "premium":
            continue
        slug = catalog_entry.get("slug")
        book_id = catalog_entry.get("id")
        book_path = catalog_entry.get("bookPath")
        if not isinstance(slug, str) or not isinstance(book_id, str) or not isinstance(book_path, str):
            errors.append(f"Malformed premium catalog entry: {catalog_entry!r}")
            continue

        book = load(CONTENT / book_path)
        sheet = f"assets/generated-draft/images/story-sheets/{slug}.png"
        if not (CONTENT / sheet).exists():
            errors.append(f"{slug}: missing richer premium story sheet {sheet}")
            continue

        story_gaps: list[str] = []
        cover = cover_entries.get(book_id)
        cover_renderer = cover.get("generationTool") if isinstance(cover, dict) else "missing"
        if not isinstance(cover, dict):
            story_gaps.append("missing cover manifest entry")
        else:
            story_gaps.extend(asset_gaps(cover, context=f"{slug} cover"))
            cover_output = cover.get("outputFile")
            if isinstance(cover_output, str):
                story_gaps.extend(
                    runtime_selection_gaps(
                        cover,
                        context=f"{slug} cover",
                        expected_output=cover_output,
                    )
                )
            if cover.get("generationTool") not in ACCEPTED_SELECTED_RENDERERS:
                story_gaps.append(
                    f"cover selected renderer is {cover.get('generationTool')!r}; expected page-specific selected renderer {sorted(ACCEPTED_SELECTED_RENDERERS)!r}"
                )
            if cover.get("generationTool") == SHEET_IMPORTER:
                story_gaps.append("cover must not be the same selected crop as page 1; use page-specific cover art")

        scene_renderers: dict[str, int] = {}
        scene_hashes: dict[str, list[int]] = {}
        for page in book.get("pages", []):
            page_number = page.get("pageNumber")
            page_id = page.get("id")
            context = f"{slug} page {page_number}"
            if not isinstance(page_number, int) or not isinstance(page_id, str):
                story_gaps.append(f"{context}: malformed page metadata")
                continue
            entry = scene_entries.get((book_id, page_id))
            if not isinstance(entry, dict):
                story_gaps.append(f"{context}: missing scene manifest entry")
                continue
            renderer = str(entry.get("generationTool"))
            scene_renderers[renderer] = scene_renderers.get(renderer, 0) + 1
            story_gaps.extend(asset_gaps(entry, context=context))
            digest = file_hash(entry.get("outputFile"))
            if digest:
                scene_hashes.setdefault(digest, []).append(page_number)

            exception_output = SINGLE_SCENE_EXCEPTIONS.get((slug, page_number))
            if exception_output:
                story_gaps.extend(
                    runtime_selection_gaps(
                        entry,
                        context=context,
                        expected_output=exception_output,
                    )
                )
                if entry.get("generationTool") != SINGLE_SCENE_IMAGEGEN:
                    story_gaps.append(f"{context}: expected story-specific single-scene ImageGen exception, got {entry.get('generationTool')!r}")
                if entry.get("outputFile") != exception_output:
                    story_gaps.append(f"{context}: expected exception output {exception_output!r}, got {entry.get('outputFile')!r}")
                if entry.get("sourceSheet") is not None or entry.get("panelIndex") is not None:
                    story_gaps.append(f"{context}: single-scene exception must not claim sourceSheet/panelIndex")
                continue

            if entry.get("generationTool") not in ACCEPTED_SELECTED_RENDERERS:
                story_gaps.append(
                    f"{context}: selected renderer is {entry.get('generationTool')!r}; expected page-specific selected renderer {sorted(ACCEPTED_SELECTED_RENDERERS)!r}"
                )
            entry_output = entry.get("outputFile")
            if isinstance(entry_output, str):
                story_gaps.extend(
                    runtime_selection_gaps(
                        entry,
                        context=context,
                        expected_output=entry_output,
                    )
                )
            if entry.get("generationTool") == SHEET_IMPORTER:
                if entry.get("sourceSheet") != sheet:
                    story_gaps.append(f"{context}: sourceSheet is {entry.get('sourceSheet')!r}, expected {sheet!r}")
                expected_panel = expected_panel_for_page(slug, page_number)
                if entry.get("panelIndex") != expected_panel:
                    story_gaps.append(f"{context}: panelIndex is {entry.get('panelIndex')!r}, expected {expected_panel}")
                story_gaps.append(f"{context}: selected runtime art still comes from a six-panel sheet crop")
            elif entry.get("sourceSheet") is not None or entry.get("panelIndex") is not None:
                story_gaps.append(f"{context}: page-specific selected art must not claim sourceSheet/panelIndex")

        duplicate_groups = [pages for pages in scene_hashes.values() if len(pages) > 1]
        for pages in duplicate_groups[:8]:
            story_gaps.append(f"selected scene pixels reused across pages {pages}")
        cover_hash = file_hash(cover.get("outputFile")) if isinstance(cover, dict) else None
        if cover_hash and cover_hash in scene_hashes:
            story_gaps.append(f"cover pixels duplicate selected scene page(s) {scene_hashes[cover_hash]}")

        if story_gaps:
            errors.extend(f"{slug}: {gap}" for gap in story_gaps)
        rows.append(
            "| "
            f"{slug} | "
            f"{len(book.get('pages', []))} | "
            f"{cover_renderer} | "
            f"{', '.join(f'{key}:{value}' for key, value in sorted(scene_renderers.items())) or 'none'} | "
            f"{'; '.join(story_gaps[:6]) if story_gaps else 'pass'}"
            f"{' ...' if len(story_gaps) > 6 else ''} |"
        )

    rows.extend(["", "## Result", "", "PASS" if not errors else "FAIL", ""])
    if errors:
        rows.extend(f"- {error}" for error in errors)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    if errors:
        print(f"Premium asset quality parity validation failed; see {REPORT.relative_to(ROOT)}")
        for error in errors[:80]:
            print(f"- {error}")
        if len(errors) > 80:
            print(f"... {len(errors) - 80} more")
        return 1
    print("Premium asset quality parity validation passed.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
