#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from story_asset_semantic_expectations import expected_panel_for_page as semantic_expected_panel_for_page

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
REPORT = ROOT / "tools" / "output" / "premium_imagegen_sheet_validation_report.md"

RENDERER = "built_in_image_gen_sheet_importer"
GENERATION_STATUS = "imported_from_six_panel_imagegen_sheet"
GENERATION_STATUS_PAGE_VARIANT = "imported_from_six_panel_imagegen_sheet_page_variant"
GENERATION_STATUSES = {GENERATION_STATUS, GENERATION_STATUS_PAGE_VARIANT}
MODEL = "built-in image_gen six_panel_story_sheet"
LOCAL_RENDERER = "local_story_specific_svg_renderer"
LOCAL_GENERATION_STATUS = "rendered_story_specific_painterly_panel"
LOCAL_MODEL = "moonjar_story_specific_painterly_svg_v3"
SINGLE_SCENE_RENDERER = "built_in_image_gen_story_specific_scene"
SINGLE_SCENE_GENERATION_STATUS = "generated_story_specific_scene"
SINGLE_SCENE_MODEL = "built-in image_gen story_specific_scene"
SINGLE_SCENE_EXCEPTIONS = {
    ("fairy-and-woodcutter", 16): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-016.png",
    ("fairy-and-woodcutter", 28): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-028.png",
}
EXPECTED_WIDTH = 960
EXPECTED_HEIGHT = 640
MIN_SHEET_WIDTH = 1536
MIN_SHEET_HEIGHT = 1024
MIN_PANEL_BYTES = 180_000

