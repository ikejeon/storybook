#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
BOOK_DIR = CONTENT / "books"
CHARACTER_DIR = CONTENT / "characters"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
CHARACTER_ART_MANIFEST = CONTENT / "assets" / "manifests" / "character_art_manifest.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
IOS = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "Views.swift"
IOS_LOADER = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "ContentLoader.swift"
ANDROID = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "ui" / "MoonJarApp.kt"
ANDROID_REPOSITORY = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "data" / "ContentRepository.kt"
REPORT = ROOT / "tools" / "output" / "art_experience_score_report.md"
REQUIRED_LAYER_ROLES = {"background", "midground", "character", "foreground", "effect", "particle_glow"}
BAD_IMAGE_RENDERERS = {"local_static_storyboard_renderer", "deterministic_repo_renderer", "moonjar_static_placeholder_renderer"}
PREMIUM_STORY_SPECIFIC_RENDERER = "local_story_specific_svg_renderer"
PREMIUM_STORY_SPECIFIC_RUNTIME_RENDERERS = {
    PREMIUM_STORY_SPECIFIC_RENDERER,
    "built_in_image_gen_sheet_importer",
    "built_in_image_gen_story_specific_scene",
}
MIN_PREMIUM_STORY_SPECIFIC_BYTES = 180_000


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def score_category(checks: list[tuple[str, bool, str]]) -> int:
    if not checks:
        return 0
    return round(100 * sum(1 for _, ok, _ in checks if ok) / len(checks))


def complete_books() -> list[dict[str, Any]]:
    catalog = load(CATALOG)
    return [entry for entry in catalog.get("books", []) if entry.get("status") == "complete"]


def manifest_scene_entries() -> list[dict[str, Any]]:
    return load(IMAGE_MANIFEST).get("sceneEntries", [])


def manifest_cover_entries() -> list[dict[str, Any]]:
    return load(IMAGE_MANIFEST).get("coverEntries", [])


def manifest_anchor_entries() -> list[dict[str, Any]]:
    return load(IMAGE_MANIFEST).get("approvalAnchorEntries", [])


def manifest_sun_moon_regeneration() -> dict[str, Any]:
    value = load(IMAGE_MANIFEST).get("sunMoonRegeneration", {})
    return value if isinstance(value, dict) else {}


def layer_scenes() -> list[dict[str, Any]]:
    return load(LAYER_MANIFEST).get("scenes", [])


def materialized_layer_assets_ready(layers: list[dict[str, Any]]) -> bool:
    if not layers:
        return False
    for entry in layers:
        planned = entry.get("plannedLayers", [])
        roles = {layer.get("role") for layer in planned if isinstance(layer, dict)}
        if not REQUIRED_LAYER_ROLES.issubset(roles):
            return False
        for layer in planned:
            if not isinstance(layer, dict):
                return False
            output = layer.get("outputFile")
            if layer.get("status") != "generated_reviewed":
                return False
            if not isinstance(output, str) or not output or not (CONTENT / output).exists():
                return False
    return True


def story_pages_reference_layer_assets(books: list[dict[str, Any]]) -> bool:
    for entry in books:
        book_path = entry.get("bookPath")
        if not isinstance(book_path, str):
            return False
        book = load(CONTENT / book_path)
        for page in book.get("pages", []):
            layers = page.get("animation", {}).get("layers", [])
            roles = {layer.get("name") for layer in layers if isinstance(layer, dict)}
            if not REQUIRED_LAYER_ROLES.issubset(roles):
                return False
            for layer in layers:
                output = layer.get("outputFile") if isinstance(layer, dict) else None
                if not isinstance(output, str) or not output or not (CONTENT / output).exists():
                    return False
    return True


def character_bibles() -> list[dict[str, Any]]:
    bibles: list[dict[str, Any]] = []
    for path in sorted(CHARACTER_DIR.glob("*.character_bible.json")):
        bibles.append(load(path))
    return bibles


def prompt_safe(entry: dict[str, Any]) -> bool:
    text = " ".join(str(entry.get(key, "")) for key in ("prompt", "rawPrompt")).lower()
    return all(needle in text for needle in ["no text", "no watermark"]) and any(
        phrase in text for phrase in ["fit-safe", "safe margins", "not cropped", "no cropped"]
    )


def selected_prompt_text(entry: dict[str, Any]) -> str:
    return " ".join(str(entry.get(key, "")) for key in ("prompt", "rawPrompt")).lower()


def selected_positive_prompt_text(entry: dict[str, Any]) -> str:
    parts = []
    for key in ("prompt", "rawPrompt"):
        text = str(entry.get(key, "")).lower()
        parts.append(text.split("negative prompt:", 1)[0])
    return " ".join(parts)


