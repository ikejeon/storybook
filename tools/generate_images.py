#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from asset_pipeline_common import (
    ASSETS,
    CONTENT,
    IMAGE_STATUSES,
    REVIEW_FIELDS,
    complete_books,
    content_path,
    existing_or_none,
    load_character_index,
    load_json,
    page_asset_name,
    utc_now,
    write_json,
)
from providers.registry import get_image_provider

IMAGE_MANIFEST = ASSETS / "manifests" / "image_manifest.json"
PROMPT_EXPORT = Path("tools/output/image_prompts.md")
STYLE_BIBLE = "style/moonjar_style_bible.json"


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


def image_priority(status: str) -> int:
    order = ["commissioned_final", "commissioned_reviewed", "generated_reviewed", "commissioned_draft", "generated_draft", "placeholder"]
    return order.index(status) if status in order else len(order)


def best_candidate(candidates: list[dict]) -> dict | None:
    existing = [item for item in candidates if item.get("outputFile") and (CONTENT / item["outputFile"]).exists()]
    return sorted(existing, key=lambda item: image_priority(item.get("status", "")))[0] if existing else None


def load_character_rules(character_bible: str | None) -> dict:
    if not character_bible:
        return {}
    path = CONTENT / character_bible
    if not path.exists():
        return {}
    return load_json(path)


def build_scene_prompt(book: dict, page: dict, character_bible: str | None, layer_plan: dict | None, character_rules: dict | None = None) -> str:
    style_reference = f"Global style bible: shared-content/{STYLE_BIBLE}."
    bible_reference = f"Book character bible: shared-content/{character_bible}." if character_bible else "Book character bible: use launch style defaults."
    character_rules = character_rules or {}
    style_direction = ""
    if character_rules.get("masterArtStylePrompt"):
        style_direction = f" Master art direction: {character_rules['masterArtStylePrompt']}"
    prompt_prefix = ""
    if character_rules.get("promptPrefix"):
        prompt_prefix = f" Character continuity direction: {character_rules['promptPrefix']}"
    negative_prompt = ""
    if character_rules.get("negativePrompt"):
        negative_prompt = f" Negative prompt: {character_rules['negativePrompt']}"
    anchor_note = ""
    anchor_plan = character_rules.get("anchorApprovalPlan") if isinstance(character_rules, dict) else None
    if isinstance(anchor_plan, dict) and page.get("pageNumber") in set(anchor_plan.get("anchorPages", [])):
        anchor_note = " Anchor approval page: generate this design for review before bulk-regenerating the full Sun and Moon book."
    layer_reference = ""
    if layer_plan:
        planned = ", ".join(f"{layer.get('role')}={layer.get('description')}" for layer in layer_plan.get("plannedLayers", []))
        layer_reference = f" Animation/layer plan: {layer_plan.get('animationType')} with {planned}."
    return (
        f"{style_reference} {bible_reference}{style_direction}{prompt_prefix}{anchor_note} Exact scene: {page['imagePrompt']}.{layer_reference} "
        "Requirements: premium Korean watercolor, gouache, soft ink, hanji texture, consistent characters and outfits, "
        "child-safe ages 3-8, no frightening anatomy, no graphic danger, no text or letters in the image."
        f"{negative_prompt}"
    )


def load_layer_lookup() -> dict[tuple[str, str], dict]:
    path = CONTENT / "animation" / "layer_manifest.json"
    if not path.exists():
        return {}
    manifest = load_json(path)
    return {
        (entry.get("storyId"), entry.get("sceneId")): entry
        for entry in manifest.get("scenes", [])
        if isinstance(entry, dict)
    }


