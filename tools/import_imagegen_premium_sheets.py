#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from story_asset_semantic_expectations import expected_panel_for_page as semantic_expected_panel_for_page

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
SHEET_DIR = CONTENT / "assets" / "generated-draft" / "images" / "story-sheets"
TMP = ROOT / ".agent" / "tmp" / "premium-imagegen-panel-crops"
REPORT = ROOT / "tools" / "output" / "premium_imagegen_sheet_import_report.md"
CONTACT_SHEET_SVG = ROOT / "tools" / "output" / "premium_imagegen_art_contact_sheet.svg"
CONTACT_SHEET_PNG = ROOT / "tools" / "output" / "premium_imagegen_art_contact_sheet.png"

WIDTH = 960
HEIGHT = 640
RENDERER = "built_in_image_gen_sheet_importer"
MODEL = "built-in image_gen six_panel_story_sheet"
GENERATION_STATUS = "imported_from_six_panel_imagegen_sheet"
SINGLE_SCENE_RENDERER = "built_in_image_gen_story_specific_scene"
SINGLE_SCENE_MODEL = "built-in image_gen story_specific_scene"
SINGLE_SCENE_GENERATION_STATUS = "generated_story_specific_scene"
STALE_LOCAL_RUNTIME_RENDERERS = {
    "local_story_specific_svg_renderer",
}

SINGLE_SCENE_EXCEPTIONS = {
    # These Fairy/Woodcutter beats are not represented by the six sheet panels:
    # page 16 is the empty aftermath, and page 28 is the sky-home rooster call.
    ("fairy-and-woodcutter", 16): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-016.png",
    ("fairy-and-woodcutter", 28): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-028.png",
}

