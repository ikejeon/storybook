#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def review_defaults(note: str = "Generated draft. Not reviewed and not final.") -> dict:
    return {
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": note,
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }


def upsert_candidate(entry: dict, output_file: str, source_sheet: str | None, status: str = "generated_draft", note: str | None = None) -> None:
    candidates = entry.setdefault("candidates", [])
    candidates[:] = [item for item in candidates if item.get("outputFile") != output_file]
    candidate = {
        "outputFile": output_file,
        "status": status,
        "provider": "built_in_image_gen",
        "model": "built-in image_gen",
        "generationStatus": "generated_storyboard_crop" if source_sheet else "generated",
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sourceFile": source_sheet,
    }
    candidate.update(review_defaults(note or "Generated draft. Not reviewed and not final."))
    candidates.append(candidate)
    entry["outputFile"] = output_file
    entry["status"] = status
    entry["generationTool"] = candidate["provider"]
    entry["generationModel"] = candidate["model"]
    entry["generationStatus"] = candidate["generationStatus"]
    entry["timestamp"] = candidate["timestamp"]
    if note:
        entry["notes"] = note


def source_sheet_for(slug: str, page_number: int) -> str:
    if slug == "red-bean-porridge-grandma" and page_number >= 9:
        return f"assets/generated-draft/images/storyboards/{slug}/sheet-03.png"
    sheet_index = ((page_number - 1) // 4) + 1
    return f"assets/generated-draft/images/storyboards/{slug}/sheet-{sheet_index:02d}.png"


def main() -> int:
    manifest = load(IMAGE_MANIFEST)
    updates = 0

    for entry in manifest.get("sceneEntries", []):
        slug = entry["storySlug"]
        page_number = entry["pageNumber"]
        output = f"assets/generated-draft/images/scenes/{slug}/page-{page_number:03d}.png"
        path = CONTENT / output
        if path.exists():
            source_sheet = source_sheet_for(slug, page_number)
            note = None
            if slug == "sun-and-moon":
                note = "Generated draft predates the revised Sun and Moon antagonist tiger direction. Not reviewed or final; regenerate after tiger anchor approval."
                entry["artDirectionStatus"] = "needs_tiger_anchor_regeneration"
                entry["anchorApprovalRequiredBeforeRegeneration"] = True
            upsert_candidate(entry, output, source_sheet, note=note)
            updates += 1

    for entry in manifest.get("coverEntries", []):
        slug = entry["storySlug"]
        output = f"assets/generated-draft/images/covers/{slug}.png"
        if (CONTENT / output).exists():
            upsert_candidate(entry, output, None)
            updates += 1

    for entry in manifest.get("appIconConcepts", []):
        concept = entry.get("conceptNumber", 1)
        output = f"assets/generated-draft/images/app-icon/app-icon-concept-{concept:02d}.png"
        if (CONTENT / output).exists():
            upsert_candidate(entry, output, None)
            updates += 1

    write(IMAGE_MANIFEST, manifest)
    print(f"Registered generated_draft image assets: {updates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