def make_candidate(output_file: str, status: str, provider_result, *, prompt: str, source_file: str | None = None) -> dict:
    candidate = {
        "outputFile": output_file,
        "status": status,
        "provider": provider_result.provider if provider_result else "not_run",
        "model": provider_result.model if provider_result else None,
        "generationStatus": provider_result.generation_status if provider_result else "not_run",
        "prompt": prompt,
        "seed": provider_result.seed if provider_result else None,
        "timestamp": utc_now(),
        "sourceFile": source_file,
    }
    candidate.update(review_defaults())
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or stage offline scene/cover images for Moon Jar Stories.")
    parser.add_argument("--provider", default="placeholder", choices=["placeholder", "external_api"])
    parser.add_argument("--status", default="placeholder", choices=sorted(IMAGE_STATUSES))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.provider == "placeholder" and args.status != "placeholder":
        raise SystemExit("Refusing to mark placeholder image copies as generated/reviewed/final.")

    generated_at = utc_now()
    character_index = load_character_index()
    layer_lookup = load_layer_lookup()
    scene_entries: list[dict] = []
    cover_entries: list[dict] = []
    generation_gates: list[dict] = []

    for _catalog_entry, _book_path, book in complete_books():
        bible = character_index.get(book["id"], book.get("characterBible"))
        character_rules = load_character_rules(bible)
        if character_rules.get("anchorApprovalPlan"):
            generation_gates.append(
                {
                    "storyId": book["id"],
                    "storySlug": book["slug"],
                    "characterBible": bible,
                    "planRef": "assets/manifests/sun_moon_tiger_anchor_plan.json" if book["id"] == "book.sun_moon" else None,
                    "plan": character_rules["anchorApprovalPlan"],
                }
            )
        cover_output = f"assets/placeholders/images/covers/{book['slug']}.png"
        cover_prompt = (
            f"Global style bible: shared-content/{STYLE_BIBLE}. Book character bible: shared-content/{bible}. "
            f"{character_rules.get('masterArtStylePrompt', '')} "
            f"Premium Korean picture-book cover for {book['title']['ko']} / {book['title']['en']}. No text in image."
        )
        cover_candidates: list[dict] = []
        cover_source = existing_or_none(book.get("coverAsset"))
        provider_result = None
        if not args.dry_run and args.provider == "placeholder" and cover_source:
            provider = get_image_provider("placeholder", source_file=cover_source)
            provider_result = provider.generate_image(cover_prompt, content_path(cover_output))
        cover_candidates.append(make_candidate(cover_output, "placeholder", provider_result, prompt=cover_prompt, source_file=book.get("coverAsset")))
        cover_best = best_candidate(cover_candidates)
        cover_entries.append(
            {
                "assetType": "cover",
                "storyId": book["id"],
                "storySlug": book["slug"],
                "prompt": cover_prompt,
                "characterBible": bible,
                "outputFile": cover_best["outputFile"] if cover_best else cover_output,
                "status": cover_best["status"] if cover_best else "placeholder",
                "generationTool": cover_best["provider"] if cover_best else args.provider,
                "generationModel": cover_best["model"] if cover_best else None,
                "timestamp": generated_at,
                "seed": None,
                "generationStatus": cover_best["generationStatus"] if cover_best else "not_run",
                "candidates": cover_candidates,
            }
        )

        for page in book["pages"]:
            output = f"assets/placeholders/images/scenes/{book['slug']}/{page_asset_name(page['pageNumber'], 'png')}"
            layer_plan = layer_lookup.get((book["id"], page["id"]))
            prompt = build_scene_prompt(book, page, bible, layer_plan, character_rules)
            source = existing_or_none(page.get("imageAsset"))
            provider_result = None
            if not args.dry_run and args.provider == "placeholder" and source:
                provider = get_image_provider("placeholder", source_file=source)
                provider_result = provider.generate_image(prompt, content_path(output))
            candidates = [make_candidate(output, "placeholder", provider_result, prompt=prompt, source_file=page.get("imageAsset"))]
            best = best_candidate(candidates)
            scene_entries.append(
                {
                    "assetType": "scene",
                    "storyId": book["id"],
                    "storySlug": book["slug"],
                    "sceneId": page["id"],
                    "pageNumber": page["pageNumber"],
                    "prompt": prompt,
                    "rawPrompt": page["imagePrompt"],
                    "characterBible": bible,
                    "styleBible": STYLE_BIBLE,
                    "layerPlanRef": "animation/layer_manifest.json",
                    "outputFile": best["outputFile"] if best else output,
                    "status": best["status"] if best else "placeholder",
                    "generationTool": best["provider"] if best else args.provider,
                    "generationModel": best["model"] if best else None,
                    "timestamp": generated_at,
                    "seed": None,
                    "generationStatus": best["generationStatus"] if best else "not_run",
                    "candidates": candidates,
                }
            )

    icon_entries: list[dict] = []
    for concept in range(1, 4):
        output = f"assets/placeholders/images/app-icon/app-icon-concept-{concept:02d}.png"
        source = existing_or_none("assets/images/app-icon/app-icon-concept-01.png") or existing_or_none("assets/ui/app-icon.png")
        prompt = (
            f"Global style bible: shared-content/{STYLE_BIBLE}. Premium app icon concept for Moon Jar Stories: "
            "moon jar silhouette, Korean bedtime story mood, deep indigo, ivory, jade, persimmon. No text."
        )
        provider_result = None
        if not args.dry_run and source:
            provider = get_image_provider("placeholder", source_file=source)
            provider_result = provider.generate_image(prompt, content_path(output))
        candidates = [make_candidate(output, "placeholder", provider_result, prompt=prompt, source_file=str(source.relative_to(CONTENT)) if source else None)]
        best = best_candidate(candidates)
        icon_entries.append(
            {
                "assetType": "app_icon_concept",
                "conceptNumber": concept,
                "prompt": prompt,
                "outputFile": best["outputFile"] if best else output,
                "status": "placeholder",
                "generationTool": best["provider"] if best else "placeholder",
                "generationModel": best["model"] if best else None,
                "timestamp": generated_at,
                "seed": None,
                "generationStatus": best["generationStatus"] if best else "not_run",
                "candidates": candidates,
            }
        )

    manifest = {
        "schemaVersion": "1.1.0",
        "generatedAt": generated_at,
        "promptSource": str(PROMPT_EXPORT),
        "provider": args.provider,
        "assetPriority": ["final", "reviewed", "generated_draft", "placeholder"],
        "statusVocabulary": sorted(IMAGE_STATUSES),
        "reviewFields": REVIEW_FIELDS,
        "generationGates": generation_gates,
        "notes": [
            "No image generation runs inside the child app.",
            "Apps resolve outputFile from this manifest; story JSON can stay stable as assets improve.",
            "Current placeholder provider only stages local demo art into separated placeholder folders.",
        ],
        "sceneEntries": scene_entries,
        "coverEntries": cover_entries,
        "appIconConcepts": icon_entries,
    }
    if not args.dry_run:
        write_json(IMAGE_MANIFEST, manifest)

    print(f"Image manifest ready: {IMAGE_MANIFEST.relative_to(CONTENT.parent)} ({len(scene_entries)} scenes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
