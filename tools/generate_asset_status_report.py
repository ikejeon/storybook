#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
OUTPUT = ROOT / "tools" / "output" / "asset_status_report.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def status_bucket(status: str, kind: str) -> str:
    if kind == "image":
        if status == "placeholder":
            return "placeholder"
        if status == "generated_draft":
            return "generated_draft"
        if status in {"generated_reviewed", "commissioned_reviewed"}:
            return "reviewed"
        if status == "commissioned_final":
            return "final"
        if status == "commissioned_draft":
            return "commissioned_draft"
    if kind == "audio":
        if status == "placeholder":
            return "placeholder"
        if status == "synthetic_draft":
            return "synthetic_draft"
        if status in {"synthetic_reviewed", "human_recorded_reviewed"}:
            return "reviewed"
        if status == "human_recorded_final":
            return "human_recorded_final"
        if status == "human_recorded_draft":
            return "human_recorded_draft"
    return status or "unknown"


def count_entries(entries: list[dict], kind: str) -> Counter:
    return Counter(status_bucket(entry.get("status", "unknown"), kind) for entry in entries)


def main() -> int:
    catalog = load(CONTENT / "catalog.json")
    image_manifest = load(CONTENT / "assets" / "manifests" / "image_manifest.json")
    audio_manifest = load(CONTENT / "audio" / "manifests" / "audio_manifest.json")
    anchor_plan_path = CONTENT / "assets" / "manifests" / "sun_moon_tiger_anchor_plan.json"
    anchor_plan = load(anchor_plan_path) if anchor_plan_path.exists() else None

    scenes_by_story: dict[str, list[dict]] = {}
    covers_by_story: dict[str, list[dict]] = {}
    narration_by_story: dict[str, list[dict]] = {}
    ambient_by_story: dict[str, list[dict]] = {}

    for entry in image_manifest.get("sceneEntries", []):
        scenes_by_story.setdefault(entry["storyId"], []).append(entry)
    for entry in image_manifest.get("coverEntries", []):
        covers_by_story.setdefault(entry["storyId"], []).append(entry)
    for entry in audio_manifest.get("narrationEntries", []):
        narration_by_story.setdefault(entry["storyId"], []).append(entry)
    for entry in audio_manifest.get("ambientEntries", []):
        slug = entry.get("outputFile", "").split("/books/")[-1].split("/ambient/")[0]
        ambient_by_story.setdefault(slug, []).append(entry)

    page_turn = next((entry for entry in audio_manifest.get("uiSoundEntries", []) if entry.get("assetType") == "page_flip_sound"), None)
    page_turn_status = page_turn.get("status", "missing") if page_turn else "missing"
    sfx_counts = count_entries(audio_manifest.get("sfxEntries", []), "audio")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Moon Jar Stories Asset Status Report",
        "",
        f"Generated: {generated_at}",
        "",
        "This report is intentionally honest: placeholder, generated-draft, and synthetic-draft assets are not final production assets.",
        "",
        f"Global page-turn sound status: `{page_turn_status}`",
        f"Default narration language: `{audio_manifest.get('defaultNarrationLanguage', 'ko')}`",
        "",
        "| Book | Scene Images | Placeholder | Generated Draft | Reviewed | Final | English Narration | Optional Korean Narration | Synthetic Draft | Human Final | Page-Turn Sound | Ambient Audio |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    totals = Counter()
    audio_totals = Counter()

    for catalog_entry in catalog["books"]:
        if catalog_entry.get("status") != "complete":
            continue
        book = load(CONTENT / catalog_entry["bookPath"])
        story_id = book["id"]
        scene_entries = scenes_by_story.get(story_id, [])
        narration_entries = narration_by_story.get(story_id, [])
        english_narration = [entry for entry in narration_entries if (entry.get("language") or ("en" if entry.get("assetType") == "english_narration" else "ko")) == "en"]
        korean_narration = [entry for entry in narration_entries if (entry.get("language") or ("en" if entry.get("assetType") == "english_narration" else "ko")) == "ko"]
        image_counts = count_entries(scene_entries, "image")
        audio_counts = count_entries(narration_entries, "audio")
        totals.update(image_counts)
        audio_totals.update(audio_counts)

        ambient_entries = ambient_by_story.get(book["slug"], [])
        ambient_status = ", ".join(sorted({entry.get("status", "missing") for entry in ambient_entries})) if ambient_entries else "missing"

        lines.append(
            "| "
            f"{book['title']['en']} | "
            f"{len(scene_entries)} | "
            f"{image_counts.get('placeholder', 0)} | "
            f"{image_counts.get('generated_draft', 0)} | "
            f"{image_counts.get('reviewed', 0)} | "
            f"{image_counts.get('final', 0)} | "
            f"{len(english_narration)} | "
            f"{len(korean_narration)} | "
            f"{audio_counts.get('synthetic_draft', 0)} | "
            f"{audio_counts.get('human_recorded_final', 0)} | "
            f"`{page_turn_status}` | "
            f"`{ambient_status}` |"
        )

    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- Scene image placeholders: {totals.get('placeholder', 0)}",
            f"- Scene image generated drafts: {totals.get('generated_draft', 0)}",
            f"- Scene image reviewed: {totals.get('reviewed', 0)}",
            f"- Scene image final: {totals.get('final', 0)}",
            f"- Narration synthetic drafts: {audio_totals.get('synthetic_draft', 0)}",
            f"- Narration human-recorded final: {audio_totals.get('human_recorded_final', 0)}",
            f"- Story SFX synthetic drafts: {sfx_counts.get('synthetic_draft', 0)}",
            "- English narration is the default app experience; Korean narration is optional and remains available through the language toggle.",
            "",
            "## Art Direction / Regeneration Gates",
            "",
        ]
    )

    if anchor_plan:
        anchors = anchor_plan.get("anchors", [])
        generated_anchors = sum(1 for item in anchors if item.get("status") not in {"not_generated", "pending_anchor_generation"})
        sun_moon_regeneration = image_manifest.get("sunMoonRegeneration", {})
        lines.extend(
            [
                f"- Sun and Moon tiger anchor plan: `{anchor_plan_path.relative_to(CONTENT)}`",
                f"- Anchor plan status: `{anchor_plan.get('status')}`",
                f"- Bulk Sun and Moon regeneration allowed: `{anchor_plan.get('bulkGenerationAllowed')}`",
                f"- Anchor images generated/total: {generated_anchors}/{len(anchors)}",
                f"- Sun and Moon bulk regeneration status: `{sun_moon_regeneration.get('status', 'not_recorded')}`",
                f"- Sun and Moon regenerated from approved antagonist anchor: {sun_moon_regeneration.get('completedSceneCount', 0)}/{sun_moon_regeneration.get('expectedSceneCount', 32)}",
                "- Seven approval anchors are generated_reviewed for draft-regeneration use only, not final production art.",
                "- Current Sun and Moon generated-draft scene art exists, but it predates the revised antagonist tiger direction and should be regenerated from the reviewed anchors before production review.",
                "",
            ]
        )
        if sun_moon_regeneration.get("blockedReason"):
            lines.extend(
                [
                    "### Current Sun and Moon Regeneration Blocker",
                    "",
                    sun_moon_regeneration["blockedReason"],
                    "",
                ]
            )
    else:
        lines.extend(["- No active art-direction generation gates found.", ""])

    lines.extend(
        [
            "## Production Gap",
            "",
            "- Final illustrated scene images: not yet present.",
            "- Reviewed/final character-consistent art: not yet present.",
            "- Actual layered animation image assets: not yet present.",
            "- Final human-recorded Korean narration: not yet present.",
            "- Final ambient/page-turn/UI sounds: not yet present.",
            "- Final app icon/store screenshots: not yet present.",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
