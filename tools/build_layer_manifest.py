#!/usr/bin/env python3
from __future__ import annotations

from asset_pipeline_common import CONTENT, complete_books, load_character_index, utc_now, write_json

LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
LAYER_ROLES = ["background", "midground", "character", "foreground", "effect", "particle_glow"]


def layer_plan(book: dict, page: dict) -> list[dict]:
    slug = book["slug"]
    scene_id = page["id"]
    animation_layers = page.get("animation", {}).get("layers", [])
    animation_summary = ", ".join(
        f"{layer.get('name')}: {layer.get('motion')}" for layer in animation_layers if layer.get("name")
    )
    return [
        {
            "role": "background",
            "description": "Static environment, sky, horizon, architecture, mountain or room base.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/background.png",
            "motion": "none or very slow parallax",
            "requiredLater": True,
        },
        {
            "role": "midground",
            "description": "Trees, furniture, pond, cottage, road, or large story props behind characters.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/midground.png",
            "motion": "subtle drift/sway where useful",
            "requiredLater": True,
        },
        {
            "role": "character",
            "description": "Main recurring characters from the character bible, isolated for breathing/blink/small pose motion.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/character.png",
            "motion": "subtle breathing, blink, small gesture",
            "requiredLater": True,
        },
        {
            "role": "foreground",
            "description": "Foreground branches, grass, table edge, doorway, or framing objects.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/foreground.png",
            "motion": "tiny sway or none",
            "requiredLater": False,
        },
        {
            "role": "effect",
            "description": f"Scene-specific animation cues from current metadata: {animation_summary or 'none'}.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/effect.png",
            "motion": page.get("animation", {}).get("type", "subtleLoop"),
            "requiredLater": False,
        },
        {
            "role": "particle_glow",
            "description": "Optional glow, steam, scent curl, sparkle, firefly, snow, star, or dust layer.",
            "futureOutputFile": f"assets/images/layers/{slug}/{scene_id}/particle-glow.png",
            "motion": "opacity pulse or slow particle drift",
            "requiredLater": False,
        },
    ]


def main() -> int:
    character_index = load_character_index()
    generated_at = utc_now()
    scenes: list[dict] = []
    animation_types: set[str] = set()

    for _entry, _book_path, book in complete_books():
        bible = character_index.get(book["id"])
        for page in book["pages"]:
            animation_type = page["animation"]["type"]
            animation_types.add(animation_type)
            scenes.append(
                {
                    "storyId": book["id"],
                    "storySlug": book["slug"],
                    "sceneId": page["id"],
                    "pageNumber": page["pageNumber"],
                    "animationType": animation_type,
                    "characterBible": bible,
                    "currentMode": "single_full_scene_image",
                    "currentImageAsset": page.get("imageAsset"),
                    "layerPlanStatus": "planned_from_single_scene",
                    "sourceAnimationLayers": page["animation"].get("layers", []),
                    "plannedLayers": layer_plan(book, page),
                }
            )

    manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": generated_at,
        "description": "Layered animation production plan. The current app still loads a single full-scene image; these entries define how each scene should be split for later native layer animation.",
        "layerRoles": LAYER_ROLES,
        "validAnimationTypes": sorted(animation_types),
        "scenes": scenes,
    }
    write_json(LAYER_MANIFEST, manifest)
    print(f"Layer manifest written: {LAYER_MANIFEST.relative_to(CONTENT.parent)} ({len(scenes)} scenes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
