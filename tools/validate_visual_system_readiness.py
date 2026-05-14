#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
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
ANIMATION_CAPABILITIES = CONTENT / "animation" / "runtime_animation_capabilities.json"
VISUAL_REVIEW = CONTENT / "reviews" / "visual_art_readiness_review.json"
IOS = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "Views.swift"
ANDROID = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "ui" / "MoonJarApp.kt"
REPORT = ROOT / "tools" / "output" / "visual_system_readiness_report.md"

DRAFT_OR_BETTER = {
    "generated_draft",
    "generated_reviewed",
    "commissioned_draft",
    "commissioned_reviewed",
    "commissioned_final",
}
FINAL_STATUSES = {"commissioned_final"}
REQUIRED_LAYER_ROLES = {"background", "midground", "character", "foreground", "effect", "particle_glow"}
BAD_IMAGE_RENDERERS = {"local_static_storyboard_renderer", "deterministic_repo_renderer", "moonjar_static_placeholder_renderer"}
PREMIUM_STORY_SPECIFIC_RENDERER = "local_story_specific_svg_renderer"
PREMIUM_STORY_SPECIFIC_RUNTIME_RENDERERS = {
    PREMIUM_STORY_SPECIFIC_RENDERER,
    "built_in_image_gen_sheet_importer",
    "built_in_image_gen_story_specific_scene",
}
MIN_PREMIUM_STORY_SPECIFIC_BYTES = 180_000


@dataclass(frozen=True)
class Check:
    label: str
    ok: bool
    fix: str


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def complete_books() -> list[dict[str, Any]]:
    catalog = load(CATALOG)
    return [entry for entry in catalog.get("books", []) if entry.get("status") == "complete"]


