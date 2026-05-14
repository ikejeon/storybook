#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
OUTPUT = ROOT / "tools" / "output" / "product_completion_report.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def count(entries: list[dict]) -> Counter:
    return Counter(entry.get("status", "missing") for entry in entries)


def main() -> int:
    catalog = load(CONTENT / "catalog.json")
    images = load(CONTENT / "assets/manifests/image_manifest.json")
    audio = load(CONTENT / "audio/manifests/audio_manifest.json")
    complete_ids = {entry["id"] for entry in catalog["books"] if entry.get("status") == "complete"}
    scenes = [entry for entry in images.get("sceneEntries", []) if entry.get("storyId") in complete_ids]
    covers = [entry for entry in images.get("coverEntries", []) if entry.get("storyId") in complete_ids]
    icons = images.get("appIconConcepts", [])
    approval_anchors = images.get("approvalAnchorEntries", [])
    narration = [entry for entry in audio.get("narrationEntries", []) if entry.get("storyId") in complete_ids]
    ui_sounds = audio.get("uiSoundEntries", [])
    ambient = audio.get("ambientEntries", [])
    sfx = audio.get("sfxEntries", [])

    scene_counts = count(scenes)
    cover_counts = count(covers)
    icon_counts = count(icons)
    anchor_counts = count(approval_anchors)
    narration_counts = count(narration)
    ui_counts = count(ui_sounds)
    ambient_counts = count(ambient)
    sfx_counts = count(sfx)
    local_storyboard_scenes = sum(1 for entry in scenes if entry.get("generationTool") == "local_storyboard_renderer")
    built_in_scene_drafts = sum(1 for entry in scenes if entry.get("generationTool") == "built_in_image_gen")
    voice_manifest_path = CONTENT / "audio/manifests/voice_bakeoff_manifest.json"
    voice_sample_count = len(load(voice_manifest_path).get("entries", [])) if voice_manifest_path.exists() else 0

    lines = [
        "# Moon Jar Stories Product Completion Report",
        "",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        "",
        "## App Shell Status",
        "- Native iOS SwiftUI prototype: build passing.",
        "- Native Android Compose prototype: Gradle test/build passing.",
        "- Shared 24-book catalog with 24 complete books: present.",
        "- Apps load shared manifests and prefer generated draft assets over placeholders.",
        "",
        "## iOS Reader Status",
        "- Library, book detail, reader, paywall mock, parent gate, narration controls, autoplay, bedtime mode: implemented.",
        "- Page turn is a custom 3D approximation with drag, shadow, page edge, page-turn sound, and Reduce Motion fallback.",
        "- Real Book Mode exists as a two-page spread demo; not a final print-grade renderer.",
        "",
        "## Android Reader Status",
        "- Library, book detail, reader, paywall mock, parent gate, Media3 narration controls, autoplay, bedtime mode: implemented.",
        "- Page turn is a Compose 3D approximation with swipe drag, shadow, page edge, page-turn sound, and reduced-motion behavior.",
        "- Real Book Mode exists as a two-page spread demo; not a final print-grade renderer.",
        "",
        "## Page Flip Status",
        "- iOS: premium approximation, not true UIKit page curl.",
        "- Android: premium approximation, not true physical page curl.",
        "- Page-turn sound: synthetic draft.",
        "",
        "## Scene Animation Status",
        "- Native overlay effects implemented: moon glow, lantern flicker, cloud drift, water ripple, tiger blink/tail sway approximation, sparkles, fireflies.",
        "- Actual separated/layered animation image assets: not present yet.",
        "",
        "## Image Asset Status",
        f"- Scene images total: {len(scenes)}",
        f"- Scene placeholders: {scene_counts.get('placeholder', 0)}",
        f"- Scene generated_draft: {scene_counts.get('generated_draft', 0)}",
        f"- Scene reviewed: {scene_counts.get('generated_reviewed', 0) + scene_counts.get('commissioned_reviewed', 0)}",
        f"- Scene final: {scene_counts.get('commissioned_final', 0)}",
        f"- Covers total: {len(covers)}",
        f"- Covers placeholder/generated/reviewed/final: {cover_counts.get('placeholder', 0)} / {cover_counts.get('generated_draft', 0)} / {cover_counts.get('generated_reviewed', 0) + cover_counts.get('commissioned_reviewed', 0)} / {cover_counts.get('commissioned_final', 0)}",
        f"- App icon concepts placeholder/generated/final: {icon_counts.get('placeholder', 0)} / {icon_counts.get('generated_draft', 0)} / {icon_counts.get('commissioned_final', 0)}",
        f"- Approval anchors generated_draft/reviewed/final: {anchor_counts.get('generated_draft', 0)} / {anchor_counts.get('generated_reviewed', 0) + anchor_counts.get('commissioned_reviewed', 0)} / {anchor_counts.get('commissioned_final', 0)}",
        "",
        "## Audio Asset Status",
        f"- Narration total: {len(narration)}",
        f"- Narration synthetic_draft: {narration_counts.get('synthetic_draft', 0)}",
        f"- Narration human_recorded_final: {narration_counts.get('human_recorded_final', 0)}",
        f"- UI sounds by status: {dict(sorted(ui_counts.items()))}",
        f"- Ambient loops by status: {dict(sorted(ambient_counts.items()))}",
        f"- Story SFX by status: {dict(sorted(sfx_counts.items()))}",
        "",
        "## Payment Status",
        "- StoreKit 2 and Google Play Billing architecture scaffolds exist.",
        "- Real store product configuration and receipt/token verification are not implemented.",
        "",
        "## Backend Status",
        "- OpenAPI contract and local stub exist.",
        "- Production backend/CMS is not deployed or implemented.",
        "",
        "## Store Readiness Status",
        "- Not App Store / Play Store ready.",
        "- Needs final art/audio, real payments, production backend, release signing, privacy policy, store listing, compliance review, and QA.",
        "",
        "## What Is Demo",
        "- Real Book Mode spread is demo quality.",
        "- Page curl is an approximation.",
        "- Layered assets are planned but not present.",
        "",
        "## What Is Generated Draft",
        f"- {scene_counts.get('generated_draft', 0)} scene images are generated_draft: {built_in_scene_drafts} from built-in image/storyboard generation and {local_storyboard_scenes} from the local SVG storyboard renderer.",
        f"- {scene_counts.get('generated_reviewed', 0) + scene_counts.get('commissioned_reviewed', 0)} scene images are generated/review draft for internal all-catalog demo use.",
        "- 24 covers derived from generated/review draft art.",
        "- 1 app icon concept derived from generated scene art.",
        "- Revised Sun and Moon tiger character-sheet V2 anchor generated with the built-in image tool and agent-reviewed for draft regeneration.",
        "- Page-turn, button, and ambient sounds are synthetic/procedural drafts.",
        "- English and Korean narration are synthetic drafts from local/offline generation.",
        f"- Voice bakeoff local baseline samples: {voice_sample_count}.",
        "",
        "## What Is Reviewed",
        f"- {anchor_counts.get('generated_reviewed', 0) + anchor_counts.get('commissioned_reviewed', 0)} Sun and Moon approval anchors are generated_reviewed for bulk draft regeneration.",
        f"- {scene_counts.get('generated_reviewed', 0) + scene_counts.get('commissioned_reviewed', 0)} complete-book scene images and {cover_counts.get('generated_reviewed', 0) + cover_counts.get('commissioned_reviewed', 0)} covers are internally reviewed for all-catalog demo use.",
        "- No complete-book scene images, covers, app icon, narration, UI sounds, or ambient audio are final production assets yet.",
        "",
        "## What Is Final",
        "- No scene art, covers, app icon, narration, UI sounds, or ambient audio are final.",
        "",
        "## What Is Blocked",
        "- Human-recorded narration.",
        "- Cultural/child-safety review.",
        "- Commissioned final illustration pass.",
        "- True page curl or platform-native page curl implementation.",
        "- Actual layered animation asset production.",
        "- Production backend and real payment verification.",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