STALE_POSITIVE_PROMPT_TERMS = (
    "not cute",
    "not plush",
    "cute",
    "cuteness",
    "plush",
    "plush-like",
    "plush toy",
    "not a friend",
    "mascot",
    "pet tiger",
    "cute companion",
    "friendly companion",
)


def has_stale_positive_prompt_text(entry: dict[str, Any]) -> bool:
    return any(term in selected_positive_prompt_text(entry) for term in STALE_POSITIVE_PROMPT_TERMS)


def sun_moon_positive_prompt_entries(scenes: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = [entry for entry in scenes if entry.get("storyId") == "book.sun_moon"]
    for anchor in anchors:
        if anchor.get("storyId") != "book.sun_moon":
            continue
        entries.append(anchor)
        for candidate in anchor.get("candidates", []):
            if isinstance(candidate, dict) and candidate.get("outputFile") == anchor.get("outputFile"):
                entries.append(candidate)
    return entries


def has_open_art_direction_blocker(entry: dict[str, Any]) -> bool:
    return bool(entry.get("regenerationBlockedReason")) or entry.get("artDirectionStatus") == "needs_tiger_anchor_regeneration"


def selected_asset_exists(entry: dict[str, Any]) -> bool:
    output = entry.get("outputFile")
    return isinstance(output, str) and (CONTENT / output).exists()


def selected_asset_size(entry: dict[str, Any]) -> int:
    output = entry.get("outputFile")
    if isinstance(output, str) and (CONTENT / output).exists():
        return (CONTENT / output).stat().st_size
    return 0


def uses_bad_image_renderer(entry: dict[str, Any]) -> bool:
    values = [entry.get("generationTool"), entry.get("generationModel")]
    for candidate in entry.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("outputFile") == entry.get("outputFile"):
            values.extend([candidate.get("provider"), candidate.get("model")])
    return any(isinstance(value, str) and value in BAD_IMAGE_RENDERERS for value in values)


def premium_story_specific_art(entry: dict[str, Any]) -> bool:
    return (
        entry.get("generationTool") in PREMIUM_STORY_SPECIFIC_RUNTIME_RENDERERS
        and entry.get("visualSpecificity") == "story_specific_illustration"
        and entry.get("placeholderLike") is False
        and selected_asset_size(entry) >= MIN_PREMIUM_STORY_SPECIFIC_BYTES
    )


def character_sheet_entries() -> list[dict[str, Any]]:
    if not CHARACTER_ART_MANIFEST.exists():
        return []
    return load(CHARACTER_ART_MANIFEST).get("entries", [])


def character_sheet_assets_ready(complete_ids: set[str]) -> bool:
    entries = [entry for entry in character_sheet_entries() if entry.get("bookId") in complete_ids]
    if len(entries) != len(complete_ids):
        return False
    for entry in entries:
        output = entry.get("outputFile")
        if entry.get("generationTool") != PREMIUM_STORY_SPECIFIC_RENDERER:
            return False
        if entry.get("status") not in {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}:
            return False
        if not isinstance(output, str) or not (CONTENT / output).exists():
            return False
    return True


def main() -> int:
    ios = read(IOS)
    ios_loader = read(IOS_LOADER)
    android = read(ANDROID)
    android_repository = read(ANDROID_REPOSITORY)
    scenes = manifest_scene_entries()
    covers = manifest_cover_entries()
    anchors = manifest_anchor_entries()
    sun_moon_regeneration = manifest_sun_moon_regeneration()
    layers = layer_scenes()
    bibles = character_bibles()
    books = complete_books()
    complete_ids = {entry["id"] for entry in books}
    premium_ids = {entry["id"] for entry in books if entry.get("access") == "premium"}
    premium_scenes = [entry for entry in scenes if entry.get("storyId") in premium_ids]
    premium_covers = [entry for entry in covers if entry.get("storyId") in premium_ids]
    expected_scene_count = 0
    for entry in books:
        book_path = entry.get("bookPath")
        if isinstance(book_path, str):
            expected_scene_count += len(load(CONTENT / book_path).get("pages", []))

    scene_checks = [
        (
            "All complete scenes have selected runtime image entries",
            len(scenes) == expected_scene_count and all(selected_asset_exists(entry) for entry in scenes),
            "Keep image_manifest sceneEntries complete and pointing at real packaged files.",
        ),
        (
            "Runtime scene art is draft-or-better and never selected as placeholder",
            scenes and all(entry.get("status") != "placeholder" for entry in scenes),
            "The app should resolve generated/reviewed/final scene art before placeholder fallback.",
        ),
        (
            "Selected runtime art does not use the old abstract static renderer",
            scenes and covers and not any(uses_bad_image_renderer(entry) for entry in scenes + covers),
            "Replace any selected local_static_storyboard_renderer/deterministic_repo_renderer asset before scoring art quality high.",
        ),
        (
            "Premium runtime scenes and covers are story-specific generated illustrations",
            premium_scenes
            and premium_covers
            and all(premium_story_specific_art(entry) for entry in premium_scenes + premium_covers),
            "Premium catalog art must carry story-specific illustration evidence, not only generated_reviewed status.",
        ),
        (
            "All complete covers have selected runtime image entries",
            len(covers) == len(complete_ids) and all(selected_asset_exists(entry) for entry in covers),
            "Every complete catalog book needs a visible cover asset.",
        ),
        (
            "Reviewed anchor art exists for style and antagonist-tone calibration",
            sum(1 for entry in anchors if entry.get("status") in {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}) >= 7,
            "Maintain a reviewed anchor set before claiming all-catalog art direction.",
        ),
        (
            "Selected runtime scene art has no unresolved regeneration blocker",
            scenes and not any(has_open_art_direction_blocker(entry) for entry in scenes),
            "Regenerate or import any scene art marked as blocked or predating approved art direction before scoring art quality at 95+.",
        ),
        (
            "Sun and Moon tiger-anchor regeneration/import is complete for generated-draft review",
            sun_moon_regeneration.get("status") == "generated_draft_regeneration_complete_pending_review"
            and sun_moon_regeneration.get("completedSceneCount") == 32,
            "Import or generate all 32 Sun and Moon scene drafts from the approved anchor before clearing the blocker.",
        ),
        (
            "Scene prompts preserve no-text, no-watermark, and fit-safe art direction",
            scenes and all(prompt_safe(entry) for entry in scenes),
            "Prompts must keep image generation safe for storybook layout and app screenshots.",
        ),
        (
            "iOS applies premium layered art treatment over scene images",
            has_all(ios, ["LayeredSceneTreatment", "ParchmentTexture", "LivingSceneEffects", "contentMode: .fit"]),
            "iOS scene art should be presented as a polished layered picture-book surface.",
        ),
        (
            "Android applies premium layered art treatment over scene images",
            has_all(android, ["LayeredSceneTreatment", "AnimatedScene", "ContentScale.Fit", "page.animation.layers"]),
            "Android scene art should be presented as a polished layered picture-book surface.",
        ),
    ]

    character_checks = [
        (
            "All complete books have character bibles",
            len([bible for bible in bibles if bible.get("bookId") in complete_ids]) == len(complete_ids)
            and {bible.get("bookId") for bible in bibles if bible.get("bookId") in complete_ids} == complete_ids,
            "Each complete catalog book needs a dedicated character bible.",
        ),
        (
            "Character bibles include per-character visual identity locks",
            bibles and all(len(bible.get("perCharacterVisualIdentity", [])) >= 4 for bible in bibles),
            "Character continuity should be locked beyond prose-level descriptions.",
        ),
        (
            "All complete books have generated character-sheet assets",
            character_sheet_assets_ready(complete_ids)
            and all(
                isinstance(bible.get("characterSheetAsset"), str)
                and (CONTENT / bible["characterSheetAsset"]).exists()
                and bible.get("characterConsistencyStatus") == "generated_reviewed_story_specific_internal_demo"
                for bible in bibles
                if bible.get("bookId") in complete_ids
            ),
            "Character consistency needs linked visual sheet evidence for every catalog book.",
        ),
        (
            "Character bibles include do-not-change and forbidden visual rules",
            bibles and all(bible.get("doNotChangeRules") and bible.get("forbiddenVisualElements") for bible in bibles),
            "Character consistency needs explicit negative and continuity rules.",
        ),
        (
            "Every scene image manifest entry points to a character bible",
            scenes and all(entry.get("characterBible") for entry in scenes),
            "Generated/imported art jobs must stay tied to a book-specific bible.",
        ),
        (
            "Sun and Moon tiger anchor plan remains present",
            any(bible.get("bookId") == "book.sun_moon" and bible.get("anchorApprovalPlan") for bible in bibles),
            "The highest-risk antagonist design needs explicit anchor approval before production regeneration.",
        ),
        (
            "Selected Sun and Moon scene and approval-anchor positive prompts avoid stale cute/plush negation",
            all(not has_stale_positive_prompt_text(entry) for entry in sun_moon_positive_prompt_entries(scenes, anchors)),
            "Keep cute/plush language in negative prompts or character bible constraints, not positive scene prompts.",
        ),
        (
            "Native apps render shared content instead of forking character prose",
            "shared-content" in ios_loader and "ContentRepository" in android and "catalog.json" in android_repository,
            "Character consistency depends on both apps using the canonical shared-content system.",
        ),
    ]

    layer_scene_keys = {(entry.get("storyId"), entry.get("sceneId")) for entry in layers}
    manifest_scene_keys = {(entry.get("storyId"), entry.get("sceneId")) for entry in scenes}
    animation_checks = [
        (
            "Layer manifest covers all complete scenes",
            len(layers) == expected_scene_count and manifest_scene_keys.issubset(layer_scene_keys),
            "Every complete scene needs a production layer plan.",
        ),
        (
            "Layer plans include background, midground, character, and effect roles",
            layers and all(
                {"background", "midground", "character", "effect"}.issubset(
                    {layer.get("role") for layer in entry.get("plannedLayers", [])}
                )
                for entry in layers
            ),
            "Layered animation should not regress to a single undifferentiated overlay.",
        ),
        (
            "Layer plans preserve source animation metadata",
            layers and all(entry.get("sourceAnimationLayers") for entry in layers),
            "Runtime animation behavior should trace back to page-level animation metadata.",
        ),
        (
            "Layer plans have materialized runtime layer assets",
            materialized_layer_assets_ready(layers),
            "Every planned layer needs an existing generated_reviewed runtime PNG asset.",
        ),
        (
            "Story pages reference layer assets for native runtime",
            story_pages_reference_layer_assets(books),
            "Every story page animation layer should point at a generated_reviewed runtime layer asset.",
        ),
        (
            "iOS runtime reads page animation layers for native layered treatment",
            has_all(ios, ["page.animation.layers", "outputFile", "DemoAssetImage", "layerOpacity", "hasCharacterLayer", "hasForegroundLayer", "hasEffectLayer"]),
            "iOS layered animation should load generated layer assets from shared scene metadata.",
        ),
        (
            "Android runtime reads page animation layers for native layered treatment",
            has_all(android, ["page.animation.layers.map", "outputFile", "repository.readSharedAsset", "layerAssetAlpha", "hasCharacterLayer", "hasForegroundLayer", "hasEffectLayer"]),
            "Android layered animation should load generated layer assets from shared scene metadata.",
        ),
        (
            "Both platforms keep reduced-motion behavior wired into layered animation",
            has_all(f"{ios}\n{android}", ["reduceMotion", "reducedMotion", "bedtimeMode"]),
            "Layered visual motion must respect bedtime and accessibility constraints.",
        ),
    ]

    categories = [
        ("Scene art coverage", scene_checks),
        ("Character consistency", character_checks),
        ("Scene animation", animation_checks),
    ]

    rows: list[str] = [
        "# Art Experience Score Report",
        "",
        "This is a repo-local all-catalog demo score for art presentation, character guardrails, and native layered animation. It does not claim final commissioned art, final character approval, or production-ready layered asset delivery.",
        "",
        "## Testing Methodology",
        "",
        "- Static manifest checks: catalog, image manifest, character bibles, and layer manifest are cross-checked for complete coverage.",
        "- Native implementation checks: iOS and Android source are scanned for shared-content-driven layered rendering, fit-safe art presentation, and reduced-motion support.",
        "- Manual/visual QA hook: run `scripts/agent/validate-ui` to refresh simulator/emulator screenshots and strict layout QA after UI changes.",
            "- Production honesty check: generated-review runtime layer files are present for all catalog scenes, but final commissioned art and human animation approval remain external blockers.",
        "",
        "| Category | Automated Structural Score | Status |",
        "| --- | ---: | --- |",
    ]

    detail_sections: list[str] = []
    failed: list[str] = []
    for name, checks in categories:
        score = score_category(checks)
        rows.append(f"| {name} | {score} | {'pass' if score >= 95 else 'fail'} |")
        detail_sections.extend(["", f"## {name}", ""])
        for label, ok, fix in checks:
            detail_sections.append(f"- {'PASS' if ok else 'FAIL'}: {label}")
            if not ok:
                failed.append(f"{name}: {label} -- {fix}")

    rows.extend(
        [
            "",
            "## Honest Caveat",
            "",
            "- These scores support an all-catalog visual-system claim, not final production art readiness.",
            "- Source scene art is generated/review draft unless a manifest entry is later upgraded to commissioned/reviewed/final with required human approvals.",
            "- Separated runtime layer assets now exist for all catalog scenes; they are generated-review presentation layers, not final commissioned production animation art.",
        ]
    )
    rows.extend(detail_sections)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    for name, checks in categories:
        print(f"{name}: {score_category(checks)}/100")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    if failed:
        for item in failed[:60]:
            print(f"- {item}")
        if len(failed) > 60:
            print(f"... {len(failed) - 60} more issue(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