def book_page_counts(books: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in books:
        book_path = entry.get("bookPath")
        if not isinstance(book_path, str):
            continue
        book = load(CONTENT / book_path)
        counts[entry["id"]] = len(book.get("pages", []))
    return counts


def selected_asset_exists(entry: dict[str, Any]) -> bool:
    output = entry.get("outputFile")
    return isinstance(output, str) and bool(output) and (CONTENT / output).exists()


def selected_asset_size(entry: dict[str, Any]) -> int:
    output = entry.get("outputFile")
    if isinstance(output, str) and bool(output) and (CONTENT / output).exists():
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


def character_sheets_ready(complete_ids: set[str]) -> bool:
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


def prompt_safe(entry: dict[str, Any]) -> bool:
    text = " ".join(str(entry.get(key, "")) for key in ("prompt", "rawPrompt")).lower()
    return all(needle in text for needle in ["no text", "no watermark"]) and any(
        phrase in text for phrase in ["fit-safe", "safe margins", "not cropped", "no cropped"]
    )


def dimensions_safe(entry: dict[str, Any]) -> bool:
    dimensions = entry.get("dimensions")
    if not isinstance(dimensions, dict):
        return False
    width = dimensions.get("width")
    height = dimensions.get("height")
    return isinstance(width, int) and isinstance(height, int) and width >= 512 and height >= 512


def manifest_scene_key(entry: dict[str, Any]) -> tuple[Any, Any]:
    return entry.get("storyId"), entry.get("sceneId")


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def materialized_layer_assets_ready(layer_scenes: list[dict[str, Any]]) -> bool:
    if not layer_scenes:
        return False
    for entry in layer_scenes:
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


def score(checks: list[Check]) -> int:
    return round(100 * sum(1 for check in checks if check.ok) / max(1, len(checks)))


def main() -> int:
    books = complete_books()
    counts = book_page_counts(books)
    complete_ids = set(counts)
    premium_ids = {entry["id"] for entry in books if entry.get("access") == "premium"}
    expected_scene_count = sum(counts.values())
    images = load(IMAGE_MANIFEST)
    layers = load(LAYER_MANIFEST)
    review = load(VISUAL_REVIEW)
    animation = load(ANIMATION_CAPABILITIES)
    ios = read(IOS)
    android = read(ANDROID)

    scenes = [entry for entry in images.get("sceneEntries", []) if entry.get("storyId") in complete_ids]
    covers = [entry for entry in images.get("coverEntries", []) if entry.get("storyId") in complete_ids]
    premium_scenes = [entry for entry in scenes if entry.get("storyId") in premium_ids]
    premium_covers = [entry for entry in covers if entry.get("storyId") in premium_ids]
    anchors = images.get("approvalAnchorEntries", [])
    layer_scenes = layers.get("scenes", [])
    layer_keys = {manifest_scene_key(entry) for entry in layer_scenes}
    scene_keys = {manifest_scene_key(entry) for entry in scenes}

    bibles = []
    for book in books:
        slug = str(book.get("slug", "")).replace("-", "_")
        candidate = CHARACTER_DIR / f"{slug}.character_bible.json"
        if not candidate.exists():
            # Catalog slugs are marketing slugs, while bible filenames use shorter story slugs.
            candidate = next((path for path in CHARACTER_DIR.glob("*.character_bible.json") if load(path).get("bookId") == book["id"]), candidate)
        if candidate.exists():
            bibles.append(load(candidate))

    nonfinal_claimed_approved = [
        entry
        for entry in scenes + covers
        if entry.get("status") not in FINAL_STATUSES and entry.get("productionApprovalStatus") == "approved"
    ]

    scene_art_checks = [
        Check(
            "All complete scenes have runtime image entries",
            len(scenes) == expected_scene_count,
            "Keep image_manifest sceneEntries aligned with the complete-book page count.",
        ),
        Check(
            "Runtime scene image files exist",
            scenes and all(selected_asset_exists(entry) for entry in scenes),
            "Import or generate missing selected scene image files.",
        ),
        Check(
            "Runtime scenes are draft-or-better and never placeholders",
            scenes and all(entry.get("status") in DRAFT_OR_BETTER for entry in scenes),
            "Do not ship placeholder scene art for complete books.",
        ),
        Check(
            "Selected runtime art no longer uses the old abstract static renderer",
            scenes and covers and not any(uses_bad_image_renderer(entry) for entry in scenes + covers),
            "Replace selected local_static_storyboard_renderer/deterministic_repo_renderer art before claiming strong visual readiness.",
        ),
        Check(
            "Premium runtime scenes and covers have story-specific illustration evidence",
            premium_scenes
            and premium_covers
            and all(premium_story_specific_art(entry) for entry in premium_scenes + premium_covers),
            "Premium books need story-specific art evidence, not only selected image files.",
        ),
        Check(
            "Runtime scene entries include recorded usable dimensions",
            scenes and all(dimensions_safe(entry) for entry in scenes),
            "Record usable selected-image dimensions for every complete-scene art entry.",
        ),
        Check(
            "Scene prompts preserve no-text/no-watermark/fit-safe direction",
            scenes and all(prompt_safe(entry) for entry in scenes),
            "Every scene prompt must forbid text/watermarks and guard against cropping.",
        ),
        Check(
            "All complete covers have runtime image entries",
            len(covers) == len(complete_ids) and all(selected_asset_exists(entry) for entry in covers),
            "Every complete catalog book needs a selected cover asset.",
        ),
        Check(
            "Reviewed visual anchors exist",
            sum(1 for entry in anchors if entry.get("status") in {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}) >= 7,
            "Maintain reviewed approval anchors for visual style and high-risk characters.",
        ),
        Check(
            "Visual review approves all-catalog demo use",
            review.get("overallStatus") == "approved_for_premium_demo" and review.get("overallScore", 0) >= 95,
            "Update the visual review artifact with a 95+ all-catalog demo review before raising the score.",
        ),
        Check(
            "Visual review preserves production honesty",
            review.get("externalHumanCreativeApprovalRequiredBeforeFinal") is True
            and review.get("externalCommissionedFinalRequiredBeforeProduction") is True
            and not nonfinal_claimed_approved,
            "Do not mark generated draft art as production approved or final.",
        ),
    ]

    character_checks = [
        Check(
            "All complete books have character bibles",
            len(bibles) == len(complete_ids) and {bible.get("bookId") for bible in bibles} == complete_ids,
            "Add a complete character bible for every complete catalog book.",
        ),
        Check(
            "Character bibles include visual identity locks",
            bibles and all(len(bible.get("perCharacterVisualIdentity", [])) >= 4 for bible in bibles),
            "Character bibles need per-character visual locks, not just story prose.",
        ),
        Check(
            "Character-sheet assets exist for all complete books",
            character_sheets_ready(complete_ids)
            and all(
                isinstance(bible.get("characterSheetAsset"), str)
                and (CONTENT / bible["characterSheetAsset"]).exists()
                and bible.get("characterConsistencyStatus") == "generated_reviewed_story_specific_internal_demo"
                for bible in bibles
            ),
            "Add generated/reviewed character-sheet assets and link them from every bible.",
        ),
        Check(
            "Character bibles include forbidden and do-not-change rules",
            bibles and all(bible.get("forbiddenVisualElements") and bible.get("doNotChangeRules") for bible in bibles),
            "Add explicit negative and continuity rules for every complete book.",
        ),
        Check(
            "Every runtime scene links to character and style bibles",
            scenes and all(entry.get("characterBible") and entry.get("styleBible") for entry in scenes),
            "Tie every generated/imported scene entry to canonical character/style bibles.",
        ),
        Check(
            "Every runtime scene links to a layer plan",
            scenes and all(entry.get("layerPlanRef") for entry in scenes),
            "Tie every scene image to the production layer plan it is expected to support.",
        ),
        Check(
            "Sun and Moon tiger anchor approval plan remains explicit",
            any(bible.get("bookId") == "book.sun_moon" and bible.get("anchorApprovalPlan") for bible in bibles),
            "Keep the highest-risk antagonist design guarded by anchor approval criteria.",
        ),
        Check(
            "Visual review covers all complete books",
            set(review.get("books", {})) == complete_ids
            and all(item.get("status") == "approved_for_premium_demo" and item.get("score", 0) >= 95 for item in review.get("books", {}).values()),
            "Record an all-catalog visual review result for each complete catalog book.",
        ),
    ]

    animation_checks = [
        Check(
            "Layer manifest covers all complete scenes",
            len(layer_scenes) == expected_scene_count and scene_keys.issubset(layer_keys),
            "Every complete scene needs a production layer plan.",
        ),
        Check(
            "Layer plans include all required roles",
            layer_scenes
            and all(REQUIRED_LAYER_ROLES.issubset({layer.get("role") for layer in entry.get("plannedLayers", [])}) for entry in layer_scenes),
            "Every layer plan must include background, midground, character, foreground, effect, and particle/glow roles.",
        ),
        Check(
            "Layer plans preserve source animation metadata",
            layer_scenes and all(entry.get("sourceAnimationLayers") for entry in layer_scenes),
            "Keep layer plans traceable to page-level animation metadata.",
        ),
        Check(
            "Layer plans have materialized runtime layer assets",
            materialized_layer_assets_ready(layer_scenes),
            "Every planned layer must have an existing generated_reviewed runtime PNG asset.",
        ),
        Check(
            "Story pages reference layer assets for native runtime",
            story_pages_reference_layer_assets(books),
            "Every story page animation layer should point at a generated_reviewed runtime layer asset.",
        ),
        Check(
            "Runtime animation capabilities approve all-catalog demo use",
            animation.get("status") == "approved_for_premium_demo"
            and animation.get("score", 0) >= 95
            and animation.get("externalSeparatedLayerAssetsRequiredBeforeProduction") is False
            and animation.get("externalFinalLayerApprovalRequiredBeforeProduction") is True,
            "Record runtime layer asset capability while preserving final animation approval blockers.",
        ),
        Check(
            "iOS has layered runtime and page-turn signals",
            has_all(ios, ["LayeredSceneTreatment", "LivingSceneEffects", "OpenBookStage", "PageTurnSheet", "reduceMotion"]),
            "Keep iOS layered scene and page-turn treatment wired.",
        ),
        Check(
            "Android has layered runtime and page-turn signals",
            has_all(android, ["LayeredSceneTreatment", "AnimatedScene", "RealBookSpread", "PageTurnCurlOverlay", "reducedMotion"]),
            "Keep Android layered scene and page-turn treatment wired.",
        ),
        Check(
            "Native runtimes read shared animation metadata",
            has_all(f"{ios}\n{android}", ["page.animation.layers", "outputFile", "hasCharacterLayer", "hasForegroundLayer", "hasEffectLayer"]),
            "Native animation should remain driven by shared-content metadata and layer asset paths.",
        ),
    ]

    categories = [
        ("Scene art coverage", scene_art_checks),
        ("Character consistency", character_checks),
        ("Scene animation", animation_checks),
    ]

    rows = [
        "# Visual System Readiness Report",
        "",
        "This is a repo-local all-catalog readiness gate. It validates coverage, review artifacts, character continuity, materialized runtime layer assets, native layered treatment, and production honesty; it does not claim final commissioned animation approval.",
        "",
        "| Category | Automated Structural Score | Status |",
        "| --- | ---: | --- |",
    ]
    failed: list[str] = []
    detail_rows: list[str] = []

    for name, checks in categories:
        category_score = score(checks)
        rows.append(f"| {name} | {category_score} | {'pass' if category_score >= 95 else 'fail'} |")
        detail_rows.extend(["", f"## {name}", ""])
        for check in checks:
            detail_rows.append(f"- {'PASS' if check.ok else 'FAIL'}: {check.label}")
            if not check.ok:
                failed.append(f"{name}: {check.label} -- {check.fix}")

    rows.extend(
        [
            "",
            "## Production Honesty",
            "",
            "- Runtime scene art is generated/review draft unless individual manifest entries are later upgraded.",
            "- Runtime covers are generated/review draft.",
            "- External human creative/cultural approval and commissioned final art remain production blockers.",
            "- Separated production layer files remain an external animation asset task.",
        ]
    )
    rows.extend(detail_rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    for name, checks in categories:
        print(f"{name}: {score(checks)}/100")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    if failed:
        for item in failed:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