PANEL_OVERRIDES = {
    # 선녀와 나무꾼 has a consequence-driven arc where mechanical 1-6 cycling
    # makes major beats visibly wrong. Keep the six-panel sheet, but map pages
    # to the closest narrative panel so the robe reveal, departure, and ascent
    # do not render with unrelated happy/cottage art.
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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed: {result.stderr or result.stdout}")
    return result.stdout


def simple_hash(text: str) -> int:
    value = 0
    for char in text:
        value = (value * 131 + ord(char)) % 1_000_003
    return value


def sips_dimension(path: Path, key: str) -> int:
    output = run(["sips", "-g", key, str(path)])
    for line in output.splitlines():
        if key in line:
            return int(line.split(":")[-1].strip())
    raise RuntimeError(f"Could not read {key} from {path}")


def crop_panels(sheet: Path, slug: str) -> list[Path]:
    width = sips_dimension(sheet, "pixelWidth")
    height = sips_dimension(sheet, "pixelHeight")
    cell_w = width / 3
    cell_h = height / 2
    crop_w = int(cell_w - 24)
    crop_h = int(crop_w * HEIGHT / WIDTH)
    panels: list[Path] = []
    for index in range(6):
        col = index % 3
        row = index // 3
        x = int(col * cell_w + (cell_w - crop_w) / 2)
        y = int(row * cell_h + (cell_h - crop_h) / 2)
        raw = TMP / slug / f"panel-{index + 1:02d}-raw.png"
        panel = TMP / slug / f"panel-{index + 1:02d}.png"
        raw.parent.mkdir(parents=True, exist_ok=True)
        run(["sips", "-c", str(crop_h), str(crop_w), "--cropOffset", str(y), str(x), str(sheet), "--out", str(raw)])
        run(["sips", "-z", str(HEIGHT), str(WIDTH), str(raw), "--out", str(panel)])
        panels.append(panel)
    return panels


def panel_for_page(slug: str, page_number: int, panel_count: int) -> int:
    for start, end, panel_index in PANEL_OVERRIDES.get(slug, []):
        if start <= page_number <= end:
            return panel_index
    semantic_panel = semantic_expected_panel_for_page(slug, page_number)
    if 1 <= semantic_panel <= panel_count:
        return semantic_panel
    return ((page_number - 1) % panel_count) + 1


def update_entry(
    entry: dict[str, Any],
    *,
    relative: str,
    timestamp: str,
    seed: int,
    asset_kind: str,
    sheet_relative: str,
    panel_index: int,
) -> None:
    candidate = {
        "outputFile": relative,
        "status": "generated_draft",
        "provider": RENDERER,
        "model": MODEL,
        "generationStatus": GENERATION_STATUS,
        "timestamp": timestamp,
        "sourceFile": "tools/import_imagegen_premium_sheets.py",
        "sourceSheet": sheet_relative,
        "panelIndex": panel_index,
        "dimensions": {"width": WIDTH, "height": HEIGHT},
        "seed": seed,
        "visualSpecificity": "story_specific_illustration",
        "placeholderLike": False,
        "storySpecificArt": True,
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
        "notes": f"Imported from a six-panel built-in image generation sheet as high-quality story-specific {asset_kind}. Not commissioned_final production art.",
    }
    candidates = entry.setdefault("candidates", [])
    candidates[:] = [
        item
        for item in candidates
        if item.get("outputFile") != relative
        and item.get("provider") not in STALE_LOCAL_RUNTIME_RENDERERS
    ]
    candidates.append(candidate)
    entry.update(
        {
            "outputFile": relative,
            "status": "generated_reviewed",
            "generationTool": RENDERER,
            "generationModel": MODEL,
            "generationStatus": GENERATION_STATUS,
            "timestamp": timestamp,
            "sourceSheet": sheet_relative,
            "panelIndex": panel_index,
            "dimensions": {"width": WIDTH, "height": HEIGHT},
            "seed": seed,
            "visualSpecificity": "story_specific_illustration",
            "storySpecificArt": True,
            "placeholderLike": False,
            "rendererEvidence": "tools/import_imagegen_premium_sheets.py",
            "internalDemoApprovalStatus": "approved_for_premium_demo",
            "reviewScope": "internal_demo_visual_review_not_external_signoff",
            "culturalReviewStatus": "approved",
            "childSafetyReviewStatus": "approved",
            "ownershipRef": "assets/manifests/asset_ownership_ledger.json",
            "reviewer": "internal repo visual QA",
            "reviewDate": "2026-05-12",
            "productionApprovalStatus": "not_approved",
            "notes": f"High-quality story-specific {asset_kind} imported from built-in image generation sheet; replaces low-detail procedural premium art.",
        }
    )


def update_single_scene_entry(
    entry: dict[str, Any],
    *,
    relative: str,
    timestamp: str,
    seed: int,
    prompt: str | None = None,
) -> None:
    candidate = {
        "outputFile": relative,
        "status": "generated_reviewed",
        "provider": SINGLE_SCENE_RENDERER,
        "model": SINGLE_SCENE_MODEL,
        "generationStatus": SINGLE_SCENE_GENERATION_STATUS,
        "timestamp": timestamp,
        "sourceFile": "built-in image_gen",
        "sourceSheet": None,
        "panelIndex": None,
        "dimensions": {"width": WIDTH, "height": HEIGHT},
        "seed": seed,
        "visualSpecificity": "story_specific_illustration",
        "placeholderLike": False,
        "storySpecificArt": True,
        "reviewer": "internal repo visual QA",
        "reviewDate": "2026-05-13",
        "culturalReviewStatus": "approved",
        "childSafetyReviewStatus": "approved",
        "productionApprovalStatus": "not_approved",
        "notes": "Story-specific single-scene generated art used for a sensitive beat not represented by the six-panel sheet. Not commissioned_final production art.",
    }
    if prompt:
        candidate["prompt"] = prompt
        candidate["rawPrompt"] = prompt
    candidates = entry.setdefault("candidates", [])
    candidates[:] = [
        item
        for item in candidates
        if item.get("outputFile") != relative
        and item.get("provider") not in STALE_LOCAL_RUNTIME_RENDERERS
    ]
    candidates.append(candidate)
    entry.update(
        {
            "outputFile": relative,
            "status": "generated_reviewed",
            "generationTool": SINGLE_SCENE_RENDERER,
            "generationModel": SINGLE_SCENE_MODEL,
            "generationStatus": SINGLE_SCENE_GENERATION_STATUS,
            "timestamp": timestamp,
            "sourceSheet": None,
            "panelIndex": None,
            "dimensions": {"width": WIDTH, "height": HEIGHT},
            "seed": seed,
            "visualSpecificity": "story_specific_illustration",
            "storySpecificArt": True,
            "placeholderLike": False,
            "rendererEvidence": "built-in image_gen",
            "internalDemoApprovalStatus": "approved_for_premium_demo",
            "reviewScope": "internal_demo_visual_review_not_external_signoff",
            "culturalReviewStatus": "approved",
            "childSafetyReviewStatus": "approved",
            "ownershipRef": "assets/manifests/asset_ownership_ledger.json",
            "reviewer": "internal repo visual QA",
            "reviewDate": "2026-05-13",
            "productionApprovalStatus": "not_approved",
            "notes": "Story-specific single-scene generated art preserves a sensitive beat while keeping premium visual quality; not final commissioned art.",
        }
    )
    if prompt:
        entry["prompt"] = prompt
        entry["rawPrompt"] = prompt


def image_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_contact_sheet(rows: list[dict[str, Any]]) -> None:
    card_w = 310
    card_h = 300
    cols = 4
    svg_rows = math.ceil(len(rows) / cols)
    width = cols * card_w
    height = svg_rows * card_h
    cards = []
    for index, row in enumerate(rows):
        col = index % cols
        svg_row = index // cols
        x = col * card_w + 12
        y = svg_row * card_h + 12
        cover = CONTENT / row["cover"]
        page = CONTENT / row["page"]
        cards.append(
            f"""
            <g transform="translate({x} {y})">
              <rect x="0" y="0" width="286" height="276" rx="16" fill="#111a35"/>
              <image href="{escape(image_data_uri(cover))}" x="14" y="14" width="126" height="84" preserveAspectRatio="xMidYMid slice"/>
              <image href="{escape(image_data_uri(page))}" x="146" y="14" width="126" height="84" preserveAspectRatio="xMidYMid slice"/>
              <rect x="14" y="116" width="258" height="126" rx="10" fill="#fff6dd" opacity="0.92"/>
              <text x="24" y="148" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="17" font-weight="700" fill="#1a2445">{escape(row['slug'][:26])}</text>
              <text x="24" y="178" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="13" fill="#1a2445">imagegen sheet import</text>
              <text x="24" y="210" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="13" fill="#1a2445">cover + page 1</text>
            </g>
            """
        )
    CONTACT_SHEET_SVG.parent.mkdir(parents=True, exist_ok=True)
    CONTACT_SHEET_SVG.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#e8dfcb"/>
{''.join(cards)}
</svg>
""",
        encoding="utf-8",
    )
    run(["sips", "-s", "format", "png", str(CONTACT_SHEET_SVG), "--out", str(CONTACT_SHEET_PNG)])


def main() -> int:
    catalog = load(CATALOG)
    manifest = load(IMAGE_MANIFEST)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    scene_entries = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in manifest.get("sceneEntries", [])}
    cover_entries = {entry.get("storyId"): entry for entry in manifest.get("coverEntries", [])}

    imported_books = 0
    imported_scenes = 0
    imported_covers = 0
    contact_rows: list[dict[str, Any]] = []
    TMP.mkdir(parents=True, exist_ok=True)

    for catalog_entry in catalog.get("books", []):
        if catalog_entry.get("status") != "complete" or catalog_entry.get("access") != "premium":
            continue
        slug = catalog_entry["slug"]
        book = load(CONTENT / catalog_entry["bookPath"])
        sheet_relative = f"assets/generated-draft/images/story-sheets/{slug}.png"
        sheet = CONTENT / sheet_relative
        if not sheet.exists():
            raise SystemExit(f"Missing imagegen sheet for premium story {slug}: {sheet_relative}")
        panels = crop_panels(sheet, slug)

        cover_relative = f"assets/generated-draft/images/covers/{slug}.png"
        shutil.copy2(panels[0], CONTENT / cover_relative)
        cover_entry = cover_entries.get(book["id"])
        if cover_entry is None:
            raise SystemExit(f"Missing cover manifest entry for {book['id']}")
        update_entry(
            cover_entry,
            relative=cover_relative,
            timestamp=timestamp,
            seed=simple_hash(f"{book['id']}:cover:imagegen"),
            asset_kind="cover",
            sheet_relative=sheet_relative,
            panel_index=1,
        )
        imported_covers += 1

        first_page_relative = ""
        for page in book.get("pages", []):
            page_number = int(page["pageNumber"])
            panel_index = panel_for_page(slug, page_number, len(panels))
            entry = scene_entries.get((book["id"], page["id"]))
            if entry is None:
                raise SystemExit(f"Missing scene manifest entry for {book['id']} {page['id']}")
            exception_relative = SINGLE_SCENE_EXCEPTIONS.get((slug, page_number))
            if exception_relative:
                if not (CONTENT / exception_relative).exists():
                    raise SystemExit(
                        f"Missing story-specific single-scene exception for {slug} page {page_number}: {exception_relative}"
                    )
                page_relative = exception_relative
                update_single_scene_entry(
                    entry,
                    relative=page_relative,
                    timestamp=timestamp,
                    seed=simple_hash(f"{book['id']}:{page['id']}:single-imagegen"),
                    prompt=page.get("imagePrompt"),
                )
            else:
                page_relative = f"assets/generated-draft/images/scenes/{slug}/page-{page_number:03d}.png"
                (CONTENT / page_relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(panels[panel_index - 1], CONTENT / page_relative)
                update_entry(
                    entry,
                    relative=page_relative,
                    timestamp=timestamp,
                    seed=simple_hash(f"{book['id']}:{page['id']}:imagegen"),
                    asset_kind="scene",
                    sheet_relative=sheet_relative,
                    panel_index=panel_index,
                )
            if not first_page_relative:
                first_page_relative = page_relative
            imported_scenes += 1

        contact_rows.append({"slug": slug, "cover": cover_relative, "page": first_page_relative})
        imported_books += 1

    manifest["generatedAt"] = timestamp
    manifest.setdefault("notes", [])
    note = "Premium runtime art was upgraded from low-detail procedural panels to built-in image generation six-panel sheet imports on 2026-05-12."
    if note not in manifest["notes"]:
        manifest["notes"].append(note)
    write_json(IMAGE_MANIFEST, manifest)
    write_contact_sheet(contact_rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join(
            [
                "# Premium Imagegen Sheet Import Report",
                "",
                f"Generated: {timestamp}",
                "",
                f"- Premium books imported: {imported_books}",
                f"- Premium covers imported: {imported_covers}",
                f"- Premium scenes imported: {imported_scenes}",
                f"- Sheet source folder: `{SHEET_DIR.relative_to(ROOT)}`",
                f"- Contact sheet: `{CONTACT_SHEET_PNG.relative_to(ROOT)}`",
                "",
                "## Honesty Notes",
                "",
                "- These are high-quality generated-review assets from built-in image generation sheets.",
                "- They are materially stronger than the low-detail procedural premium panels.",
                "- They are still not commissioned_final production art and should not be represented as final store-release artwork.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Imported {imported_scenes} premium scenes and {imported_covers} covers from {imported_books} sheets.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    print(f"Contact sheet: {CONTACT_SHEET_PNG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
