#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from asset_pipeline_common import (
    ASSETS,
    CONTENT,
    IMAGE_STATUSES,
    complete_books,
    content_path,
    existing_or_none,
    load_character_index,
    page_asset_name,
    utc_now,
    write_json,
)

IMAGE_MANIFEST = ASSETS / "manifests" / "image_manifest.json"
SCENE_DIR = ASSETS / "images" / "scenes"
COVER_DIR = ASSETS / "images" / "covers"
APP_ICON_DIR = ASSETS / "images" / "app-icon"
PROMPT_EXPORT = Path("tools/output/image_prompts.md")


def copy_placeholder(src_relative: str | None, dst_relative: str) -> bool:
    src = existing_or_none(src_relative)
    if not src:
        return False
    dst = content_path(dst_relative)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return True
    shutil.copy2(src, dst)
    return True


def build_scene_prompt(book: dict, page: dict, character_bible: str | None, character_rules: dict | None = None) -> str:
    prefix = ""
    if character_bible:
        prefix = f"Reference character bible shared-content/{character_bible}. "
    character_rules = character_rules or {}
    style_direction = f"{character_rules.get('masterArtStylePrompt', '')} " if character_rules.get("masterArtStylePrompt") else ""
    prompt_prefix = f"{character_rules.get('promptPrefix', '')} " if character_rules.get("promptPrefix") else ""
    negative_prompt = f" Negative prompt: {character_rules.get('negativePrompt')}" if character_rules.get("negativePrompt") else ""
    anchor_note = ""
    anchor_plan = character_rules.get("anchorApprovalPlan") if isinstance(character_rules, dict) else None
    if isinstance(anchor_plan, dict) and page.get("pageNumber") in set(anchor_plan.get("anchorPages", [])):
        anchor_note = "Anchor approval page: generate and approve this image before bulk-regenerating the full Sun and Moon book. "
    return (
        f"{prefix}{style_direction}{prompt_prefix}{anchor_note}{page['imagePrompt']} "
        "Production requirements: premium Korean watercolor, gouache, and soft ink; hanji paper texture; "
        "child-safe emotional tone; no text baked into image unless specifically requested; maintain scene continuity."
        f"{negative_prompt}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare production image jobs/manifests for Moon Jar Stories.")
    parser.add_argument(
        "--stage-placeholders",
        action="store_true",
        help="Copy existing demo placeholders into the production image folder layout and update book JSON paths.",
    )
    parser.add_argument(
        "--provider",
        default="stub",
        choices=["stub", "external"],
        help="Image generation provider. 'stub' writes a manifest/job list only. 'external' marks jobs for an outside generator.",
    )
    parser.add_argument(
        "--status",
        default="placeholder",
        choices=sorted(IMAGE_STATUSES),
        help="Status to assign to staged assets. Use placeholder unless real generation has occurred.",
    )
    args = parser.parse_args()

    if args.status != "placeholder" and args.provider == "stub":
        raise SystemExit("Refusing to mark stub image jobs as non-placeholder.")

    generated_at = utc_now()
    character_index = load_character_index()
    entries: list[dict] = []
    cover_entries: list[dict] = []

    for _entry, book_path, book in complete_books():
        bible = character_index.get(book["id"])
        character_rules = load(CONTENT / bible) if bible and (CONTENT / bible).exists() else {}

        cover_output = f"assets/images/covers/{book['slug']}.png"
        cover_copied = False
        source_cover_asset = book.get("coverAsset")
        if args.stage_placeholders:
            cover_copied = copy_placeholder(source_cover_asset, cover_output)
            if cover_copied:
                book["coverAsset"] = cover_output
                book["coverAssetStatus"] = args.status
                if bible:
                    book["characterBible"] = bible

        cover_entries.append(
            {
                "assetType": "cover",
                "storyId": book["id"],
                "storySlug": book["slug"],
                "prompt": f"Create a premium Korean picture-book cover for {book['title']['ko']} / {book['title']['en']}. Reference {bible or 'the launch character bible'}.",
                "characterBible": bible,
                "outputFile": cover_output,
                "sourcePlaceholderFile": source_cover_asset,
                "generationTool": "placeholder_copy" if cover_copied else args.provider,
                "generationModel": None,
                "timestamp": generated_at,
                "seed": None,
                "status": args.status if cover_copied else "placeholder",
                "generationStatus": "staged_placeholder" if cover_copied else "not_run_tool_unavailable",
            }
        )

        for page in book["pages"]:
            output = f"assets/images/scenes/{book['slug']}/{page_asset_name(page['pageNumber'], 'png')}"
            copied = False
            source_asset = page.get("imageAsset")
            if args.stage_placeholders:
                copied = copy_placeholder(source_asset, output)
                if copied:
                    page["imageAsset"] = output
                    page["imageAssetStatus"] = args.status
                    if bible:
                        page["characterBible"] = bible

            entries.append(
                {
                    "assetType": "scene",
                    "storyId": book["id"],
                    "storySlug": book["slug"],
                    "sceneId": page["id"],
                    "pageNumber": page["pageNumber"],
                    "prompt": build_scene_prompt(book, page, bible, character_rules),
                    "rawPrompt": page["imagePrompt"],
                    "characterBible": bible,
                    "outputFile": output,
                    "sourcePlaceholderFile": source_asset,
                    "generationTool": "placeholder_copy" if copied else args.provider,
                    "generationModel": None,
                    "timestamp": generated_at,
                    "seed": None,
                    "status": args.status if copied else "placeholder",
                    "generationStatus": "staged_placeholder" if copied else "not_run_tool_unavailable",
                }
            )

        if args.stage_placeholders:
            write_json(book_path, book)

    app_icon_entries: list[dict] = []
    for concept_number in range(1, 4):
        output = f"assets/images/app-icon/app-icon-concept-{concept_number:02d}.png"
        copied = False
        if args.stage_placeholders:
            copied = copy_placeholder("assets/ui/app-icon.png", output)
        app_icon_entries.append(
            {
                "assetType": "app_icon_concept",
                "conceptNumber": concept_number,
                "prompt": (
                    "Premium app icon concept for Moon Jar Stories: moon jar silhouette, Korean bedtime story mood, "
                    "deep indigo, ivory, jade, and persimmon palette, child-safe premium library feel."
                ),
                "outputFile": output,
                "generationTool": "placeholder_copy" if copied else args.provider,
                "generationModel": None,
                "timestamp": generated_at,
                "seed": None,
                "status": "placeholder",
                "generationStatus": "staged_placeholder" if copied else "not_run_tool_unavailable",
            }
        )

    manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": generated_at,
        "promptSource": str(PROMPT_EXPORT),
        "provider": args.provider,
        "notes": [
            "No live image generation is performed inside the child app.",
            "This manifest is for offline/dev-time asset production only.",
            "Current run uses staged placeholders unless a real external generator is connected later.",
        ],
        "statusVocabulary": sorted(IMAGE_STATUSES),
        "sceneEntries": entries,
        "coverEntries": cover_entries,
        "appIconConcepts": app_icon_entries,
    }
    write_json(IMAGE_MANIFEST, manifest)

    staged_scenes = sum(1 for item in entries if item["generationStatus"] == "staged_placeholder")
    staged_covers = sum(1 for item in cover_entries if item["generationStatus"] == "staged_placeholder")
    staged_icons = sum(1 for item in app_icon_entries if item["generationStatus"] == "staged_placeholder")
    print(
        f"Image manifest written: {IMAGE_MANIFEST.relative_to(CONTENT.parent)} "
        f"({len(entries)} scenes, {len(cover_entries)} covers, {len(app_icon_entries)} app icons; "
        f"staged placeholders: {staged_scenes} scenes, {staged_covers} covers, {staged_icons} app icons)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
