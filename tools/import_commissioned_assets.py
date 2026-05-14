#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from asset_pipeline_common import AUDIO, CONTENT, ASSETS, load_json, utc_now, write_json
from providers.manual_import import ManualImportProvider


def find_entry(manifest: dict, group: str, story_id: str, scene_id: str | None):
    for entry in manifest.get(group, []):
        if entry.get("storyId") != story_id:
            continue
        if scene_id is None or entry.get("sceneId") == scene_id:
            return entry
    return None


def review_payload(args) -> dict:
    return {
        "reviewer": args.reviewer,
        "reviewDate": args.review_date,
        "rejectionReason": None,
        "notes": args.notes or "",
        "culturalReviewStatus": args.cultural_review_status,
        "childSafetyReviewStatus": args.child_safety_review_status,
        "productionApprovalStatus": args.production_approval_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import commissioned image/audio and register it as a manifest candidate.")
    parser.add_argument("--kind", required=True, choices=["image_scene", "image_cover", "audio_narration"])
    parser.add_argument("--story-id", required=True)
    parser.add_argument("--scene-id")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--status", required=True)
    parser.add_argument("--reviewer")
    parser.add_argument("--review-date")
    parser.add_argument("--notes")
    parser.add_argument("--cultural-review-status", default="not_reviewed")
    parser.add_argument("--child-safety-review-status", default="not_reviewed")
    parser.add_argument("--production-approval-status", default="not_approved")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source file does not exist: {args.source}")

    importer = ManualImportProvider()
    timestamp = utc_now()

    if args.kind.startswith("image"):
        manifest_path = ASSETS / "manifests" / "image_manifest.json"
        manifest = load_json(manifest_path)
        group = "sceneEntries" if args.kind == "image_scene" else "coverEntries"
        entry = find_entry(manifest, group, args.story_id, args.scene_id)
        if not entry:
            raise SystemExit(f"No manifest entry found for {args.story_id} {args.scene_id or ''}")
        slug = entry["storySlug"]
        file_name = args.source.name
        relative = f"assets/final/images/{'scenes/' + slug if args.kind == 'image_scene' else 'covers'}/{file_name}"
        result = importer.import_image(args.source, CONTENT / relative, status=args.status)
        candidate = {
            "outputFile": relative,
            "status": args.status,
            "provider": result.provider,
            "model": result.model,
            "generationStatus": result.generation_status,
            "timestamp": timestamp,
            "sourceFile": str(args.source),
        }
    else:
        manifest_path = AUDIO / "manifests" / "audio_manifest.json"
        manifest = load_json(manifest_path)
        entry = find_entry(manifest, "narrationEntries", args.story_id, args.scene_id)
        if not entry:
            raise SystemExit(f"No narration manifest entry found for {args.story_id} {args.scene_id or ''}")
        slug = entry["storySlug"]
        file_name = args.source.name
        relative = f"audio/human-recorded-final/narration/{slug}/ko/{file_name}"
        result = importer.import_audio(args.source, CONTENT / relative, status=args.status)
        candidate = {
            "outputFile": relative,
            "status": args.status,
            "provider": result.provider,
            "tool": result.provider,
            "model": result.model,
            "generationStatus": result.generation_status,
            "timestamp": timestamp,
            "sourceFile": str(args.source),
        }

    candidate.update(review_payload(args))
    entry.setdefault("candidates", []).append(candidate)
    entry["outputFile"] = relative
    entry["status"] = args.status
    entry["generationStatus"] = "imported"
    entry["timestamp"] = timestamp
    write_json(manifest_path, manifest)
    print(f"Imported {args.kind}: {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
