#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def review_defaults() -> dict:
    return {
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": "Local generated storyboard draft from the SVG renderer. Not reviewed, not final, and not a substitute for approved production art.",
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }


def main() -> int:
    manifest = load(IMAGE_MANIFEST)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updated = 0
    missing_sources: list[str] = []

    for entry in manifest.get("sceneEntries", []):
        if entry.get("status") != "placeholder":
            continue

        slug = entry["storySlug"]
        page_number = int(entry["pageNumber"])
        filename = f"page-{page_number:03d}.png"
        source = CONTENT / "assets" / "books" / slug / filename
        output = CONTENT / "assets" / "generated-draft" / "images" / "scenes" / slug / filename
        output_relative = str(output.relative_to(CONTENT))

        if not source.exists():
            missing_sources.append(str(source.relative_to(CONTENT)))
            continue

        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)

        candidate = {
            "outputFile": output_relative,
            "status": "generated_draft",
            "provider": "local_storyboard_renderer",
            "model": "moonjar_svg_scene_renderer",
            "generationStatus": "generated_local_storyboard",
            "timestamp": now,
            "sourceFile": str(source.relative_to(CONTENT)),
        }
        candidate.update(review_defaults())

        candidates = entry.setdefault("candidates", [])
        candidates[:] = [item for item in candidates if item.get("outputFile") != output_relative]
        candidates.append(candidate)

        entry["outputFile"] = output_relative
        entry["status"] = "generated_draft"
        entry["generationTool"] = candidate["provider"]
        entry["generationModel"] = candidate["model"]
        entry["generationStatus"] = candidate["generationStatus"]
        entry["timestamp"] = now
        entry["notes"] = candidate["notes"]
        updated += 1

    write(IMAGE_MANIFEST, manifest)
    print(f"Generated local draft scene art for {updated} placeholder scenes.")
    if missing_sources:
        print("Missing local renderer sources:")
        for source in missing_sources:
            print(f"- {source}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