PANEL_OVERRIDES = {
    "fairy-and-woodcutter": [
        (1, 2, 1),
        (3, 4, 2),
        (5, 12, 3),
        (13, 14, 4),
        (15, 16, 5),
        (17, 32, 6),
    ],
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG with an IHDR header")
    width, height = struct.unpack(">II", header[16:24])
    return int(width), int(height)


def rel_exists(relative: str | None) -> bool:
    return isinstance(relative, str) and bool(relative) and (CONTENT / relative).exists()


def expected_panel_for_page(slug: str, page_number: int) -> int:
    for start, end, panel_index in PANEL_OVERRIDES.get(slug, []):
        if start <= page_number <= end:
            return panel_index
    return semantic_expected_panel_for_page(slug, page_number)


def image_ok(entry: dict[str, Any], *, expected_sheet: str, expected_panels: set[int], label: str) -> list[str]:
    errors: list[str] = []
    output = entry.get("outputFile")
    output_path = CONTENT / output if isinstance(output, str) else None
    dimensions = entry.get("dimensions")
    panel_index = entry.get("panelIndex")
    renderer = entry.get("generationTool")

    if renderer not in {RENDERER, LOCAL_RENDERER, SINGLE_SCENE_RENDERER}:
        errors.append(
            f"{label}: generationTool is {renderer!r}, expected source-sheet importer {RENDERER!r}, "
            f"per-page renderer {LOCAL_RENDERER!r}, or single-scene renderer {SINGLE_SCENE_RENDERER!r}"
        )
    if renderer == RENDERER:
        if entry.get("generationModel") != MODEL:
            errors.append(f"{label}: generationModel is {entry.get('generationModel')!r}, expected {MODEL!r}")
        if entry.get("generationStatus") not in GENERATION_STATUSES:
            errors.append(
                f"{label}: generationStatus is {entry.get('generationStatus')!r}, "
                f"expected one of {sorted(GENERATION_STATUSES)!r}"
            )
        if entry.get("sourceSheet") != expected_sheet:
            errors.append(f"{label}: sourceSheet is {entry.get('sourceSheet')!r}, expected {expected_sheet!r}")
        if not isinstance(panel_index, int) or panel_index not in expected_panels:
            errors.append(f"{label}: panelIndex is {panel_index!r}, expected one of {sorted(expected_panels)}")
    if renderer == LOCAL_RENDERER:
        if entry.get("generationModel") != LOCAL_MODEL:
            errors.append(f"{label}: generationModel is {entry.get('generationModel')!r}, expected {LOCAL_MODEL!r}")
        if entry.get("generationStatus") != LOCAL_GENERATION_STATUS:
            errors.append(f"{label}: generationStatus is {entry.get('generationStatus')!r}, expected {LOCAL_GENERATION_STATUS!r}")
    if renderer == SINGLE_SCENE_RENDERER:
        if entry.get("generationModel") != SINGLE_SCENE_MODEL:
            errors.append(f"{label}: generationModel is {entry.get('generationModel')!r}, expected {SINGLE_SCENE_MODEL!r}")
        if entry.get("generationStatus") != SINGLE_SCENE_GENERATION_STATUS:
            errors.append(f"{label}: generationStatus is {entry.get('generationStatus')!r}, expected {SINGLE_SCENE_GENERATION_STATUS!r}")
        if entry.get("sourceSheet") is not None:
            errors.append(f"{label}: single-scene art must not claim a sourceSheet")
        if entry.get("panelIndex") is not None:
            errors.append(f"{label}: single-scene art must not claim a panelIndex")
    if entry.get("status") != "generated_reviewed":
        errors.append(f"{label}: status is {entry.get('status')!r}, expected 'generated_reviewed'")
    if entry.get("visualSpecificity") != "story_specific_illustration":
        errors.append(f"{label}: visualSpecificity is not story_specific_illustration")
    if entry.get("placeholderLike") is not False:
        errors.append(f"{label}: placeholderLike must be false")
    if entry.get("storySpecificArt") is not True:
        errors.append(f"{label}: storySpecificArt must be true")
    if entry.get("productionApprovalStatus") != "not_approved":
        errors.append(f"{label}: productionApprovalStatus must remain not_approved until final art approval exists")
    if dimensions != {"width": EXPECTED_WIDTH, "height": EXPECTED_HEIGHT}:
        errors.append(f"{label}: dimensions are {dimensions!r}, expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    if not rel_exists(output):
        errors.append(f"{label}: output file missing: {output!r}")
        return errors

    assert output_path is not None
    if output_path.stat().st_size < MIN_PANEL_BYTES:
        errors.append(f"{label}: output is too small to be a high-detail runtime panel ({output_path.stat().st_size} bytes)")
    try:
        width, height = png_dimensions(output_path)
    except ValueError as exc:
        errors.append(f"{label}: {exc}")
    else:
        if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            errors.append(f"{label}: PNG dimensions are {width}x{height}, expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    return errors


def main() -> int:
    catalog = load(CATALOG)
    manifest = load(IMAGE_MANIFEST)
    scene_entries = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in manifest.get("sceneEntries", [])}
    cover_entries = {entry.get("storyId"): entry for entry in manifest.get("coverEntries", [])}
    errors: list[str] = []
    rows: list[str] = []
    total_scenes = 0
    total_covers = 0

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
        sheet_path = CONTENT / sheet
        if not sheet_path.exists():
            errors.append(f"{slug}: missing source story sheet {sheet}")
            continue
        try:
            sheet_width, sheet_height = png_dimensions(sheet_path)
        except ValueError as exc:
            errors.append(f"{slug}: {exc}")
            sheet_width = 0
            sheet_height = 0
        if sheet_width < MIN_SHEET_WIDTH or sheet_height < MIN_SHEET_HEIGHT:
            errors.append(f"{slug}: source story sheet is too small ({sheet_width}x{sheet_height})")

        cover = cover_entries.get(book_id)
        if cover is None:
            errors.append(f"{slug}: missing premium cover manifest entry")
        else:
            errors.extend(image_ok(cover, expected_sheet=sheet, expected_panels={1}, label=f"{slug} cover"))
            total_covers += 1

        page_count = 0
        for page in book.get("pages", []):
            page_id = page.get("id")
            page_number = page.get("pageNumber")
            label = f"{slug} page {page_number}"
            entry = scene_entries.get((book_id, page_id))
            if entry is None:
                errors.append(f"{label}: missing premium scene manifest entry")
                continue
            expected_panel = expected_panel_for_page(slug, int(page_number)) if isinstance(page_number, int) else None
            expected_panels = {expected_panel} if isinstance(expected_panel, int) else set(range(1, 7))
            exception_output = SINGLE_SCENE_EXCEPTIONS.get((slug, int(page_number))) if isinstance(page_number, int) else None
            if exception_output:
                if entry.get("generationTool") != SINGLE_SCENE_RENDERER:
                    errors.append(f"{label}: expected {SINGLE_SCENE_RENDERER!r} for sensitive single-scene exception")
                if entry.get("outputFile") != exception_output:
                    errors.append(f"{label}: outputFile is {entry.get('outputFile')!r}, expected {exception_output!r}")
            errors.extend(image_ok(entry, expected_sheet=sheet, expected_panels=expected_panels, label=label))
            page_count += 1
            total_scenes += 1

        rows.append(f"| {slug} | {page_count} | {sheet} |")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join(
            [
                "# Premium Imagegen Sheet Validation Report",
                "",
                f"- Premium covers checked: {total_covers}",
                f"- Premium scenes checked: {total_scenes}",
                f"- Source sheet renderer checked: `{RENDERER}`",
                f"- Selected runtime renderer accepted: per-page `{LOCAL_RENDERER}`, selected `{SINGLE_SCENE_RENDERER}` exceptions, or explicit `{RENDERER}` sheet variants when another validator confirms page-level fit",
                f"- Minimum selected panel size: {MIN_PANEL_BYTES} bytes",
                "",
                "| Story | Scenes checked | Source sheet |",
                "| --- | ---: | --- |",
                *rows,
                "",
                "## Result",
                "",
                "PASS" if not errors else "FAIL",
                "",
                *[f"- {error}" for error in errors],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    if errors:
        print(f"Premium imagegen sheet validation failed; see {REPORT.relative_to(ROOT)}")
        for error in errors[:40]:
            print(f"- {error}")
        if len(errors) > 40:
            print(f"... {len(errors) - 40} more")
        return 1

    print(f"Premium imagegen sheet validation passed: {total_scenes} scenes and {total_covers} covers.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
